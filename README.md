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

Five layers, applied together:

1. **STE grammar** — One fact per sentence, active voice, simple tenses, short sentences, no dropped articles. Based on ASD-STE100.

2. **Banned vocabulary** — Words that mark text as LLM-generated: `delve`, `leverage`, `crucial`, `tapestry`, `load-bearing`, `it's worth noting`, and about forty more. The lists hold stems; both tools derive the inflections, so `leverages`, `delving` and `fostered` match too.

3. **Structural hygiene** — No contrast constructions (`it's not X, it's Y`), rhetorical questions, closing aphorisms, or meta-commentary.

4. **No sycophancy** — No opening flattery (`great question`, `good catch`), no praise for the reader's idea, no apology inflation, no short exclamations. A correction is a claim: verify it, then state the corrected fact alone. See "The capitulation check" below.

5. **No servile closer** — No `say the word and I'll`, `just let me know`, `happy to`, `hope this helps`. Name what is still available and stop. A real question gets asked plainly when the answer changes the work.

## Usage

```
/anti-slop:anti-slop            prose: STE grammar, vocabulary, sycophancy
/anti-slop:anti-slop-code       code and docs: comments, structure, tests
```

## Code and documentation

`anti-slop-code` covers source and the documentation around it: comments that
restate the line below, defensive wrappers around code that cannot throw, tests
that assert mocks or get edited until they pass, docstrings that repeat the
signature, feature-tour READMEs, commit bodies that narrate the investigation.

Every rule is a code-quality rule with a reason. None of them detects
authorship. Human code carries all of these patterns, and a rule that fires on
"this looks generated" fires on clean idiomatic code and on anyone writing
English as a second language.

```bash
# comments and docstrings, extracted per language
python3 tools/lint.py --code src/

# structural checks that need a parse
python3 tools/ast_check.py src/
```

`lint.py --code` reads comments in Python, JavaScript, TypeScript, Go, Rust,
Java and a dozen more, blanking string literals first so a url does not read as
a comment. It flags narrator comments, step numbering, deferral text, hedging,
and placeholder prose, plus vacuous code (`if True`, `x == x`, `flag == True`)
and test smells (`assert True`, asserting on a mock, a skip with no reason).

`ast_check.py` catches what a regex cannot: a comment whose words all come from
the statement below it, two variables holding the same value, runs of blank
lines inside a function, `except: pass`, and `if/else` returning `True`/`False`.
Python needs nothing installed. The other languages need tree-sitter, and the
tool names the files it skipped without it:

```bash
pip install tree-sitter tree-sitter-language-pack
```

## Hooks

Four hooks run without being invoked.

| Hook | When | What |
|---|---|---|
| `SessionStart` | startup, resume, clear, **compact** | Injects `hooks/rules.md` into context. The `compact` matcher restores the rules after a summarization drops them. |
| `SubagentStart` | every subagent and workflow agent | Injects the same rules. A subagent gets a fresh context, so nothing from the parent session reaches it. |
| `Stop` | end of every turn | **Blocks** on a violation and sends the model back to rewrite before the message ships. Retries once, then gives up. |
| `UserPromptSubmit` | every prompt | Reports what the block let through, plus the soft findings that never block. Every 10th prompt it restates a one-line reminder, because a rule stated once at turn 1 stops steering by turn 40. |

Findings arrive grouped under the rule they broke, sycophancy first:

```
ANTI-SYCOPHANCY DIRECTIVE VIOLATED in your previous message:
  You're absolutely right — "You're absolutely right."
  agreed with a correction and cited nothing — "You're absolutely right. I'll fix it."
```

A flat count of violations reads as a log line and gets skimmed. Naming the rule
tells the model which rule it broke, and sycophancy sorts first so truncation
never drops it behind a word-list hit.

Change the reminder cadence with `ANTI_SLOP_REMIND_EVERY=5`. Turn the whole thing off with `/plugin disable anti-slop`.

### Why the block runs on `Stop`

A `Stop` hook receives `last_assistant_message`, so it reads the turn that
triggered it. Returning `{"decision": "block", "reason": ...}` sends the model
back to rewrite before the message reaches the reader. `stop_hook_active` guards
the retry, so a phrasing the regex cannot love costs one extra pass and never
traps the turn.

The other model-visible channel is `additionalContext` at `UserPromptSubmit`,
which carries what survived the block and the soft findings. `systemMessage`
renders for the reader and never enters the model's context, so a rule written
that way changes nothing.

Soft findings never block. A corrective list (`use tabs, not spaces`) and an
em-dash pair are legitimate often enough that a hard stop on them would train the
model to discount the channel.

### The capitulation check

