# Before / After Examples

Real patterns, real fixes.

## Banned Vocabulary

| Before | After | Why |
|--------|-------|-----|
| "We leverage Redis for caching" | "We use Redis for caching" | leverage → use |
| "This is a robust solution" | "This handles X, Y, Z edge cases" | Say what it actually handles |
| "The function delves into the data" | "The function reads the data" | delve → read |
| "This is load-bearing code" | "The retry loop reads this config on every attempt" | Say what depends on it |
| "A seamless integration" | "Syncs automatically every 5 minutes" | Say what it does |

## Contrast Construction

| Before | After |
|--------|-------|
| "It's not about speed, it's about correctness" | "Correctness matters more here" |
| "This isn't just a refactor, it's a redesign" | "This redesign changes X, Y, Z" |
| "Less code, more clarity" | "Shorter and clearer" |
| "The real question isn't whether we should do it, it's how" | "The question is how" |

## LinkedIn Cadence

**Before:**
```
We shipped the new payment flow.

It handles 10x the volume.

That's the power of good architecture.
```

**After:**
```
The new payment flow handles 10x the volume.
```

---

**Before:**
```
What makes a great engineer? It's not about knowing everything.
It's about knowing how to learn.
```

**After:**
```
Great engineers learn fast.
```

## STE Grammar

### Passive → Active

| Before | After |
|--------|-------|
| "The file is deleted by the handler" | "The handler deletes the file" |
| "Errors are logged to stderr" | "The logger writes errors to stderr" |
| "The config was parsed successfully" | "parseConfig() succeeded" |

### Complex → Simple Tense

| Before | After |
|--------|-------|
| "The service has been running for 3 days" | "The service started 3 days ago" |
| "We have received your request" | "We received your request" |
| "The job will have completed by midnight" | "The job finishes by midnight" |

### -ing Openers

| Before | After |
|--------|-------|
| "Handling the timeout gracefully..." | "Handles the timeout gracefully" |
| "Using Redis as a cache..." | "Uses Redis as a cache" |
| "Leveraging the existing infrastructure..." | "Uses the existing infrastructure" |

## Dense → Clear

**Before:**
```
Since Stop() only sends SIGTERM and doesn't actually wait around for the
process to fully exit, which we found out through testing, we also call
Wait() afterward to make sure it's really done.
```

**After:**
```
Stop() only signals; qemu unlinks the monitor socket during Wait().
```

---

**Before:**
```
This function is basically responsible for handling the case where a user
record might not have a name set, which can happen for older accounts, so
we're using a fallback value here just in case.
```

**After:**
```
Legacy rows predate the NOT NULL migration; name is null for ~4k of them.
```

---

**Before:**
```
We're leveraging a retry mechanism here since sometimes the API call to the
provisioning service will fail transiently, especially under load, and we
don't want that to fail the whole operation.
```

**After:**
```
The provisioning API fails transiently under load. Retry keeps one
transient failure from aborting the operation.
```

## Meta-Commentary

| Before | After |
|--------|-------|
| "To be clear, the function returns null" | "The function returns null" |
| "Quick note: this is deprecated" | "Deprecated" |
| "I don't want this read as criticism, but..." | [just say the thing] |
| "Before I answer, let me explain..." | [just answer] |

## The Hallway Test

Read it aloud. Would you say it to a colleague? If not, rewrite.

"We're leveraging our robust infrastructure to facilitate seamless integration"
→ "We use our servers to sync data"

<!-- anti-slop: ignore-file (this file quotes the banned patterns) -->
