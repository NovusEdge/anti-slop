#!/usr/bin/env node
// SessionStart and UserPromptSubmit hook. Both events add stdout to the context.
//
// SessionStart fires on startup, resume, clear, and compact. The compact matcher
// is what restores the rules after a summarization drops them.
//
// UserPromptSubmit does two jobs. It lints the previous assistant turn, which is
// on disk by now, and it restates a one-line reminder every REMIND_EVERY
// prompts, because a rule stated once at turn 1 stops steering by turn 40.

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

  // Stop carries last_assistant_message, so the turn that triggered the hook is
  // readable here. A block sends the model back to rewrite before the message
  // ships. systemMessage reaches the user only, so an advisory tier is invisible
  // to the model and changes nothing.
  if (data.hook_event_name === 'Stop') {
    stopGate(data);
    return;
  }

  if (data.hook_event_name !== 'UserPromptSubmit') {
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

// One retry only. A phrasing the regex cannot love must not trap the turn.
function stopGate(data) {
  if (data.stop_hook_active) return process.exit(0);
  const message = data.last_assistant_message;
  if (!message) return process.exit(0);

  // A soft finding reports on the next turn and never blocks. Length is soft:
  // a report the reader asked for is allowed to be long.
  const violations = check(message, '').filter(v => !v.soft);
  if (!violations.length) return process.exit(0);

  const lines = violations
    .slice(0, MAX_REPORTED)
    .map(v => `  ${DIRECTIVE[v.kind] || DIRECTIVE.default}: ${v.match} — "${v.sentence}"`);

  process.stdout.write(
    JSON.stringify({
      decision: 'block',
      reason:
        'Your message breaks anti-slop rules:\n' +
        lines.join('\n') +
        '\nRewrite the offending sentences so each states the thing directly, ' +
        'then reply with the corrected message. Do not narrate the correction.',
    })
  );
  process.exit(0);
}

function report(data) {
  const state = loadState(data.session_id);
  const turn = lastTurn(data.transcript_path);
  if (!turn.assistant) return [];
  // Each turn is reported once. Without this the same text repeats every prompt.
  if (turn.uuid && turn.uuid === state.lastUuid) return [];
  saveState(data.session_id, { ...state, lastUuid: turn.uuid });

  const violations = check(turn.assistant, turn.user);
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
