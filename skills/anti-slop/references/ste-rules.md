# STE Rules

Simplified Technical English rules adapted from ASD-STE100 for code comments, docstrings, commit messages, and technical documentation.

## The 12 Rules

### 1. One fact per sentence

No joining two claims with "and" or a comma splice. A second fact is a second sentence.

**Before:** "The function parses the config and validates the schema and then initializes the connection pool."

**After:** "The function parses the config. It validates the schema. Then it initializes the connection pool."

### 2. Short sentences

Aim under ~20 words. If it runs long, split it or cut a clause. Never drop the subject, verb, or article just to hit the count.

**Before:** "This handler processes incoming webhook events from the payment provider and updates the local order status accordingly while also triggering any configured notification callbacks."

**After:** "This handler processes incoming webhook events from the payment provider. It updates the local order status. It triggers any configured notification callbacks."

### 3. Simple tenses

Simple present for what a thing does ("returns", "holds", "refuses"). Simple past for what happened. No perfect or compound tenses.

| Banned | Use instead |
|---|---|
| has been closed | closed, is closed |
| will have run | will run, runs |
| was being rebuilt | rebuilt, was rebuilt |
| have been receiving | received |

### 4. Active voice

Name the actor. Passive only when the actor is genuinely unknown.

**Before:** "The socket is unlinked by the cleanup handler."

**After:** "The cleanup handler unlinks the socket."

**Before:** "The file was deleted." (actor unknown — passive OK)

### 5. No -ing verb forms as sentence point

Not "Handling the case where...", "Using X to...". Say the plain verb.

**Before:** "Handling the timeout by retrying three times."

**After:** "Handles the timeout by retrying three times." or "The handler retries three times on timeout."

### 6. One word, one meaning

Don't let "handle" / "process" / "manage" stand for three different behaviors in one file. Name the actual operation. Don't swap synonyms for variety.

**Before:** "The service handles requests, processes events, and manages connections."

**After:** "The service routes requests, dispatches events, and pools connections."

### 7. Articles before countable nouns

"the lock", "a socket", not bare "lock ensures...". Dropped articles are the main source of terse-writing ambiguity.

**Before:** "Lock ensures thread safety."

**After:** "The lock ensures thread safety."

### 8. Noun stacks ≤3 words

"vm registry lock" is fine. "vm registry lock timeout retry config" is not.

**Before:** "user session authentication token refresh interval config"

**After:** "the config for the token refresh interval" or "userSessionAuth.tokenRefreshInterval"

### 9. State the constraint or consequence

The code already shows the call. The comment gives the reason, the invariant, or the failure it prevents.

**Before:** "// Call Wait() after Stop()"

**After:** "// Stop() only signals; qemu unlinks the monitor socket during Wait()."

### 10. Concrete over abstract

A name, a type, a number, a limit — not "system", "logic", "the process", "various parts of the code".

**Before:** "The system handles various edge cases in the logic."

**After:** "parseConfig() returns nil for empty input and missing required fields."

### 11. Edge case is its own sentence

Put the failure or exception on its own line, not buried in a subordinate clause.

**Before:** "The function returns the parsed config, or nil if the file doesn't exist or contains invalid JSON, which can happen when the user manually edits it."

**After:** "The function returns the parsed config. It returns nil if the file is missing. It returns nil if the JSON is invalid."

### 12. One topic per comment block

Two unrelated facts are two comments.

**Before:**
```go
// This validates the schema and also note that we're using
// a connection pool here because the old approach had issues
// with connection exhaustion under load.
```

**After:**
```go
// Validates against the v2 schema.

// Connection pool prevents exhaustion under load.
```

## Before / After Examples

**Before:** "Since Stop() only sends SIGTERM and doesn't actually wait around for the process to fully exit, which we found out through testing, we also call Wait() afterward to make sure it's really done."

**After:** "Stop() only signals; qemu unlinks the monitor socket during Wait()."

---

**Before:** "This function is basically responsible for handling the case where a user record might not have a name set, which can happen for older accounts, so we're using a fallback value here just in case."

**After:** "Legacy rows predate the NOT NULL migration; name is null for ~4k of them."

---

**Before:** "We're leveraging a retry mechanism here since sometimes the API call to the provisioning service will fail transiently, especially under load, and we don't want that to fail the whole operation."

**After:** "The provisioning API fails transiently under load. Retry keeps one transient failure from aborting the operation."

<!-- anti-slop: ignore-file (this file quotes the banned patterns) -->
