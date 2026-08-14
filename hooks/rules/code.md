ANTI-SLOP CODE DIRECTIVE. You are editing source. Keep the change minimal and the comments factual.

Do not over-engineer.
- Make only the change requested or clearly needed. A bug fix leaves the surrounding code alone. A small feature stays at the scope asked for.
- Edit an existing file before you create a new one.
- Do not add an abstraction (interface, wrapper, factory, helper) for one call site. Inline first. Abstract at the third repeat.
- Do not add error handling or validation for cases that cannot happen. Validate at system boundaries: user input and external APIs.
- YAGNI bans speculative features. It never licenses skipping the tests, the validation at a trust boundary, or the refactoring.

A comment earns its place by carrying a fact the code cannot show: why a branch exists, what breaks if an order changes, a constraint from outside this file.
- No narrator comments. Delete "this function handles the request" and any comment that paraphrases the line below it.
- No step numbering in comments ("Step 1:", "First,", "Next,"). The code is the steps.
- No deferral prose ("for now", "in a real implementation", "we could add this later"). Write the code, or a TODO with an owner.
- No hedging ("this should work", "hopefully", "in theory").
- No investigation narrative ("originally we tried", "as you requested", "note that we now"). That belongs in the commit message.
- A docstring states what the caller cannot infer from the signature. It does not repeat the parameter list.
- No defensive wrapper around code that cannot throw. No catch that swallows the error.
- Tests assert behaviour, not mocks. No "assert True", no asserting a value against itself, no "assert_called" as the only check.

Comments follow the core rules too: STE grammar, active voice, no banned vocabulary.

<!-- anti-slop: ignore-file (this file quotes the banned patterns) -->
