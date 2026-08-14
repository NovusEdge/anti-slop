# Changelog

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0]

### Added

- Surgical-brevity and one-adjective rules at the top of `rules/core.md`, so the directive steers output before the model generates.
- A deterministic context router in `inject.js`. It injects one more rule file per tool call, once per session: `code.md` on a source edit, `prose.md` on a docs edit, `commit.md` on `git commit`.
- A `PreToolUse` guard on Bash that flags a file op belonging to Write/Edit/Read (a redirect into a source file, `sed -i`, `cat` of a doc) and asks before it runs. `ANTI_SLOP_TOOL_GUARD` sets the posture: `ask` (default), `deny`, or `off`.
- An anti-over-engineering block in `code.md`, following Anthropic's Opus migration guidance. It pairs DRY with the rule of three and weighs completeness against restraint.

### Changed

- Split the single `rules.md` into `rules/{core,code,prose,commit}.md`.
- Reminder cadence default moved to every 9 prompts. `ANTI_SLOP_REMIND_EVERY` still overrides it.
- Length nudge lowered from 400 to 250 words. It stays soft and never blocks.
- Sharpened the two skill descriptions so invocation splits prose from code.
- Trimmed the README.

## [0.2.0]

### Added

- A code and documentation mode (`anti-slop-code`, `lint.py --code`, `ast_check.py`).
- Enforcement on `PostToolUse` next to the tool result.

## [0.1.0]

### Added

- The prose linter, the banned-vocabulary and sycophancy layers, and the session-start directive.

[0.3.0]: https://github.com/NovusEdge/anti-slop/releases/tag/v0.3.0
[0.2.0]: https://github.com/NovusEdge/anti-slop/releases/tag/v0.2.0
[0.1.0]: https://github.com/NovusEdge/anti-slop/releases/tag/v0.1.0
