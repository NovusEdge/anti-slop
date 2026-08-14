# anti-slop

Claude Code models ramble. They open with "You're absolutely right", hand you a summary of the diff you just watched them write, and reach for `leverage` when they mean `use`. anti-slop leans on them to stop.

The main move runs before the model writes a word. Every session, it drops a short writing directive into the top of the context window, where the model pays the most attention. A pair of linters and a few hooks clean up whatever slips through.

## Install

Run this inside Claude Code:

```
/plugin marketplace add NovusEdge/anti-slop
/plugin install anti-slop@anti-slop
```

From a shell: `curl -fsSL https://raw.githubusercontent.com/NovusEdge/anti-slop/main/install.sh | bash`, or `./install.sh --local` from a checkout. Restart Claude Code when it finishes.

## What it tells the model

The core directive loads at `SessionStart`. A router adds `code`, `prose`, or `commit` rules based on what the model is touching, which [docs/hooks.md](docs/hooks.md) walks through. What it asks for:

1. **Say the outcome first.** No preamble, and no summary of work your diff already shows.
2. **Use one adjective.** "A clean solution" beats "a clean, simple, elegant solution".
3. **Drop the buzzwords.** `delve`, `leverage`, `crucial`, `load-bearing`, and forty-odd more, inflections included.
4. **Skip the contrast setup.** No "it's not X, it's Y", no rhetorical questions, no closing aphorism.
5. **Cut the flattery.** No "great question", no reflexive apology. When you push back, it checks the claim before it agrees with you.
6. **Stop at the end.** No "happy to help", no "hope this helps". It names what is left and quits.
7. **Write like STE.** One fact per sentence, active voice, plain tenses.

There is no hard word limit. Anthropic tried a 100-word cap on Claude Code in April 2026. They pulled it four days later when it cost 3% on evals. So the length check nudges you and never blocks.

## Usage

Point the skills at your work:

```
/anti-slop:anti-slop            audit prose: comments, docstrings, commits, PR bodies, docs
/anti-slop:anti-slop-code       audit and trim code: narrator comments, dead generality, mock tests
```

`ANTI_SLOP_REMIND_EVERY` sets how often the reminder fires (default 9). `ANTI_SLOP_TOOL_GUARD` sets the Bash-guard posture: `ask`, `deny`, or `off`.

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
