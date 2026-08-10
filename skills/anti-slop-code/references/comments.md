# Comments

One test decides whether a comment stays: does it carry a fact the reader cannot
get from the code? Everything else is filler, whatever its length. A dense
four-line comment about a locking invariant is right. One line restating the
call below it is wrong.

## Paraphrase

The comment says in English what the next line says in code.

```python
# BAD
# increment the retry counter
retries += 1

# GOOD
retries += 1
```

```go
// BAD
// Stop the VM and wait for it to exit
vm.Stop()
vm.Wait()

// GOOD
// Stop() only signals; qemu unlinks the monitor socket during Wait().
vm.Stop()
vm.Wait()
```

The good version carries a fact about qemu that the reader cannot see from two
method names.

## Narration

A comment that announces what the function is about to do.

```js
// BAD
// This function handles the incoming request
function handleRequest(req) {

// GOOD
function handleRequest(req) {
```

The name already said it. When the name does not say it, fix the name.

## Step numbering

```python
# BAD
# Step 1: Validate the input
validate(payload)
# Step 2: Transform the payload
normalized = transform(payload)
# Step 3: Write to the database
db.write(normalized)

# GOOD
validate(payload)
normalized = transform(payload)
db.write(normalized)
```

Three sequential calls read as three sequential steps. The numbering adds a
layer of bookkeeping that goes stale the moment someone inserts a fourth call.

## The investigation

The story of how the answer was found belongs in the commit message.

```go
// BAD
// Originally we called Stop() here, but it turned out that Stop() only sends
// SIGTERM and does not wait for the process to exit, which we confirmed by
// running the test 20 times and seeing 3 failures. So now we call Wait().
// See the discussion above about why the first fix was wrong.
vm.Stop(); vm.Wait()

// GOOD
// Stop() only signals; qemu unlinks the monitor socket during Wait().
vm.Stop(); vm.Wait()
```

What was tried, what was verified, what an earlier version got wrong, what the
tool output said: all of it goes in the commit body.

## Comments addressed to a person

```ts
// BAD
// Updated this per your request to use the new API. Note that we now handle
// the null case as you pointed out.
const name = user?.name ?? "anon"

// GOOD
// Legacy rows predate the NOT NULL migration; name is null for ~4k of them.
const name = user?.name ?? "anon"
```

The next reader is a stranger. Write for them.

## Deferral and hedging

```python
# BAD
# for now, just retry three times. we can make this configurable later
# this should work for most cases
# TODO: handle the edge case properly

# GOOD
# ponytail: fixed at 3 retries; make it configurable if a caller needs it.
```

"For now", "temporary", "should work", "hopefully", "in a real implementation",
"you would want to" — each one describes the author's confidence rather than the
code. A deliberate shortcut gets a `ponytail:` marker naming the ceiling and the
upgrade path. Everything else gets deleted or fixed.

An honest `TODO` names who or what unblocks it. A bare `TODO: handle this` is a
note to nobody.

## Section banners

```python
# BAD
# ============================================
# HELPER FUNCTIONS
# ============================================

# GOOD
```

If a file needs banners to be navigable, split the file.

## Docstrings

An exported symbol in a language whose tooling consumes docstrings gets a real
doc: what it returns, what it raises, what it refuses to handle.

```python
# BAD
def parse_config(path: Path) -> Config:
    """
    Parse config.

    Args:
        path: The path to the config file.

    Returns:
        The parsed Config object.
    """

# GOOD
def parse_config(path: Path) -> Config:
    """Read a config file.

    Raises FileNotFoundError when path is missing. Unknown keys are ignored,
    which is how a v2 config stays readable by a v1 binary.
    """
```

The bad version restates the signature three times. The type annotations already
say `path` is a `Path` and the return is a `Config`.

A private helper with an obvious name needs no docstring at all.

## What earns its place

Each of these carries something the code cannot show.

```rust
// Lock order is always registry then vm, never the reverse: the reaper thread
// takes registry while holding no vm lock, so acquiring vm first here would
// deadlock it. Any new path that touches both must follow this order.
let reg = self.registry.lock();
let vm = reg.get(id)?.lock();
```

```sql
-- events is partitioned by day; unbounded scans here have OOM'd prod twice.
select ... where day >= current_date - 7
```

```js
// Safari fires this twice on the same gesture; the guard drops the second one.
if (seen.has(event.timeStamp)) return
```

A constraint from outside the file, a bug that already shipped, a limit with a
number. None of it is visible in the code below.

## Match the file

A file that comments sparsely gets sparse comments. Delete a stale comment
rather than appending a correction to it.

<!-- anti-slop: ignore-file (this file quotes the banned patterns) -->
