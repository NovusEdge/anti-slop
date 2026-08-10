# Structure

## Vacuous code

Code that runs, costs a line, and decides nothing.

```python
# Conditions that are already known
if True:
if x == x:
if len(items) >= 0:
while True: break

# Comparing a boolean to a boolean
if is_ready == True:            →  if is_ready:
if is_ready is not False:       →  if is_ready:
if not (a != b):                →  if a == b:

# Returning a boolean the branch already computed
if user.is_admin:               →  return user.is_admin
    return True
else:
    return False

# Assigning a value to itself, or rebinding with no change
x = x
config = config

# A branch with the same body on both sides
if fast_path:
    return compute(n)
else:
    return compute(n)

# Catching an exception to re-raise it unchanged
try:
    run()
except Exception as e:
    raise e
```

Each of these reads as thoroughness and carries none. Delete the wrapper and
keep the expression.

## Defensive code around paths that cannot fail

```python
# BAD
def area(w: float, h: float) -> float:
    try:
        if w is None or h is None:
            return 0.0
        return w * h
    except Exception:
        return 0.0

# GOOD
def area(w: float, h: float) -> float:
    return w * h
```

The types say `float`. A caller passing `None` has a bug, and the wrapper hides
it behind a `0.0` that flows downstream and gets found three layers away.

Catch the exception you expect, from the call that raises it:

```python
# BAD
try:
    data = json.loads(body)
    user = db.get(data["id"])
    send(user.email)
except Exception:
    pass

# GOOD
try:
    data = json.loads(body)
except json.JSONDecodeError:
    return Response(400, "malformed body")
```

`except Exception: pass` around four statements swallows the typo in the third
one. A silent handler is worse than a crash, because a crash has a stack trace.

Validation at a trust boundary stays. Input from a user, a network, or a file
gets checked. Input from the function next door does not.

## Say it once

Repeating near-identical logic in a nearby scope is the common failure, and it
reads as completeness.

```python
# BAD
def load_user_config(path):
    if not path.exists():
        raise ConfigError(f"missing: {path}")
    text = path.read_text()
    if not text.strip():
        raise ConfigError(f"empty: {path}")
    return parse(text)

def load_site_config(path):
    if not path.exists():
        raise ConfigError(f"missing: {path}")
    text = path.read_text()
    if not text.strip():
        raise ConfigError(f"empty: {path}")
    return parse(text)

# GOOD
def load_config(path):
    if not path.exists():
        raise ConfigError(f"missing: {path}")
    text = path.read_text()
    if not text.strip():
        raise ConfigError(f"empty: {path}")
    return parse(text)
```

Three copies is the threshold where the cost of a rename exceeds the cost of the
extraction. Two identical blocks that will diverge next week stay separate; say
so in a comment when it is not obvious.

## One name per value

```python
# BAD
result = compute(n)
value = result
output = value
return output

# GOOD
return compute(n)
```

Two variables holding the same thing under different names is a rename left
half-done. The reader has to prove they are equal before touching either.

## Dead generality

```python
# BAD
def render(template, data, *, strict=False, encoding="utf-8", hooks=None):
    # strict, encoding and hooks are never passed by any caller

# GOOD
def render(template, data):
```

An unused parameter, an unreachable branch, an exported symbol nobody imports:
delete it. Git remembers. Add the parameter back on the day a caller needs it,
when you will know what it should mean.

Over-abstraction — an interface with one implementation, a factory for one
product, a config value that never changes — belongs to the `ponytail` skill.
Use it. Those are ordinary over-engineering and long predate any model.

## Whitespace

```python
# BAD
def handle(req):

    user = auth(req)


    if not user:

        return deny()


    return serve(user)

# GOOD
def handle(req):
    user = auth(req)
    if not user:
        return deny()
    return serve(user)
```

One blank line separates two ideas inside a function. Runs of two and three
separate nothing and push the body off the screen.

## Size

Write the code the task needs. Extra statements around the same task cost review
attention on every future read, and they are the most measurable difference
between padded code and tight code.

A function that needs a comment to explain its second half usually wants to be
two functions. A function of six lines with a clear name rarely does.

## Architecture

Rules with teeth, applied when the code already asks for them.

- **Dependencies point one way.** Domain logic does not import the web
  framework, the ORM, or the CLI parser. When it does, the logic cannot be
  tested without booting all of it.
- **IO at the edges.** A function that computes and also writes to the database
  needs a database to test. Split the decision from the effect: compute a
  result, return it, let the caller persist it.
- **Errors cross boundaries once.** Translate a driver exception into a domain
  error at the layer that owns the driver. Do not let `psycopg2.IntegrityError`
  reach an HTTP handler.
- **No work in a constructor.** Building an object should not open a socket. The
  caller cannot construct it in a test without the socket.
- **Name the seam before you write the interface.** An abstraction is worth its
  cost when a second implementation exists or a test needs a fake. Write it
  then, when you know what varies.
- **State the invariant where it is enforced.** When two locks have an order,
  when a field is only valid after `init()`, when a cache may be stale: the
  comment goes at the place that would break.

A pattern applied because it is a pattern costs more than the problem it was
meant to solve. Reach for the plainest structure that holds, and let the second
requirement tell you where the seam goes.

<!-- anti-slop: ignore-file (this file quotes the banned patterns) -->
