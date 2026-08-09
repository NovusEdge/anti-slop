---
name: anti-slop
description: "Enforce clear technical prose — STE grammar, no AI buzzwords, no LinkedIn cadence. Default mode for code comments, docstrings, commit messages, PR bodies."
version: 0.1.0
---

# anti-slop

A writing discipline for technical prose that humans have to read: code comments, docstrings, commit bodies, PR descriptions, design docs, READMEs.

Three layers, applied together:

1. **STE grammar** — Simplified Technical English rules from ASD-STE100. One fact per sentence, active voice, simple tenses, short sentences, no dropped articles.
2. **Banned vocabulary** — Words and phrases that mark text as LLM-generated on sight. Reach for the ordinary word.
3. **Structural hygiene** — No contrast constructions, rhetorical questions, LinkedIn cadence, or meta-commentary about the text itself.

## When to Use

- Writing or reviewing code comments, docstrings, commit messages
- Drafting PR descriptions or design doc sections
- Any prose a developer will read repeatedly
- Agent-to-agent messages where ambiguity has cost

Not for: marketing copy, user-facing content that needs voice, creative writing.

## The Rules

### STE Grammar

| Rule | Do | Don't |
|---|---|---|
| One fact per sentence | Split on "and" or comma splice | "X and also Y which means Z" |
| Short sentences | Under ~20 words | Drop subject/verb/article to hit count |
| Simple tenses | "returns", "failed" | "has been returning", "will have failed" |
| Active voice | "qemu unlinks the socket" | "the socket is unlinked" |
| No -ing sentence openers | "handles", "uses" | "Handling the case where..." |
| Articles on countable nouns | "the lock", "a socket" | "lock ensures..." |
| Noun stacks ≤3 words | "vm registry lock" | "vm registry lock timeout retry config" |
| Concrete over abstract | A name, type, number | "the system", "various parts" |

See `references/ste-rules.md` for the full 12 rules with examples.

### Banned Vocabulary

**The worst offender:** "load-bearing" — say what actually depends on it.

**Puffed verbs/adjectives:** delve, leverage, harness, foster, bolster, underscore, showcase, illuminate, facilitate, garner, navigate (figurative), unpack (figurative), elevate, streamline, spearhead, robust, seamless, meticulous, intricate, comprehensive, pivotal, crucial, vital, key (adj), multifaceted, nuanced, holistic, vibrant, compelling

**Metaphor nouns:** tapestry, landscape, realm, ecosystem (outside software), beacon, cornerstone, backbone, lifeblood, north star, journey, deep dive, game-changer, paradigm, interplay, symphony

**Significance inflation:** "a testament to", "stands as", "serves as", "plays a crucial role", "underscores the importance of", "marks a shift", "at its core", "the reality is", "it's worth noting", "fundamentally", "profound", "transformative", "powerful" (about code), "elegant" (about your own work)

**Transition scaffolding:** moreover, furthermore, additionally, notably, importantly, "that said" (paragraph opener), "in today's fast-paced X", "when it comes to X", "let's dive in"

**Hedge-and-flatter openers:** "Great question", "You're absolutely right", "I hope this finds you well", "Certainly!", "Absolutely."

See `references/banned-vocabulary.md` for the complete list with rationale.

### Structural Patterns to Avoid

**Contrast construction** — Never define a thing by first negating something unstated:
- "it's not X, it's Y"
- "X isn't just Y"
- "less A, more B"
- "the real question isn't A, it's B"

Delete the negated half. State the real thing on its own.

**LinkedIn cadence:**
- One-line paragraph dropped in for punch
- Rhetorical question you then answer yourself
- Closing aphorism restating the paragraph as a slogan
- Counting what follows ("Three things...", "Two reasons...")

**Meta-commentary:**
- "To be clear", "Quick framing first"
- "I don't want this read as..."
- Recapping what the reader already sees

**Structural tells:**
- Three-item lists where two items are real
- Uniform sentence length across a paragraph
- Bolding a phrase in every bullet
- Emoji as section markers

See `references/structural-patterns.md` for detection heuristics.

## Process

1. **Draft normally.** Don't self-censor while writing.
2. **Scan for banned vocab.** Ctrl+F the worst offenders (delve, leverage, robust, crucial).
3. **Check sentence structure.** Split compound sentences. Convert passive to active.
4. **Cut meta-commentary.** Delete sentences about the text itself.
5. **Read aloud.** If you wouldn't say it to a colleague in a hallway, rewrite it.

## Output

When reviewing text, produce a table:

```markdown
| Violation | Original | Fixed |
|---|---|---|
| Banned: "leverage" | "leverage the cache" | "use the cache" |
| Passive voice | "the file is deleted" | "the handler deletes the file" |
| Contrast construction | "It's not about speed, it's about correctness" | "Correctness matters more here" |
```

If the text already complies, say so. Don't force changes onto clean prose.

## Boundaries

**Will:**
- Flag banned vocabulary and suggest replacements
- Rewrite passive voice, compound tenses, -ing openers
- Detect and remove contrast constructions
- Strip meta-commentary and LinkedIn cadence

**Will not:**
- Simplify creative or marketing copy where voice matters
- Drop precision to shorten sentences
- Enforce rules inside code fences or inline code spans

<!-- anti-slop: ignore-file (this file quotes the banned patterns) -->
