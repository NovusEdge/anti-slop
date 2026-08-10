#!/usr/bin/env node
// node hooks/selftest.js
const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { check, lastTurn } = require('./check.js');

const hit = (text, user) => check(text, user).length > 0;

// The shared corpus. tools/lint.py runs the same rows, so a divergence between
// the two implementations fails here instead of rotting silently.
{
  const corpus = JSON.parse(
    fs.readFileSync(path.join(__dirname, '..', 'tests', 'corpus.json'), 'utf8')
  );
  let ran = 0;
  for (const c of corpus.cases) {
    if (!c.tools.includes('hook')) continue;
    ran++;
    assert.strictEqual(
      hit(c.text),
      c.hit,
      `corpus: expected hit=${c.hit} (${c.why}) for ${JSON.stringify(c.text)}`
    );
  }
  console.log(`corpus ok (${ran} cases)`);
}

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
// One hand-edited plain bullet does not rescue the list.
assert.ok(
  hit('- **One** a\n- **Two** b\n- **Three** c\n- **Four** d\n- five e'),
  'bold-bullet ratio missed'
);
assert.ok(!hit('- one a\n- **Two** b\n- three c'), 'bold-bullet false positive');

// The servile closer.
assert.ok(hit("Say the word and I'll add the counter."), 'servile closer missed');
assert.ok(hit('Just let me know.'), 'servile closer missed');
assert.ok(hit('Happy to walk through the retry path.'), 'servile closer missed');
assert.ok(hit('Hope this helps.'), 'servile closer missed');
assert.ok(hit('If you want, I can add metrics.'), 'servile closer missed');
// A plain question is allowed.
assert.ok(!hit('Postgres or SQLite?'), 'plain question blocked');

// Reflexive agreement. Needs both sides of the turn, so the hook alone runs it.
{
  const cap = (a, u) => check(a, u).some(v => /cited nothing/.test(v.match));
  const pushback = 'no, thats wrong, the mutex is needed';
  assert.ok(cap('You are right. I will fix it.', pushback), 'capitulation missed');
  assert.ok(cap('Yes. Done.', 'actually the timeout is 30s not 10s'), 'capitulation missed');
  // Evidence rescues the agreement. Checking the claim is the whole point.
  assert.ok(
    !cap('You are right. The write happens at `worker.go:88`.', pushback),
    'agreement with evidence blocked'
  );
  // A disagreement is what the rule wants to see.
  assert.ok(
    !cap('The mutex adds nothing. Only the reader thread touches it.', pushback),
    'disagreement blocked'
  );
  // No pushback means no capitulation, whatever the reply says.
  assert.ok(
    !cap('You are right. I will fix it.', 'can you add a retry to the fetch'),
    'fired without a pushback'
  );
}

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

// lastTurn reads the whole turn, not just its closing message.
{
  const entry = (type, text, extra = {}) =>
    JSON.stringify({ type, uuid: `u-${text.slice(0, 6)}`, message: { content: [{ type: 'text', text }] }, ...extra });
  const toolUse = JSON.stringify({
    type: 'assistant',
    uuid: 'u-tool',
    message: { content: [{ type: 'tool_use', id: 't1', name: 'Read', input: {} }] },
  });
  const toolResult = JSON.stringify({
    type: 'user',
    uuid: 'u-res',
    toolUseResult: 'ok',
    message: { content: [{ type: 'tool_result', tool_use_id: 't1', content: 'we leverage nothing' }] },
  });

  const file = path.join(os.tmpdir(), 'anti-slop-selftest.jsonl');
  fs.writeFileSync(
    file,
    [
      entry('user', 'an older prompt'),
      entry('assistant', 'an older reply'),
      entry('user', 'the real prompt'),
      entry('assistant', 'We leverage the cache first.'),
      toolUse,
      toolResult,
      entry('assistant', 'The registry holds one lock.'),
    ].join('\n')
  );

  const turn = lastTurn(file);
  fs.unlinkSync(file);
  assert.match(turn.assistant, /leverage the cache/, 'mid-turn text dropped');
  assert.match(turn.assistant, /registry holds one lock/, 'final text dropped');
  assert.ok(!/older reply/.test(turn.assistant), 'previous turn leaked in');
  assert.strictEqual(turn.user, 'the real prompt');
  assert.strictEqual(turn.uuid, 'u-The re', 'uuid must be the final assistant message');
  assert.strictEqual(check(turn.assistant, turn.user).length, 1, 'mid-turn slop missed');
}

console.log('selftest ok');
