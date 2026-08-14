# Linting

The injected directive steers the model before it writes. The linters are the backstop, and they also run standalone in CI and pre-commit.

## Prose

```bash
python tools/lint.py README.md          # check a file
python tools/lint.py --check README.md   # exit 1 on violations, for CI
python tools/lint.py --all README.md     # add the ambiguous words (robust, harness, ...)
python tools/lint.py --json README.md    # JSON output
echo "We leverage seamless infra" | python tools/lint.py
```

`ambiguous_words` stay behind `--all`. They are real technical words, and a commit gate that fails on `robust` gets disabled within a week.

## Code and documentation

`anti-slop-code` covers source and the documentation around it: comments that restate the line below, defensive wrappers around code that cannot throw, tests that assert mocks, docstrings that repeat the signature. The injected `code.md` also steers the size of the change, following Anthropic's own Opus migration guidance: fit the change to the goal, edit before creating a file, and abstract at the third call site. It weighs completeness against restraint, so it flags a cut corner as readily as an over-build.

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

## Pre-commit hook

```yaml
- repo: https://github.com/NovusEdge/curt
  rev: main
  hooks:
    - id: curt            # markdown files
    - id: curt-commit-msg # the commit message
      stages: [commit-msg]
```

The commit-message hook needs `pre-commit install --hook-type commit-msg`. It skips `#` lines, so the diff that `git commit -v` appends stays out of the lint.

<!-- anti-slop: ignore-file (this file quotes the banned patterns) -->
