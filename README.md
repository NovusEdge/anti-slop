# curt

Curt makes Claude Code stop writing like a chatbot. No "you're absolutely right", no recap of the diff you just read, no `leverage` where `use` works.

The rules load before the model writes. A linter catches the rest.

## Install

Inside Claude Code:

```
/plugin marketplace add NovusEdge/curt
/plugin install curt@curt
```

From a shell:

```shell
curl -fsSL https://raw.githubusercontent.com/NovusEdge/curt/main/install.sh | bash

# or, from a local checkout:
./install.sh --local
```

Restart Claude Code after.

## Rules

Injected at session start. A router adds code, prose, or commit rules from context ([docs/hooks.md](docs/hooks.md)).

- Outcome first. No preamble, no summary of the diff.
- One adjective per noun.
- No filler vocabulary: `delve`, `leverage`, `crucial`, `load-bearing`, ~40 more.
- No "it's not X, it's Y", no rhetorical questions.
- No flattery, no reflexive apology.
- No "happy to help" sign-off.
- STE grammar: one fact per sentence, active voice.

No hard word cap. Anthropic tried one (100 words) in April 2026 and pulled it four days later after a 3% eval drop.

## Usage

```
/curt:anti-slop         prose: comments, docstrings, commits, PRs, docs
/curt:anti-slop-code    code: narrator comments, dead generality, mock tests
```

Env: `ANTI_SLOP_REMIND_EVERY` (reminder cadence, default 9), `ANTI_SLOP_TOOL_GUARD` (`ask`, `deny`, `off`).

## Docs

- [Hooks and the Bash guard](docs/hooks.md)
- [Linters and pre-commit](docs/linting.md)
- [Contributing](docs/CONTRIBUTING.md)
- [Changelog](docs/CHANGELOG.md)

## License

MIT.
