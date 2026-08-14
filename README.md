# anti-slop

A Claude Code plugin that steers models toward clear, terse technical prose. It injects a writing directive at the top of context before the model writes, then lints what leaks through.

## Install

Inside Claude Code:

```
/plugin marketplace add NovusEdge/anti-slop
/plugin install anti-slop@anti-slop
```

From a shell: `curl -fsSL https://raw.githubusercontent.com/NovusEdge/anti-slop/main/install.sh | bash`, or `./install.sh --local` from a checkout. Restart Claude Code after.

## What it does

The lever is a directive injected at `SessionStart` and `SubagentStart`, so it lands in the first tokens of context and steers the model before it generates. The linter and the mid-turn hooks are the backstop for what slips past it.

The directive splits across `hooks/rules/`. `core.md` injects at session start and applies to every reply. A deterministic router then injects one more file the first time it fits: `code.md` when the model edits a source file, `prose.md` when it edits a doc, `commit.md` when it runs `git commit`. Each routed file injects once per session. The router picks from the tool name and the file extension, nothing else.

The directive carries seven rules:

1. **Surgical brevity** — Lead with the outcome. No preamble, no closing summary of work the diff already shows. One or two sentences of framing on a routine change.
2. **One adjective** — "A clean solution", never "a clean, simple, elegant solution".
3. **Banned vocabulary** — `delve`, `leverage`, `crucial`, `tapestry`, `load-bearing`, and about forty more. The lists hold stems, so `leverages`, `delving` and `fostered` match too.
4. **No contrast constructions** — `it's not X, it's Y`, `X isn't just Y`, rhetorical questions, closing aphorisms.
5. **No sycophancy** — No opening flattery, no praise for the reader's idea, no apology inflation. A correction is a claim: verify it, then state the corrected fact alone.
6. **No servile closer** — No `say the word and I'll`, `happy to`, `hope this helps`. Name what is still available and stop.
7. **STE grammar** — One fact per sentence, active voice, simple tenses, no dropped articles. Based on ASD-STE100.

A hard word cap is deliberately absent. Anthropic capped Claude Code responses at 100 words in April 2026 and reverted it four days later after a 3% eval drop. The length check here reports and never blocks.

## Usage

```
/anti-slop:anti-slop            audit prose: comments, docstrings, commits, PR bodies, docs
/anti-slop:anti-slop-code       audit and trim code: narrator comments, dead generality, mock tests
```

## Code and documentation

`anti-slop-code` covers source and the documentation around it: comments that restate the line below, defensive wrappers around code that cannot throw, tests that assert mocks, docstrings that repeat the signature.

```bash
# comments and docstrings, extracted per language
python3 tools/lint.py --code src/

# structural checks that need a parse
python3 tools/ast_check.py src/
```

`lint.py --code` reads comments in Python, JavaScript, TypeScript, Go, Rust, Java and a dozen more, blanking string literals first so a url does not read as a comment. It flags narrator comments, step numbering, deferral text, hedging, placeholder prose, vacuous code (`if True`, `x == x`), and test smells (`assert True`, asserting on a mock).

`ast_check.py` catches what a regex cannot: a comment whose words all come from the statement below it, two variables holding the same value, `except: pass`, and `if/else` returning `True`/`False`. Python needs nothing installed. The other languages need tree-sitter, and the tool names the files it skipped without it:

```bash
pip install tree-sitter tree-sitter-language-pack
```

## Hooks

Four hooks run without being invoked.

| Hook | When | What |
|---|---|---|
| `SessionStart` | startup, resume, clear, **compact** | Injects `rules/core.md`. The `compact` matcher restores the rules after a summarization drops them. |
| `SubagentStart` | every subagent and workflow agent | Injects `core.md` into the fresh context a subagent starts with. |
| `PostToolUse` | every tool call | Routes one context rule file in (`code`/`prose`/`commit`, once each per session), then lints the prose written so far and reports a finding next to the tool result. |
| `UserPromptSubmit` | every prompt | Lints the previous turn and names what `PostToolUse` did not reach. Every 9th prompt it restates a one-line reminder. |

Nothing blocks. A `Stop` hook can send the model back to rewrite, but that costs a second message. `PostToolUse` and `UserPromptSubmit` carry their findings as `additionalContext` at a point where the model is about to write anyway, so a finding steers the next words and adds no generation.

Change the reminder cadence with `ANTI_SLOP_REMIND_EVERY=5` (default 9). Turn it off with `/plugin disable anti-slop`.

### The capitulation check

Reflexive agreement is the sycophancy that a single sentence cannot reveal. "You're right, I'll fix that" is correct when the writer checked the claim first, and a fold when nobody checked. The hook reports it only when all three hold:

1. The user's message carries a pushback marker (`no`, `wrong`, `actually`, `are you sure`, …).
2. The reply's first two sentences open by agreeing (`you're right`, `good catch`, `my mistake`, …).
3. The reply cites nothing: no `file:line`, no path, no command output, no number with a unit.

An agreement backed by `worker.go:88` never trips it, and a reply that disagrees never trips it. The three marker lists live in `patterns.json`.

### False positives

The hook reports only the sets named in `hook_confidence` in `patterns.json`. Three exclusions keep it usable: `ambiguous_words` (`harness`, `robust`, …) never fire; a word the user wrote is skipped; fenced code, inline code, blockquotes, and quoted spans are skipped. Known misses the word list cannot avoid: `leverage` as the finance noun, `Foster` as a surname. The STE and em-dash sets stay out of the hook for the same reason.

## Linter

```bash
python tools/lint.py README.md          # check a file
python tools/lint.py --check README.md   # exit 1 on violations, for CI
python tools/lint.py --all README.md     # add the ambiguous words (robust, harness, ...)
python tools/lint.py --json README.md    # JSON output
echo "We leverage seamless infra" | python tools/lint.py
```

`ambiguous_words` stay behind `--all`. They are real technical words, and a commit gate that fails on `robust` gets disabled within a week.

### Pre-commit hook

```yaml
- repo: https://github.com/NovusEdge/anti-slop
  rev: main
  hooks:
    - id: anti-slop            # markdown files
    - id: anti-slop-commit-msg # the commit message
      stages: [commit-msg]
```

The commit-message hook needs `pre-commit install --hook-type commit-msg`. It skips `#` lines, so the diff that `git commit -v` appends stays out of the lint.

## Quick reference

| Don't | Do |
|---|---|
| `Let me walk you through what I did.` | (lead with the outcome, cut the preamble) |
| `A clean, simple, elegant solution.` | `A clean solution.` |
| `leverage the cache` | `use the cache` |
| `This is load-bearing` | `The retry loop reads this on every attempt` |
| `It's not about X, it's about Y` | State Y directly |
| `robust error handling` | `retries three times, then fails` |
| `You're absolutely right, I'll fix it` | `The lock order is reversed at vm.go:41.` |

If you wouldn't say it to a colleague in a hallway, rewrite it.

## License

MIT
