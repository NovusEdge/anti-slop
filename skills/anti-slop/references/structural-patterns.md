# Structural Patterns to Avoid

Patterns that mark text as LLM-generated or LinkedIn-brained, independent of vocabulary.

## The Contrast Construction

Never define a thing by first negating something the reader did not say. The pattern manufactures a wrong answer so the right one has something to beat.

**Banned forms:**
- "it's not X, it's Y"
- "X isn't just Y"
- "that's A, not B"
- "less A, more B"
- "this isn't about A, it's about B"
- "the real question isn't A, it's B"
- "not because A, but because B"

Any word order, any tense. Still counts when buried mid-sentence, when it spans two sentences, and when the negated half is implied.

**Fix:** Delete the negated half. State the real thing on its own.

**Before:** "It's not about writing less code, it's about writing clearer code."

**After:** "Clarity matters more than brevity here."

## LinkedIn Cadence

### One-line paragraph for punch

A sentence set apart as its own paragraph to create false drama.

**Before:**
```
The system processed 10 million requests.

Without a single failure.

That's what reliability looks like.
```

**After:**
```
The system processed 10 million requests without a single failure.
```

### Rhetorical question answered immediately

**Before:** "What makes a great engineer? It's not about knowing everything. It's about knowing how to learn."

**After:** "Great engineers learn fast." (or just cut it)

### Closing aphorism

Restating the paragraph as a slogan.

**Before:** "We refactored the payment flow, added retries, and fixed the race condition. At the end of the day, it's all about building systems that work."

**After:** "We refactored the payment flow, added retries, and fixed the race condition."

### Counting what follows

**Before:** "Three things matter here: speed, reliability, and cost."

**After:** "Speed, reliability, and cost matter here."

## Meta-Commentary

Text about the text itself. Cut it.

- "To be clear, ..."
- "Quick framing first: ..."
- "I don't want this read as..."
- "Let me explain what I mean by..."
- "Before I answer, ..."
- "The short answer is... The long answer is..."

If the work is scoped right, it shows. If it needs framing, the framing is part of the content, not a disclaimer.

## The Servile Closer

A sign-off that hands the decision back instead of ending the message. It performs eagerness and adds a turn.

**Banned forms:**
- "Say the word and I'll ..."
- "Just let me know", "Let me know if you'd like ..."
- "Happy to ...", "I'd be glad to ..."
- "Feel free to ..."
- "Hope this helps"
- "Shall I proceed?", "Does that work for you?"

State what remains available and stop. The reader knows they can reply.

**Before:** "I fixed the retry path. Happy to also add the metrics counter, just say the word!"

**After:** "I fixed the retry path. The metrics counter is untouched."

Ask a real question when the answer changes the work and you cannot pick a default. Then ask it plainly, on its own line, and ask nothing else.

**Before:** "Let me know if you'd like me to use Postgres or SQLite, or if you have another preference, happy to go either way."

**After:** "Postgres or SQLite?"

## The Staged Trigger

An offer of undone work, written as a standing order the reader has to fire. It reads as a demand for a command word, and the reader has to answer it in the shape you chose.

**Banned forms:**
- "Say the word and I'll ..."
- "Point me at the file and I'll ..."
- "Once you confirm the scope, I'll ..."
- "Give me the go-ahead and I'll ..."

Ask for the work as a question, or offer it as a capability. Both let the reader answer yes or no.

**Before:** "Say the word on scope and I will rewrite status.md against current state, flip the COSTS.md mic row, and refresh the two CHECKPOINT.md lines."

**After:** "Would you like me to rewrite status.md, flip the COSTS.md mic row, and refresh the CHECKPOINT.md lines?"

"I can rewrite status.md against current state if you want" carries the same offer and stays a sentence.

## Structural Tells

### Three-item lists where two are real

Padding to hit a "rule of three".

**Before:** "This change improves performance, readability, and overall code quality."

**After:** "This change improves performance and readability." (if "code quality" is just restating "readability")

### Uniform sentence length

Every sentence in a paragraph being roughly the same length is a tell. Vary naturally.

### Bolding in every bullet

- **Important thing one** — explanation
- **Important thing two** — explanation
- **Important thing three** — explanation

If everything is bold, nothing is. Bold sparingly or not at all.

### Title Case In Every Heading

Use sentence case. "How to configure the cache", not "How To Configure The Cache".

### Emoji as section markers

Don't use emoji to mark sections unless the context demands it (e.g., a changelog for a consumer app).

## Detection Heuristics

These patterns are mechanical enough to grep:

1. **Contrast construction:** regex for "not X, it's Y" patterns
2. **Banned vocabulary:** word list match
3. **Sentence length uniformity:** stddev of word counts per sentence
4. **Em-dash frequency:** more than 2 per paragraph is a tell. Two is one parenthetical pair.
5. **Perfect tense:** "has been", "have been", "had been"
6. **-ing sentence openers:** sentences starting with gerunds
7. **Meta phrases:** "to be clear", "it's worth noting", "the reality is"

The semantic rules (one fact per sentence, concrete over abstract, constraint vs mechanism) need human judgment.

<!-- anti-slop: ignore-file (this file quotes the banned patterns) -->
