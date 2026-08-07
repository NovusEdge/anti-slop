#!/usr/bin/env node
/**
 * anti-slop hook — checks Claude's output for banned patterns
 * Runs on Stop event, warns if violations detected
 */

const BANNED_WORDS = [
  'delve', 'leverage', 'harness', 'foster', 'bolster', 'underscore',
  'showcase', 'illuminate', 'facilitate', 'garner', 'spearhead',
  'robust', 'seamless', 'meticulous', 'intricate', 'comprehensive',
  'pivotal', 'crucial', 'vital', 'multifaceted', 'nuanced', 'holistic',
  'vibrant', 'compelling', 'tapestry', 'landscape', 'realm', 'beacon',
  'cornerstone', 'backbone', 'lifeblood', 'paradigm', 'interplay',
  'symphony', 'moreover', 'furthermore', 'additionally', 'notably',
  'importantly', 'fundamentally', 'profound', 'transformative',
  'load-bearing', 'north star', 'deep dive', 'game-changer'
];

const BANNED_PHRASES = [
  /it's not .+, it's/i,
  /that's not .+, that's/i,
  /less .+, more/i,
  /plays a (crucial|vital|key) role/i,
  /stands as a testament/i,
  /it's worth noting/i,
  /in today's fast-paced/i,
  /let's dive in/i,
  /great question/i,
  /certainly!/i,
];

let input = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => input += chunk);
process.stdin.on('end', () => {
  try {
    const data = JSON.parse(input);
    const text = extractAssistantText(data);
    if (!text) process.exit(0);

    const violations = checkText(text);
    if (violations.length > 0) {
      console.log('\n**anti-slop:** ' + violations.length + ' violation(s) detected');
      violations.slice(0, 3).forEach(v => {
        console.log(`  - ${v.type}: "${v.match}"`);
      });
      if (violations.length > 3) {
        console.log(`  - ...and ${violations.length - 3} more`);
      }
    }
  } catch (e) {
    process.exit(0);
  }
});

function extractAssistantText(data) {
  if (data.assistant_message) return data.assistant_message;
  if (data.messages) {
    const assistant = data.messages.filter(m => m.role === 'assistant');
    if (assistant.length > 0) {
      return assistant[assistant.length - 1].content;
    }
  }
  return null;
}

function checkText(text) {
  const violations = [];
  const lower = text.toLowerCase();

  // Skip code blocks
  const noCode = text.replace(/```[\s\S]*?```/g, '').replace(/`[^`]+`/g, '');
  const lowerNoCode = noCode.toLowerCase();

  for (const word of BANNED_WORDS) {
    const regex = new RegExp(`\\b${word}\\b`, 'i');
    if (regex.test(lowerNoCode)) {
      violations.push({ type: 'word', match: word });
    }
  }

  for (const pattern of BANNED_PHRASES) {
    const match = lowerNoCode.match(pattern);
    if (match) {
      violations.push({ type: 'phrase', match: match[0] });
    }
  }

  return violations;
}
