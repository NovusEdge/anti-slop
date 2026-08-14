# anti-slop

Steer Claude Code toward clear, terse technical prose. A directive injected at the top of context shapes the model before it writes, and the linters catch what leaks through.

## Install

Inside Claude Code:

```
/plugin marketplace add NovusEdge/anti-slop
/plugin install anti-slop@anti-slop
```

From a shell: `curl -fsSL https://raw.githubusercontent.com/NovusEdge/anti-slop/main/install.sh | bash`, or `./install.sh --local` from a checkout. Restart Claude Code after.

## What it enforces

A directive injected at `SessionStart` carries the rules. A router adds `code`, `prose`, or `commit` rules from the tool context. See [docs/hooks.md](docs/hooks.md).

1. **Surgical brevity** — Lead with the outcome. No preamble, no closing summary of work the diff already shows.
2. **One adjective** — "A clean solution", never "a clean, simple, elegant solution".
3. **Banned vocabulary** — `delve`, `leverage`, `crucial`, `load-bearing`, and about forty more, plus their inflections.
4. **No contrast constructions** — `it's not X, it's Y`, rhetorical questions, closing aphorisms.
5. **No sycophancy** — No flattery, no apology inflation. A correction is a claim: verify it, then state the fact alone.
6. **No servile closer** — No `happy to`, `hope this helps`. Name what is available and stop.
7. **STE grammar** — One fact per sentence, active voice, simple tenses. Based on ASD-STE100.

No hard word cap. Anthropic capped Claude Code responses at 100 words in April 2026 and reverted it four days later after a 3% eval drop, so the length check reports and never blocks.

## Usage

```
/anti-slop:anti-slop            audit prose: comments, docstrings, commits, PR bodies, docs
/anti-slop:anti-slop-code       audit and trim code: narrator comments, dead generality, mock tests
```

`ANTI_SLOP_REMIND_EVERY` sets the reminder cadence (default 9). `ANTI_SLOP_TOOL_GUARD` sets the Bash-guard posture (`ask`, `deny`, `off`).

## Docs

- [How the hooks and the Bash guard work](docs/hooks.md)
- [Running the linters and pre-commit](docs/linting.md)
- [Contributing](docs/CONTRIBUTING.md)
- [Changelog](docs/CHANGELOG.md)

## Quick reference

| Don't | Do |
|---|---|
| `Let me walk you through what I did.` | (lead with the outcome, cut the preamble) |
| `A clean, simple, elegant solution.` | `A clean solution.` |
| `leverage the cache` | `use the cache` |
| `It's not about X, it's about Y` | State Y directly |
| `You're absolutely right, I'll fix it` | `The lock order is reversed at vm.go:41.` |

If you wouldn't say it to a colleague in a hallway, rewrite it.

## License

MIT. Use it, fork it, ship it. The one unlicensed act is opening a PR that starts with "You're absolutely right."