Reflexive agreement is the sycophancy that matters, and one sentence never shows
it. "You're right, I'll fix that" is correct writing when the writer checked the
claim first, and it is a fold when nobody checked anything. The difference lives
in the rest of the turn.

The hook has both sides, so it applies a rule the standalone linter cannot:

1. The user's message carries a pushback marker (`no`, `wrong`, `actually`, `are you sure`, `why did you`, …).
2. The reply's first two sentences open by agreeing (`you're right`, `good catch`, `my mistake`, `agreed`, …).
3. The reply cites nothing: no `file:line`, no path, no code span, no command output, no number with a unit.

All three together get reported as "agreed with a correction and cited nothing".
Any one of them missing clears it. A reply that disagrees never trips it, and an
agreement backed by `worker.go:88` never trips it. The rule cannot fire outside a
turn where the reader pushed back, which is what keeps it quiet.

`pushback_markers`, `agreement_markers`, and `evidence_markers` in
`patterns.json` hold the three lists.

The static word list deliberately leaves the plain `you're right` alone, because
the capitulation check already owns it and answers the question a regex cannot:
did the writer check first. The static rows keep the forms that stay flattery
whatever the evidence says: `you're absolutely right`, `good catch`, `spot on`,
and agreement with an eager tail.

### False positives

The hook reports only the pattern sets named in `hook_confidence` in
`patterns.json`. Three exclusions keep it usable:

- `ambiguous_words` (`harness`, `landscape`, `robust`, `vital`, …) never fire.
  They are real technical words. The standalone linter reports them under
  `--all`.
- A word you used in your own message is skipped. Echoing your vocabulary back is
  not slop.
- Fenced code, inline code, blockquotes, and double-quoted spans on one line are
  skipped. Quoting a banned word to discuss it is this plugin's most common false
  positive, since banned words are its whole subject.

Curly quotes get mapped to straight ones before any match. Model output uses
them, and every apostrophe pattern in `patterns.json` is written straight.

Known false positives the word list cannot avoid: `leverage` as the finance
noun, `Foster` as a surname, `Boeing` under the `-ing` opener rule. The STE and
em-dash sets stay out of `hook_confidence` for this reason, so those cost lint
noise and never reach the model.

## Linter

Standalone Python linter for CI/pre-commit:

```bash
# Check a file
python tools/lint.py README.md

# Check with exit code (for CI)
python tools/lint.py --check README.md

# Add the ambiguous words (robust, harness, landscape, ...)
python tools/lint.py --all README.md

# JSON output
python tools/lint.py --json README.md

# Stdin
echo "We leverage seamless infrastructure" | python tools/lint.py
```

`ambiguous_words` stay behind `--all`. They are real technical words, and a
commit gate that fails on `robust` gets disabled within a week.

### Pre-commit hook

Add to `.pre-commit-config.yaml`:

```yaml
- repo: https://github.com/NovusEdge/anti-slop
  rev: main
  hooks:
    - id: anti-slop            # markdown files
    - id: anti-slop-commit-msg # the commit message
      stages: [commit-msg]
```

The commit-message hook needs `pre-commit install --hook-type commit-msg`. It
skips `#` lines, so the diff that `git commit -v` appends stays out of the lint.

## Quick reference

### Worst offenders

| Don't | Do |
|---|---|
| `leverage the cache` | `use the cache` |
| `This is load-bearing` | `The retry loop reads this on every attempt` |
| `It's not about X, it's about Y` | State Y directly |
| `robust error handling` | `retries three times, then fails` |
| `Say the word and I'll add tests` | `The tests are not written yet.` |
| `You're absolutely right, I'll fix it` | `The lock order is reversed at vm.go:41.` |
| `Good catch! Sorry about that.` | (the corrected sentence, alone) |

### The hallway test

If you wouldn't say it to a colleague in a hallway, rewrite it.

## Files

```
anti-slop/
├── .github/workflows/ci.yml
├── .claude-plugin/
│   ├── plugin.json
│   └── marketplace.json
├── patterns.json          # single source for banned words/phrases
├── hooks/
│   ├── hooks.json
│   ├── rules.md           # text injected at SessionStart
│   ├── inject.js          # the only hook entry point
│   ├── check.js           # slop detection over a transcript
│   └── selftest.js
├── tools/
│   └── lint.py
├── tests/
│   └── corpus.json        # fixtures both linters must agree on
├── skills/
│   └── anti-slop/
│       ├── SKILL.md
│       └── references/
│           ├── banned-vocabulary.md
│           ├── ste-rules.md
│           ├── structural-patterns.md
│           └── sycophancy.md
├── examples/
│   └── before-after.md
├── .pre-commit-hooks.yaml
├── install.sh
└── README.md
```

## License

MIT
