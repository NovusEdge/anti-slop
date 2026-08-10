# Documentation

## Docstrings

An exported symbol carries a contract: what it returns, what it raises, what it
refuses to handle. A docstring that restates the signature carries nothing.

```python
# BAD
def retry(fn: Callable[[], T], attempts: int = 3) -> T:
    """
    Retry a function.

    Args:
        fn: The function to retry.
        attempts: The number of attempts. Defaults to 3.

    Returns:
        The result of the function.
    """

# GOOD
def retry(fn: Callable[[], T], attempts: int = 3) -> T:
    """Call fn until it returns without raising.

    Re-raises the last exception when every attempt fails. Sleeps 100ms between
    attempts, so a caller on a request path should keep attempts low.
    """
```

The types already say what `fn` and `attempts` are. The good version says what
happens when everything fails and what it costs, which the reader cannot see.

A private helper with a clear name needs no docstring.

## README

Say what the thing does, how to run it, and what breaks. Stop.

```markdown
<!-- BAD -->
# TaskFlow

TaskFlow is a modern, lightweight task queue built for today's demanding
workloads.

## ✨ Features

- 🚀 **Blazing fast** — Process thousands of tasks per second
- 🔒 **Secure** — Built with security in mind
- 🎯 **Simple** — Get started in minutes
- 📦 **Zero config** — Works out of the box

## Why TaskFlow?

In today's fast-paced development landscape, teams need a task queue that
scales with them...

<!-- GOOD -->
# TaskFlow

A task queue backed by Postgres. One table, no broker.

## Install

    pip install taskflow

## Use

    from taskflow import queue

    @queue.task
    def resize(image_id: int): ...

    resize.delay(42)

Workers poll with `SELECT ... FOR UPDATE SKIP LOCKED`, so throughput caps at
roughly 2k tasks/second on one Postgres instance. Above that, use a broker.
```

The feature grid says nothing a reader can act on. "Blazing fast" with no number
is a claim nobody can check. The good version gives the mechanism, the number,
and the point where the tool stops being the right choice.

A section per capability is a product page. Documentation answers: how do I do
the thing, and what will bite me.

## Formatting

- No emoji as section markers, no badge walls, no title case in headings, unless
  the repo already does it. Match the file you are in.
- No bold label on every bullet. When each bullet opens with a bolded phrase,
  the bolding marks nothing.
- No three-item list where two items are real.

## Commit messages

The subject says what changed. The body says why, and what a reader needs to
know that the diff does not show.

```
BAD:
Fix bug in retry logic

I spent a while debugging this. At first I thought the problem was in the
connection pool, so I added logging there, but that turned out to be a dead
end. Then I noticed that the retry counter was being reset. I tried moving
the reset into the loop but that broke the tests, so instead I moved the
initialization outside the function. Now all 47 tests pass.

GOOD:
Reset the retry counter once per call, not per attempt

The counter lived inside the attempt loop, so a failing call retried forever.
The bug needed three consecutive failures to show, which is why the existing
tests missed it.
```

The investigation goes nowhere. What was tried, what turned out to be a dead
end, how many tests pass now: none of it helps the reader in six months.

State the change in the imperative. Explain the cause, not the search.

## Pull request descriptions

Say what the diff does and what a reviewer should look at hardest.

Never describe a change the diff does not contain. A description claiming work
that is not there wastes the reviewer's first pass and costs the trust that
makes later reviews fast.

Do not restate the diff line by line. The reviewer can read it. Give them the
part that is hard to see: the constraint you worked around, the case you decided
not to handle, the file where the real change lives.

## Changelogs

An entry says what changed for the user of the thing, in their vocabulary.

```
BAD:  Refactored the TaskRunner class to improve maintainability
GOOD: Tasks now retry three times before failing. Previously they failed on the
      first error.

BAD:  Various bug fixes and improvements
GOOD: Fixed a crash when a task argument contained a NUL byte.
```

## Generated documentation

Documentation generated from types stays generated. Do not hand-edit the output,
and do not paste a copy of it into the README where it will drift.

<!-- anti-slop: ignore-file (this file quotes the banned patterns) -->
