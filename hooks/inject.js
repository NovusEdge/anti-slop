#!/usr/bin/env node
// SessionStart and UserPromptSubmit hook. Both events add stdout to the context.
//
// SessionStart fires on startup, resume, clear, and compact. The compact matcher
// is what restores the rules after a summarization drops them.
// UserPromptSubmit re-states a one-line reminder every REMIND_EVERY prompts,
// because a rule stated once at turn 1 stops steering by turn 40.

const fs = require('fs');
const os = require('os');
const path = require('path');

const REMIND_EVERY = Number(process.env.ANTI_SLOP_REMIND_EVERY || 10);
const RULES = path.join(__dirname, 'rules.md');
const SHORT =
  'anti-slop is active: no contrast constructions ("it\'s not X, it\'s Y"), ' +
  'no LLM vocabulary (delve, leverage, crucial, robust, "load-bearing"), ' +
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

  if (data.hook_event_name === 'UserPromptSubmit') {
    if (shouldRemind(data.session_id)) console.log(SHORT);
    process.exit(0);
  }

  try {
    console.log(fs.readFileSync(RULES, 'utf8').trim());
  } catch {
    console.log(SHORT);
  }
});

// Per-session prompt counter. A missing or unreadable counter reminds rather
// than staying silent, so a wiped tmpdir does not disable the reminder.
function shouldRemind(sessionId) {
  if (!sessionId) return false;
  const file = path.join(os.tmpdir(), `anti-slop-${sessionId}.count`);
  let n = 0;
  try {
    n = parseInt(fs.readFileSync(file, 'utf8'), 10) || 0;
  } catch {
    n = 0;
  }
  n += 1;
  try {
    fs.writeFileSync(file, String(n));
  } catch {
    /* tmpdir not writable; the counter resets and reminds again */
  }
  return n % REMIND_EVERY === 0;
}
