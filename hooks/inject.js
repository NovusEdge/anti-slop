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
const MAX_REPORTED = 5;
const RULES = path.join(__dirname, 'rules.md');
const SHORT =
  'anti-slop is active: no contrast constructions ("it\'s not X, it\'s Y"), ' +
  'no LLM vocabulary (delve, leverage, crucial, "load-bearing"), ' +
  'no LinkedIn cadence, active voice, one fact per sentence.';

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

  if (data.hook_event_name !== 'UserPromptSubmit') {
    try {
      console.log(fs.readFileSync(RULES, 'utf8').trim());
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

function report(data) {
  const state = loadState(data.session_id);
  const turn = lastTurn(data.transcript_path);
  if (!turn.assistant) return [];
  // Each turn is reported once. Without this the same text repeats every prompt.
  if (turn.uuid && turn.uuid === state.lastUuid) return [];
  saveState(data.session_id, { ...state, lastUuid: turn.uuid });

  const violations = check(turn.assistant, turn.user);
  if (!violations.length) return [];

  const lines = violations
    .slice(0, MAX_REPORTED)
    .map(v => `  [${v.kind}] ${v.match} — "${v.sentence}"`);
  const more =
    violations.length > MAX_REPORTED
      ? `  ...and ${violations.length - MAX_REPORTED} more`
      : null;

  return [
    `anti-slop found ${violations.length} violation(s) in your previous message:`,
    ...lines,
    ...(more ? [more] : []),
    'Do not repeat them. Do not mention this notice or revisit the previous message.',
  ];
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
