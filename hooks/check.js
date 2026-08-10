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

// Model output uses curly quotes. Every apostrophe pattern in patterns.json is
// written with a straight quote, so "It’s not X, it’s Y" escaped the contrast
// set. The curly double quote also has to become straight before prosify strips
// quoted citations.
function normalize(text) {
  return text.replace(/[‘’]/g, "'").replace(/[“”]/g, '"');
}

// Regex for a stem and its inflections. The lists hold stems, and a bare \b stem
// \b missed "leverages", "delving" and "fostered". Mirrors inflect() in
// tools/lint.py; tests/corpus.json holds both to the same answers.
function inflect(word) {
  if (word.endsWith('ic')) return `${word}(?:ally|s)?`;
  if (word.endsWith('e')) return `${word.slice(0, -1)}(?:e|es|ed|ing|ely)`;
  // A consonant before the y takes -ies: tapestry, tapestries.
  if (word.endsWith('y') && !'aeiou'.includes(word[word.length - 2])) {
    return `(?:${word}|${word.slice(0, -1)}ies)`;
  }
  return `${word}(?:s|es|ed|ing|ly)?`;
}

// Returns every assistant text in the last turn, the uuid of its final message,
// and the user prompt that opened the turn.
//
// One turn spans many assistant entries: Claude Code writes a new entry per text
// block, so prose written before a tool call sits several entries back. Reading
// only the final entry left most of a tool-using turn unchecked.
function lastTurn(transcriptPath) {
  const out = { assistant: null, uuid: null, user: null };
  if (!transcriptPath || !fs.existsSync(transcriptPath)) return out;

  const lines = fs.readFileSync(transcriptPath, 'utf8').trim().split('\n');
  const texts = [];
  for (let i = lines.length - 1; i >= 0; i--) {
    let entry;
    try {
      entry = JSON.parse(lines[i]);
    } catch {
      continue;
    }
    if (entry.isMeta || isToolResult(entry)) continue;
    const text = textOf(entry);
    if (!text) continue;
    if (entry.type === 'assistant') {
      if (!out.uuid) out.uuid = entry.uuid || null;
      texts.unshift(text);
    } else if (entry.type === 'user' && texts.length) {
      out.user = text;
      break;
    }
  }
  out.assistant = texts.join('\n\n') || null;
  return out;
}

// A tool result is a user entry by transcript type only. It carries no prose and
// must not end the walk backwards through a turn.
function isToolResult(entry) {
  if (entry.toolUseResult !== undefined) return true;
  const content = entry.message?.content;
  return Array.isArray(content) && content.some(b => b.type === 'tool_result');
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
  return normalize(text)
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
  const userProse = normalize(userText || '').toLowerCase();
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
        const stem = new RegExp(`\\b${inflect(word)}\\b`, 'i');
        // The user's own vocabulary counts in any form they wrote it.
        if (stem.test(userProse)) continue;
        if (stem.test(sentence)) add('word', word, sentence);
      }
    }
    for (const [set, spec] of Object.entries(P._phrase_sets || {})) {
      if (!sets.includes(set) || !spec.tools.includes('hook')) continue;
      for (const entry of P[set] || []) {
        const [pattern, desc] = Array.isArray(entry) ? entry : [entry, null];
        const m = sentence.match(new RegExp(pattern, 'i'));
        if (m) add(spec.kind, desc || m[0].trim(), sentence);
      }
    }
    if (sets.includes('structural')) {
      for (const [pattern, desc] of P.structural || []) {
        if (new RegExp(pattern, 'iu').test(sentence)) add('structure', desc, sentence);
      }
    }
  }

  violations.push(...bulletBolding(prose));
  violations.push(...capitulation(prose, assistantText, userText));
  return violations;
}

const anyMatch = (patterns, text) =>
  (patterns || []).some(p => new RegExp(p, 'i').test(text));

// Reflexive agreement: the user pushed back, the reply opens by agreeing, and
// the reply cites nothing. A regex over one sentence cannot see this, because
// the same sentence is correct when the writer checked the claim first.
//
// The evidence scan runs over the raw text. prosify strips code spans and
// fences, which are most of what counts as evidence.
function capitulation(prose, raw, userText) {
  if (!userText) return [];
  if (!anyMatch(P.pushback_markers, normalize(userText))) return [];

  const opening = sentences(prose).slice(0, 2).join(' ');
  if (!opening) return [];
  const agreed = (P.agreement_markers || [])
    .map(p => opening.match(new RegExp(p, 'i')))
    .find(Boolean);
  if (!agreed) return [];
  if (anyMatch(P.evidence_markers, normalize(raw))) return [];

  return [
    {
      kind: 'sycophancy',
      match: `agreed with a correction and cited nothing (${agreed[0].trim()})`,
      sentence: clip(opening),
    },
  ];
}

// Three or more bullets that open with a bold phrase is the LinkedIn list. The
// threshold is a ratio, not all-or-nothing: one hand-edited plain bullet is how
// the pattern usually survives review.
function bulletBolding(prose) {
  const bullets = prose.split('\n').filter(l => /^\s*[-*]\s/.test(l));
  if (bullets.length < 3) return [];
  const bolded = bullets.filter(l => /^\s*[-*]\s+\*\*/.test(l));
  if (bolded.length < 3 || bolded.length / bullets.length < 0.8) return [];
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

