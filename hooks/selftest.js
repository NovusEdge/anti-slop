#!/usr/bin/env node
// node hooks/selftest.js
const assert = require('assert');
const { check } = require('./check.js');

const hit = (text, user) => check(text, user).length > 0;

// Blocking sets fire.
assert.ok(hit('We leverage the cache.'), 'banned word missed');
assert.ok(hit("It's not a cache, it's a buffer."), 'contrast construction missed');
assert.ok(hit('This is load-bearing for the retry path.'), 'phrase missed');
assert.ok(hit('Three things matter here.'), 'counting missed');
assert.ok(hit('To be clear, the lock is held.'), 'meta-commentary missed');
assert.ok(
  hit('- **One** a\n- **Two** b\n- **Three** c'),
  'bold-every-bullet missed'
);

// Ambiguous words never block.
assert.ok(!hit('The harness runs the hook.'), 'ambiguous word blocked');
assert.ok(!hit('A robust retry covers the landscape.'), 'ambiguous words blocked');

// Code and quotes are not prose.
assert.ok(!hit('Use `leverage` as the example word.'), 'inline code not skipped');
assert.ok(!hit('```\nWe leverage it.\n```'), 'fence not skipped');
assert.ok(!hit('> we leverage the cache'), 'blockquote not skipped');
assert.ok(
  !hit('If you ask "should we leverage the cache?", the reply may repeat it.'),
  'double-quoted citation not skipped'
);
// A quote must close on its own line to count as a citation.
assert.ok(hit('He said "we leverage\nthe cache" yesterday.'), 'multiline quote skipped');

// A word the user used is not the assistant's slop.
assert.ok(
  !hit('We leverage it there.', 'should we leverage the cache?'),
  'user-supplied word still blocked'
);

// Clean prose passes.
assert.ok(!hit('The registry holds one lock per vm. Stop() only signals.'), 'false positive');

// Findings carry the offending sentence, not just the word.
const found = check('The lock is fine. We leverage the cache heavily.');
assert.strictEqual(found.length, 1);
assert.match(found[0].sentence, /leverage the cache/);
assert.ok(!found[0].sentence.includes('lock is fine'), 'sentence split failed');

console.log('selftest ok');
