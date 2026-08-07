# anti-slop

A Claude Code plugin that enforces clear technical prose. Removes AI-generated text markers, enforces Simplified Technical English grammar, and bans LinkedIn cadence.

## Install

```bash
# One-liner
curl -fsSL https://raw.githubusercontent.com/NovusEdge/anti-slop/main/install.sh | bash

# Or via plugin command
/plugin install NovusEdge/anti-slop

# Or manual
git clone https://github.com/NovusEdge/anti-slop ~/.claude/plugins/anti-slop
```

## What it does

Three layers, applied together:

1. **STE grammar** — One fact per sentence, active voice, simple tenses, short sentences, no dropped articles. Based on ASD-STE100.

2. **Banned vocabulary** — Words that mark text as LLM-generated: delve, leverage, robust, crucial, tapestry, "load-bearing", "it's worth noting", etc.

3. **Structural hygiene** — No contrast constructions ("it's not X, it's Y"), rhetorical questions, closing aphorisms, or meta-commentary.

## Usage

```bash
/anti-slop              # invoke the skill
/anti-slop review       # review and fix text
```

The plugin also runs a hook on Stop events to warn about violations in Claude's output.

## Linter

Standalone Python linter for CI/pre-commit:

```bash
# Check a file
python tools/lint.py README.md

# Check with exit code (for CI)
python tools/lint.py --check README.md

# JSON output
python tools/lint.py --json README.md

# Stdin
echo "We leverage robust infrastructure" | python tools/lint.py
```

### Pre-commit hook

Add to `.pre-commit-config.yaml`:

```yaml
- repo: local
  hooks:
    - id: anti-slop
      name: anti-slop
      entry: python ~/.claude/plugins/anti-slop/tools/lint.py --check
      language: system
      types: [markdown]
```

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
├── hooks/
│   ├── hooks.json
│   └── lint-output.js
├── tools/
│   └── lint.py
├── skills/
│   └── anti-slop/
│       ├── SKILL.md
│       └── references/
│           ├── banned-vocabulary.md
│           ├── ste-rules.md
│           └── structural-patterns.md
├── examples/
│   └── before-after.md
├── install.sh
└── README.md
```

## License

MIT
