# Tests

A test states what the code must do. A suite that gets edited until it passes
states nothing, and it costs more than no suite: it reports green while the
behaviour is broken, and every reader trusts it.

## Write the expectation before the body

Name the outcome first, from the requirement. Then write the call that should
produce it.

```python
# BAD: run the code, paste what came out
def test_parse_duration():
    assert parse_duration("1h30m") == 5400.0   # copied from the REPL

# GOOD: state the number the requirement demands, then run it
def test_parse_duration_returns_seconds():
    assert parse_duration("1h30m") == 5400
```

The bad version passes on the day it is written and asserts nothing afterward.
It encodes whatever the function did, including the float where an int was
specified, including the bug.

When you cannot say what the answer should be without running the code, you do
not yet understand the requirement. Go find it. A test derived from observed
output is a snapshot of today's behaviour wearing a test's clothes.

Snapshot and approval tests are the exception, and they earn it by saying so in
the name. Review the snapshot on the first commit and on every change.

## A failing test is a claim about the code

The default reading of a red test: the code is wrong. Fix the code.

Change the test only when you can name why the expectation itself was wrong, and
write that reason in the commit body. "The test failed" is not a reason.

These edits turn a suite into decoration:

```python
# Weakening the assertion until it passes
assert result == 5400          →  assert result > 0
assert result == 5400          →  assert result is not None
assert body == expected        →  assert expected[:10] in body

# Widening a tolerance to swallow the drift
assert abs(x - 1.0) < 1e-9     →  assert abs(x - 1.0) < 0.5

# Retiring the case
def test_rejects_negative_ttl  →  @pytest.mark.skip
def test_rejects_negative_ttl  →  (deleted)

# Catching the failure the test exists to prove
with pytest.raises(ValueError) →  try: ...
                                  except ValueError: pass

# Rewriting the expectation to match the output
assert status == 200           →  assert status == 500
```

Each of these makes the suite green. None of them makes the code correct. When a
test is genuinely wrong, delete it and write the right one, with the reason in
the commit.

## Assert behaviour, not implementation

```python
# BAD: asserts which internal calls happened
def test_send_welcome_email():
    mailer = Mock()
    service = UserService(mailer)
    service.register("ana@example.com")
    mailer.connect.assert_called_once()
    mailer.send.assert_called_once_with(to="ana@example.com", template="welcome")
    mailer.close.assert_called_once()

# GOOD: asserts what the caller can observe
def test_register_sends_one_welcome_email():
    mailer = FakeMailer()
    service = UserService(mailer)
    service.register("ana@example.com")
    assert [m.to for m in mailer.sent] == ["ana@example.com"]
```

The first test breaks when someone reorders `connect` and `send`, which changes
nothing a user can see. It passes when `send` is called with an empty body.

Mock what hits the network, the clock, the filesystem, or a paid API. Mock
nothing else. A mock for a pure function is a way to test that you wrote the
call you wrote.

## Tautological and vacuous tests

These run, pass, and prove nothing.

```python
assert True
assert x == x
assert result == result
assert isinstance(cfg, Config)          # the constructor already guaranteed it
assert response is not None             # as the only assertion
mock.method()                           # calling the mock, then asserting it was called
assert mock.method.called

def test_add():
    assert add(2, 2) == add(2, 2)       # both sides run the same code
```

A test whose expected value comes from calling the code under test has no
expectation in it. Write the literal.

```python
# BAD
assert normalize(path) == normalize(path.replace("//", "/"))

# GOOD
assert normalize("/a//b/") == "/a/b"
```

## Cover the boundary and the failure

A single happy-path test per function is where most generated suites stop. The
cases that find bugs sit at the edges.

For each function ask: what does it do with an empty input, with one element,
with the maximum, with a value one past the maximum, with the wrong type, with a
duplicate, with a concurrent caller? Then write the ones that can actually
happen.

The error path needs a test more than the happy path does, because nobody
exercises it by hand.

```python
def test_rejects_ttl_above_the_cap():
    with pytest.raises(ValueError, match="ttl exceeds 86400"):
        set_ttl(86401)
```

Assert the error type and something about the message. A bare `pytest.raises
(Exception)` passes on a typo in the function body.

## One behaviour per test

The name says the condition and the outcome. `test_user` says nothing.
`test_register_rejects_a_duplicate_email` says what broke when it goes red.

A test with five unrelated assertions reports the first failure and hides the
rest.

## Coverage is not the target

Line coverage counts lines that ran. It cannot tell whether an assertion would
have noticed a wrong answer.

When coverage is high and the suite still feels thin, run a mutation test
(`mutmut`, `Stryker`, `PIT`). It changes an operator or a constant and reruns
the suite. Every mutant that survives is a change to the code that no test
objected to. A high line coverage with a low kill rate means the assertions are
decorative.

## Deleting a test

Deleting a test is a decision, and it goes in the commit body with the reason.
A test deleted in the same commit that changed the code it guarded is the
signature of a suite bent to fit.

<!-- anti-slop: ignore-file (this file quotes the banned patterns) -->
