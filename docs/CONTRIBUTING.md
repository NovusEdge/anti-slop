# Contributing

Thanks for helping. The plugin lints prose for a living, so it holds its own text to the same rules. Expect CI to check that.

## Layout

- `patterns.json`: the single source for banned words, phrases, and structural tells. Both linters read it. Edit here, nowhere else.
- `hooks/rules/`: the injected directives. `core.md` loads every session. `code.md`, `prose.md`, and `commit.md` are routed in by tool context.
- `hooks/inject.js`: the hook entry point: session injection, the context router, the mid-turn lint, and the Bash guard.
- `hooks/check.js`: slop detection over a transcript.
- `tools/lint.py`: the standalone linter and `--code` comment linter.
- `tools/ast_check.py`: structural checks that need a parse.
- `tests/corpus.json`: shared fixtures. Both linters run them, so a divergence between the two fails CI.

## Running the tests

```bash
node hooks/selftest.js
python3 tools/lint.py --selftest
python3 tools/ast_check.py --selftest
```

All three run in CI on every push. `ast_check.py` needs `tree-sitter` and `tree-sitter-language-pack` for non-Python files; without them it checks Python and names what it skipped.

## Adding a banned word or phrase

1. Add the pattern to the right set in `patterns.json`. A word goes in `banned_words`; a multi-word or regex pattern goes in `banned_phrases` or the matching set.
2. Add at least one case to `tests/corpus.json`: a `hit: true` example and, where the pattern risks a false positive, a `hit: false` control. Set `tools` to the linters the case applies to.
3. Run all three selftests. The hook and the Python linter must agree on every shared case.

A word that is also a real technical term goes in `ambiguous_words`. Those stay behind `--all` and never block a commit.

## Adding a rule file or a router target

`ruleTargetFor` in `hooks/inject.js` maps a tool call to one rule file. To add a target, add the file under `hooks/rules/`, extend the router, and add a case to the router block in `hooks/selftest.js`. Keep the rule file short; it competes for space at the top of the model's context.

## Style

Contributions follow the plugin's own rules. Write comments that carry a fact the code cannot show. Keep the commit body in Simplified Technical English: one fact per sentence, active voice, simple tenses. The commit-message hook lints it.

## Pull requests

Branch from `main`, keep the change focused, and make sure the three selftests pass locally. Describe what changed and why. Skip the preamble.
