---
name: anti-slop-code
description: "Audit and trim code itself — narrator comments, defensive boilerplate, dead generality, tests that assert mocks, docstrings that restate the signature. Use for source files; use anti-slop for prose."
version: 0.1.0
---

# anti-slop-code

The prose rules in `anti-slop` cover text a developer reads. This covers the
code and the documentation around it.

Every rule here is a code-quality rule with a reason. None of them detects
authorship. Human code carries all of these patterns too, and a rule that fires
on "this looks generated" is a rule that fires on clean idiomatic code, on a
junior developer's first pass, and on anyone writing English as a second
language. Judge the artifact.

## When to Use

- Before you commit code you or a model just wrote
- Reviewing a large diff, especially one you did not type
- Writing a README, an API reference, a docstring, or a commit body
- Cleaning a file that reads padded and you cannot say why

## The Rules

### Comments

A comment earns its place by carrying a fact the reader cannot get from the
code. Delete every comment that fails that test.

See `references/comments.md`. The short version:

| Cut | Keep |
|---|---|
| Paraphrase of the line below | The constraint that forced the shape |
| `// Step 1:` `// Step 2:` narration | The invariant a reader would break |
| A docstring restating the signature | The failure this code already shipped |
| The story of how you found the answer | The lock order, the null-row count, the limit |
| Deferral text: "for now", "temporary" | A `ponytail:` marker naming the ceiling |
| Hedges: "should work", "hopefully" | A measured number |

### Structure

- Delete vacuous code: `if True`, `x == x`, `if flag == True`, an if/else
  returning `True`/`False` for a value the condition already holds, a branch
  with the same body on both sides, `except E as e: raise e`.
- Write the code the task needs. Extra statements around the same task are the
  most measurable tell in the literature, and they cost review time forever.
- Extract a function when logic repeats across files. Re-deriving near-identical
  logic in a nearby scope is the failure mode, and it reads as thoroughness.
- Delete a `try`/`except` around code that cannot throw. Name the exception you
  expect and let the rest crash.
- Delete a null check on a value that a type or a caller already guarantees.
- One variable per value. Two names holding the same thing is a rename left
  half-done.
- Collapse runs of blank lines inside a function body. One blank line separates
  two ideas; three separate nothing.

Architecture rules that earn their keep: dependencies point one way, IO sits at
the edges, errors get translated once at the layer that owns the driver, a
constructor does no work, an abstraction waits for its second implementation.

Over-abstraction (an interface with one implementation, a factory for one
product, config for a constant that never changes) belongs to the `ponytail`
skill, which already owns that ground. Use it rather than duplicating it here.
Those patterns are ordinary over-engineering and predate any model.

See `references/structure.md`.

### Imports and APIs

Resolve every import against the lockfile or the registry before you claim the
code runs. An invented package name is the one failure here with no judgment in
it: the package exists or it does not.

Same for a method on a library type. Read the signature, then call it.

### Tests

- **Write the test before the code.** A test written after the code passes because the code runs, bugs included. A test written first defines the behavior the code must satisfy. The order matters: test → red → code → green → refactor.
- **State the expected outcome from the requirement**, not from running the code. An assertion built by pasting output encodes today's behavior. A test that went green on the first run never proved anything.
- **A red test is a claim that the code is wrong.** Fix the code. Change the test only when you can name why the expectation was wrong, and put that reason in the commit body.
- **Never weaken an assertion to reach green.** Loosening `==` to `is not None`, widening a tolerance, skipping the case, deleting the case, or catching the exception the test exists to prove: each makes the suite green and the code no more correct.
- **Test behavior at boundaries, not every line.** A pure function with no branches needs one test. A function with three branches needs three. A getter needs zero. Coverage measures lines that ran, not bugs that would be caught; a 100% covered codebase with no boundary tests catches nothing.
- **Assert behaviour, not implementation.** A test that asserts which internal method was called in which order breaks on a refactor that changed nothing, and passes when the behaviour is wrong. Mock what hits the network, the clock, or the disk, and nothing else.
- **No tautologies.** `assert True`, `assert x == x`, an expected value produced by calling the code under test.
- **Cover the error path**, which is where the bugs are and where a single happy-path test stops.

See `references/tests.md`.

### Documentation

- A docstring on an exported symbol carries the contract: what it returns, what
  it raises, what it does not handle. A docstring that restates the signature in
  English carries nothing.
- A README says what the thing does, how to run it, and what breaks. A feature
  tour with a section per capability is marketing.
- A commit body says what changed and why. The investigation goes nowhere.
- A PR description says what the diff does. Claiming a change the diff does not
  contain is the expensive version of this mistake.
- No emoji section markers, no badge walls, no title case in headings, unless
  the repo already does it. Match the file you are in.

See `references/docs.md`.

## Checking

```bash
# comments and docstrings, extracted from source
python3 tools/lint.py --code src/

# structural checks that need a parse
python3 tools/ast_check.py src/
```

The linter reports what a regex can see. Everything above it needs a reader.

## Boundaries

**Will:**
- Delete comments that carry no fact
- Cut defensive code around paths that cannot fail
- Rewrite tests that assert implementation into tests that assert behaviour
- Strip feature-tour prose from a README

**Will not:**
- Claim a file was machine-written
- Remove a comment that records a constraint, a bug, or an external cause
- Remove error handling at a trust boundary, or around IO that genuinely fails
- Flatten a complex solution to a genuinely complex problem
- Impose its own house style on a repo that already has one

<!-- anti-slop: ignore-file (this file quotes the banned patterns) -->
