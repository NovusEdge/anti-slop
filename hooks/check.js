#!/usr/bin/env node
// Slop detection over a transcript. inject.js is the only caller.
//
// Blocks nothing. A Stop hook cannot lint the turn that triggers it: Claude Code
// appends the final assistant message to the transcript after Stop fires, so a
// Stop hook always reads the previous turn. The lint runs at UserPromptSubmit
// instead, where the previous turn is on disk and stdout reaches the model.
//
// Reports only the patterns.json sets named in hook_confidence. ambiguous_words
// stay out: "harness", "landscape" and "robust" are real technical words.

const fs = require('fs');
const path = require('path');

const P = JSON.parse(
  fs.readFileSync(path.join(__dirname, '..', 'patterns.json'), 'utf8')
);

// Returns the last assistant text, its uuid, and the user message before it.
function lastTurn(transcriptPath) {
  const out = { assistant: null, uuid: null, user: null };
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
    if (!out.assistant && entry.type === 'assistant') {
      out.assistant = text;
      out.uuid = entry.uuid || null;
    } else if (out.assistant && entry.type === 'user') {
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

// Code, quoted examples and blockquotes are not the writer's own prose. A
// double-quoted span is how you cite slop, and this plugin's own subject is
// banned words, so flagging the citation is its most common false positive.
// The span must stay on one line; a quote that spans lines is usually prose.
function prosify(text) {
  return text
    .replace(/```[\s\S]*?```/g, '')
    .replace(/`[^`]*`/g, '')
    .replace(/"[^"\n]*"/g, '""')
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

module.exports = { check, lastTurn, sentences, prosify };
