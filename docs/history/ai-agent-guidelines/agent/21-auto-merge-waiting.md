# Auto-Merge Timing Constants

**Status:** Single source of truth for auto-merge timing.
**Load:** When using auto-merge workflow.

---

## The One Constant

```
AUTO_MERGE_MAX_WAIT_SECONDS = 600
```

**Meaning:** Maximum time to wait for CI checks before timing out.

**Rationale:**

- 10 minutes is enough for most CI pipelines
- Longer waits risk context loss in constrained agents
- Provides predictable timeout behavior across implementations

---

## Usage

### In Scripts

```bash
# Bash
AUTO_MERGE_MAX_WAIT_SECONDS=600
```

```python
# Python
AUTO_MERGE_MAX_WAIT_SECONDS = 600
```

```perl
# Perl
my $AUTO_MERGE_MAX_WAIT_SECONDS = 600;
```

```powershell
# PowerShell
$AUTO_MERGE_MAX_WAIT_SECONDS = 600
```

### Polling Interval (Recommended)

```
POLL_INTERVAL_SECONDS = 10
```

**Meaning:** How often to check CI status while waiting.

**Calculation:**

- Total polls = AUTO_MERGE_MAX_WAIT_SECONDS / POLL_INTERVAL_SECONDS
- Total polls = 600 / 10 = 60 checks maximum

---

## Timeout Behavior

**When timeout occurs:**

1. Log the timeout with timestamp
2. Preserve PR state (do NOT close or abandon)
3. Update journal with timeout details
4. Exit cleanly with appropriate exit code
5. Leave PR ready for human review

**What NOT to do on timeout:**

- Don't disable auto-merge
- Don't close the PR
- Don't retry indefinitely
- Don't modify PR labels/status

---

## Why This Constant Exists

**Problem:** Without a single constant, implementations drift:

- Bash uses 300 seconds
- Python uses 900 seconds
- PowerShell uses 450 seconds
- Agents get confused by inconsistent behavior

**Solution:** One constant, defined here, referenced everywhere.

**Enforcement:**

- All implementations MUST use this value
- No hard-coded timeouts elsewhere
- Conformance tests validate timeout behavior

---

## Adjusting the Constant

**When to consider changing:**

- CI pipelines consistently take > 9 minutes
- Constrained agents need shorter context windows
- Project-specific requirements differ

**How to change:**

1. Update this file ONLY
2. Update all implementations to read from this value
3. Update tests to use this value
4. Document the change in journal
5. Verify all implementations comply

**Do NOT:**

- Hard-code different values per implementation
- Change the value without updating all implementations
- Make the value dynamic or environment-dependent

---

## Related Constants

### `POLL_INTERVAL_SECONDS = 10`

How often to check CI status while waiting.

### `INITIAL_DELAY_SECONDS = 5`

Time to wait before first CI status check (allows GitHub API to update).

### `MAX_RETRIES = 3`

Maximum API request retries on transient failures (network errors, rate limits).

---

**Version:** 1.0
**Last Updated:** 2025-12-26
**Refs:** RFC v0.1.0 section 5.4
