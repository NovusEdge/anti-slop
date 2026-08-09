# anti-slop

A Claude Code plugin that enforces clear technical prose. Removes AI-generated text markers, enforces Simplified Technical English grammar, and bans LinkedIn cadence.

## Install

Inside Claude Code:

```
/plugin marketplace add NovusEdge/anti-slop
/plugin install anti-slop@anti-slop
```

From a shell:

```bash
curl -fsSL https://raw.githubusercontent.com/NovusEdge/anti-slop/main/install.sh | bash
```

From a local checkout:

```bash
./install.sh --local
```

Restart Claude Code after any of them.

## What it does

Three layers, applied together:

1. **STE grammar** — One fact per sentence, active voice, simple tenses, short sentences, no dropped articles. Based on ASD-STE100.

2. **Banned vocabulary** — Words that mark text as LLM-generated: `delve`, `leverage`, `robust`, `crucial`, `tapestry`, `load-bearing`, `it's worth noting`, and about forty more.

3. **Structural hygiene** — No contrast constructions (`it's not X, it's Y`), rhetorical questions, closing aphorisms, or meta-commentary.

## Usage

```
/anti-slop:anti-slop            invoke the skill
/anti-slop:anti-slop review     review and fix text
```

## Hooks

Three hooks run without being invoked.

| Hook | When | What |
|---|---|---|
| `SessionStart` | startup, resume, clear, **compact** | Injects `hooks/rules.md` into context. The `compact` matcher restores the rules after a summarization drops them. |
| `UserPromptSubmit` | every 10th prompt | Re-states a one-line reminder. A rule stated once at turn 1 stops steering by turn 40. |
| `Stop` | end of each assistant turn | Scans the turn. On a violation it blocks and quotes the offending sentences. |

Change the reminder cadence with `ANTI_SLOP_REMIND_EVERY=5`. Turn the whole thing off with `/plugin disable anti-slop`.

The `Stop` hook blocks only on the pattern sets listed in `hook_confidence` in `patterns.json`. `ambiguous_words` (`harness`, `landscape`, `robust`, `key`, …) stay out of it — they are real technical words, and blocking a turn over one teaches you to disable the plugin. The standalone linter still reports them.

It also skips a word you used in your own message. Echoing your vocabulary back is not slop.

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
- repo: https://github.com/NovusEdge/anti-slop
  rev: main
  hooks:
    - id: anti-slop
```

## Quick reference

### Worst offenders

| Don't | Do |
|---|---|
| `leverage the cache` | `use the cache` |
| `This is load-bearing` | `The retry loop reads this on every attempt` |
| `It's not about X, it's about Y` | State Y directly |
| `robust error handling` | `retries three times, then fails` |

### The hallway test

If you wouldn't say it to a colleague in a hallway, rewrite it.

## Files

```
anti-slop/
├── .claude-plugin/
│   ├── plugin.json
│   └── marketplace.json
├── patterns.json          # single source for banned words/phrases
├── hooks/
│   ├── hooks.json
│   ├── rules.md           # text injected at SessionStart
│   ├── inject.js          # SessionStart + UserPromptSubmit
│   ├── lint-output.js     # Stop
│   └── selftest.js
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
├── .pre-commit-hooks.yaml
├── install.sh
└── README.md
```

## License

MIT
