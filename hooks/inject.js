#!/usr/bin/env node
// SessionStart, SubagentStart, PostToolUse and UserPromptSubmit hook. All four
// reach the model. Any other event exits silently.
//
// SessionStart fires on startup, resume, clear, and compact. The compact matcher
// is what restores the rules after a summarization drops them.
//
// PostToolUse reports a finding mid-turn, next to the tool result.
//
// UserPromptSubmit does two jobs. It lints the previous assistant turn, which is
// on disk by now, and it restates a one-line reminder every REMIND_EVERY
// prompts, because a rule stated once at turn 1 stops steering by turn 40.

const crypto = require('crypto');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { check, lastTurn } = require('./check.js');

const REMIND_EVERY = Number(process.env.ANTI_SLOP_REMIND_EVERY || 10);
const MAX_REPORTED = 8;
const RULES = path.join(__dirname, 'rules.md');
const DIRECTIVE = {
  sycophancy: 'ANTI-SYCOPHANCY DIRECTIVE',
  word: 'BANNED VOCABULARY RULE',
  phrase: 'BANNED CONSTRUCTION RULE',
  structure: 'STRUCTURAL SLOP RULE',
  verbosity: 'BREVITY RULE',
  ambiguous: 'WRITING-STYLE NOTE (soft, judge it)',
  default: 'ANTI-SLOP RULE',
};
const SHORT =
  'ANTI-SLOP DIRECTIVE, still in force: no contrast constructions ' +
  '("it\'s not X, it\'s Y"), no LLM vocabulary (delve, leverage, crucial, ' +
  '"load-bearing"), no LinkedIn cadence, no flattery and no apologies, ' +
  'no servile closer, active voice, one fact per sentence.';

let input = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', c => (input += c));
process.stdin.on('end', () => {
  let data;
  try {
    data = JSON.parse(input);
  } catch {
    process.exit(0);
  }

  if (data.hook_event_name === 'PostToolUse') {
    try {
      midTurn(data);
    } catch {
      /* a malformed transcript must not disturb the tool result */
    }
    process.exit(0);
  }

  if (data.hook_event_name !== 'UserPromptSubmit') {
    if (!['SessionStart', 'SubagentStart'].includes(data.hook_event_name)) {
      process.exit(0);
    }
    try {
      // The linter's ignore marker belongs to the file, not to the context.
      const rules = fs
        .readFileSync(RULES, 'utf8')
        .replace(/^<!-- anti-slop:.*$/gm, '')
        .trim();
      console.log(rules);
    } catch {
      console.log(SHORT);
    }
    process.exit(0);
  }

  const out = [];
  try {
    out.push(...report(data));
  } catch {
    /* a malformed transcript must not block the prompt */
  }
  if (bump(data.session_id) % REMIND_EVERY === 0) out.push(SHORT);
  if (out.length) console.log(out.join('\n'));
});

// PostToolUse writes additionalContext next to the tool result, so a finding
// reaches the model while the turn is still open and the rest of the prose is
// still unwritten. Nothing blocks and no second message ships. The final message
// of a turn arrives after the last tool call, so UserPromptSubmit still has work.
//
// Soft findings stay out. Length is not measurable on half a turn.
function midTurn(data) {
  const turn = lastTurn(data.transcript_path);
  if (!turn.assistant) return;

  const state = loadState(data.session_id);
  const turnKey = turnId(turn);
  const seen = turnKey && state.turnKey === turnKey ? state.seen || [] : [];

  const fresh = check(turn.assistant, turn.user)
    .filter(v => !v.soft)
    .filter(v => !seen.includes(key(v)));
  if (!fresh.length) return;

  const shown = fresh.slice(0, MAX_REPORTED);
  saveState(data.session_id, {
    ...state,
    turnKey,
    seen: [...seen, ...shown.map(key)].slice(-40),
  });

  process.stdout.write(
    JSON.stringify({
      hookSpecificOutput: {
        hookEventName: 'PostToolUse',
        additionalContext: [
          'ANTI-SLOP: your prose earlier in this turn breaks the rules below.',
          ...shown.map(v => `  ${DIRECTIVE[v.kind] || DIRECTIVE.default}: ${v.match} — "${v.sentence}"`),
          'Write the rest of this turn without them. Do not rewrite the earlier ' +
            'text and do not mention this notice.',
        ].join('\n'),
      },
    })
  );
}

const key = v => `${v.kind}:${v.match}:${v.sentence}`;

// Both hooks derive the turn from the same walk, so the opening user prompt is
// the one identifier they agree on. prompt_id identifies the prompt that just
// arrived at UserPromptSubmit, and the turn on disk carries an older one.
const turnId = turn =>
  turn.user ? crypto.createHash('sha1').update(turn.user).digest('hex').slice(0, 12) : null;

function report(data) {
  const state = loadState(data.session_id);
  const turn = lastTurn(data.transcript_path);
  if (!turn.assistant) return [];
  // Each turn is reported once. Without this the same text repeats every prompt.
  if (turn.uuid && turn.uuid === state.lastUuid) return [];
  saveState(data.session_id, { ...state, lastUuid: turn.uuid });

  // A finding the PostToolUse hook already delivered stays out. The model acted
  // on it mid-turn; a repeat reads as a second offence.
  const turnKey = turnId(turn);
  const seen = turnKey && state.turnKey === turnKey ? state.seen || [] : [];
  const violations = check(turn.assistant, turn.user).filter(v => !seen.includes(key(v)));
  if (!violations.length) return [];

  // Grouped under a named directive per kind. A flat "anti-slop found 3
  // violations" reads as a log line and gets skimmed; the rule name tells the
  // model which rule it broke.
  // Sycophancy first. Truncation used to drop it behind a word-list hit, and it
  // is the finding the model most needs to see.
  const rank = {
    sycophancy: 0, verbosity: 1, phrase: 2, structure: 3, word: 4, ambiguous: 5,
  };
  const ordered = [...violations].sort(
    (a, b) => (rank[a.kind] ?? 9) - (rank[b.kind] ?? 9)
  );
  const shown = ordered.slice(0, MAX_REPORTED);
  const out = [];
  for (const kind of [...new Set(shown.map(v => v.kind))]) {
    out.push(`${DIRECTIVE[kind] || DIRECTIVE.default} VIOLATED in your previous message:`);
    for (const v of shown.filter(v => v.kind === kind)) {
      out.push(`  ${v.match} — "${v.sentence}"`);
    }
  }
  if (violations.length > MAX_REPORTED) {
    out.push(`  ...and ${violations.length - MAX_REPORTED} more`);
  }
  out.push(
    'These are hard rules. Rewrite the offending construction in every reply ' +
      'from now on. Do not acknowledge this notice and do not revisit the ' +
      'previous message.'
  );
  return out;
}

const stateFile = id => path.join(os.tmpdir(), `anti-slop-${id}.json`);

function loadState(id) {
  if (!id) return { n: 0, lastUuid: null };
  try {
    return JSON.parse(fs.readFileSync(stateFile(id), 'utf8'));
  } catch {
    return { n: 0, lastUuid: null };
  }
}

function saveState(id, state) {
  if (!id) return;
  try {
    fs.writeFileSync(stateFile(id), JSON.stringify(state));
  } catch {
    /* tmpdir not writable; the counter resets and reminds again */
  }
}

function bump(id) {
  const state = loadState(id);
  state.n = (state.n || 0) + 1;
  saveState(id, state);
  return state.n;
}
