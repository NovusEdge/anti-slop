# anti-slop

A Claude Code plugin that enforces clear technical prose. Removes AI-generated text markers, enforces Simplified Technical English grammar, and bans LinkedIn cadence.

## Install

```bash
/plugin install NovusEdge/anti-slop
```

Or clone and install locally:

```bash
git clone https://github.com/NovusEdge/anti-slop ~/.claude/plugins/anti-slop
```

## What it does

Three layers, applied together:

1. **STE grammar** — One fact per sentence, active voice, simple tenses, short sentences, no dropped articles. Based on ASD-STE100.

2. **Banned vocabulary** — Words that mark text as LLM-generated: delve, leverage, robust, crucial, tapestry, "load-bearing", "it's worth noting", etc.

3. **Structural hygiene** — No contrast constructions ("it's not X, it's Y"), rhetorical questions, closing aphorisms, or meta-commentary.

## When to use

- Code comments and docstrings
- Commit messages and PR descriptions
- Design docs and READMEs
- Agent-to-agent messages

Not for marketing copy or content where voice matters.

## Quick reference

### Worst offenders

| Don't | Do |
|---|---|
| "leverage the cache" | "use the cache" |
| "This is load-bearing" | "The retry loop reads this on every attempt" |
| "It's not about X, it's about Y" | State Y directly |
| "robust error handling" | "retries three times, then fails" |

### The hallway test

If you wouldn't say it to a colleague in a hallway, rewrite it.

## Files

```
anti-slop/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   └── anti-slop/
│       ├── SKILL.md
│       └── references/
│           ├── banned-vocabulary.md
│           ├── ste-rules.md
│           └── structural-patterns.md
└── README.md
```

## License

MIT
