#!/usr/bin/env node
// Stop hook. Reads the last assistant turn from the transcript and reports slop.
// Exit 2 with stderr is the only channel Claude reads back; stdout is discarded.
//
// Blocks only on patterns.json sets named in hook_confidence. ambiguous_words
// stay out of it: "harness", "landscape" and "key" are real technical words, and
// blocking a turn over one trains the user to disable the plugin.

const fs = require('fs');
const path = require('path');

const P = JSON.parse(
  fs.readFileSync(path.join(__dirname, '..', 'patterns.json'), 'utf8')
);
const MAX_REPORTED = 6;

let input = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', c => (input += c));
process.stdin.on('end', () => {
  let violations;
  try {
    const data = JSON.parse(input);
    // Without this guard the block-and-retry loop never terminates.
    if (data.stop_hook_active) process.exit(0);

    const turn = lastTurn(data.transcript_path);
    if (!turn.assistant) process.exit(0);
    violations = check(turn.assistant, turn.user);
  } catch (e) {
    process.exit(0);
  }

  if (violations.length === 0) process.exit(0);

  const lines = violations.slice(0, MAX_REPORTED).map(v =>
    `  [${v.kind}] ${v.match}\n      "${v.sentence}"`
  );
  const more =
    violations.length > MAX_REPORTED
      ? `\n  ...and ${violations.length - MAX_REPORTED} more`
      : '';

  process.stderr.write(
    `anti-slop: ${violations.length} violation(s) in your last message.\n` +
      lines.join('\n') +
      more +
      '\n\nRewrite only the sentences quoted above. Keep everything else as it is.\n' +
      'Do not mention this correction in your reply.\n'
  );
  process.exit(2);
});

// Returns the last assistant text and the user message that preceded it.
function lastTurn(transcriptPath) {
  const out = { assistant: null, user: null };
  if (!transcriptPath || !fs.existsSync(transcriptPath)) return out;

  const lines = fs.readFileSync(transcriptPath, 'utf8').trim().split('\n');
  for (let i = lines.length - 1; i >= 0; i--) {
    let entry;
    try {
      entry = JSON.parse(lines[i]);
    } catch {
      continue;
    }
    const text = textOf(entry);
    if (!text) continue;
    if (!out.assistant && entry.type === 'assistant') out.assistant = text;
    else if (out.assistant && entry.type === 'user') {
      out.user = text;
      break;
    }
  }
  return out;
}

function textOf(entry) {
  const content = entry.message?.content;
  if (typeof content === 'string') return content.trim() || null;
  if (!Array.isArray(content)) return null;
  const text = content
    .filter(b => b.type === 'text')
    .map(b => b.text)
    .join('\n');
  return text.trim() || null;
}

// Code and quoted examples are not prose. Blockquotes usually quote the user.
function prosify(text) {
  return text
    .replace(/```[\s\S]*?```/g, '')
    .replace(/`[^`]*`/g, '')
    .split('\n')
    .filter(l => !l.trimStart().startsWith('>'))
    .join('\n');
}

function sentences(prose) {
  return prose
    .split(/\n{2,}|(?<=[.!?])\s+(?=[A-Z"'—])|\n(?=[-*|#])/)
    .map(s => s.replace(/\s+/g, ' ').trim())
    .filter(Boolean);
}

function check(assistantText, userText) {
  const prose = prosify(assistantText);
  // A word the user just used is theirs. Echoing it back is not slop.
  const userProse = (userText || '').toLowerCase();
  const violations = [];
  const seen = new Set();

  const add = (kind, match, sentence) => {
    const key = `${kind}:${match}:${sentence}`;
    if (seen.has(key)) return;
    seen.add(key);
    violations.push({ kind, match, sentence: clip(sentence) });
  };

  const sets = P.hook_confidence || ['banned_words', 'banned_phrases'];

  for (const sentence of sentences(prose)) {
    if (sets.includes('banned_words')) {
      for (const word of P.banned_words) {
        if (userProse.includes(word)) continue;
        if (new RegExp(`\\b${word}\\b`, 'i').test(sentence)) {
          add('word', word, sentence);
        }
      }
    }
    if (sets.includes('banned_phrases')) {
      for (const pattern of P.banned_phrases) {
        const m = sentence.match(new RegExp(pattern, 'i'));
        if (m) add('phrase', m[0], sentence);
      }
    }
    if (sets.includes('structural')) {
      for (const [pattern, desc] of P.structural || []) {
        if (new RegExp(pattern, 'iu').test(sentence)) add('structure', desc, sentence);
      }
    }
  }

  violations.push(...bulletBolding(prose));
  return violations;
}

// Three or more bullets that each open with a bold phrase is the LinkedIn list.
function bulletBolding(prose) {
  const bullets = prose.split('\n').filter(l => /^\s*[-*]\s/.test(l));
  if (bullets.length < 3) return [];
  const bolded = bullets.filter(l => /^\s*[-*]\s+\*\*/.test(l));
  if (bolded.length !== bullets.length) return [];
  return [
    {
      kind: 'structure',
      match: 'bold phrase opening every bullet',
      sentence: clip(bullets[0]),
    },
  ];
}

function clip(s) {
  return s.length > 100 ? s.slice(0, 97) + '...' : s;
}

module.exports = { check, sentences, prosify };
