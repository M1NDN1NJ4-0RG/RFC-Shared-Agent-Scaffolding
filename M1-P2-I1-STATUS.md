# M1-P2-I1 Status: Python 3 Bundle Alignment to M0 Contract

**Status:** Partially Complete (safe_run.py ✅, preflight ⚠️)  
**Date:** 2025-12-26  
**Epic:** Issue #3  
**Refs:** #3

---

## Summary

M1-P2-I1 aims to align Python 3 implementation and tests with the finalized M0 contract decisions.

**Completed:**
- ✅ `safe_run.py` fully aligned with M0-P1-I1 and M0-P1-I2
- ✅ All 5 safe_run tests pass
- ✅ `preflight_automerge_ruleset.py` auth header updated to M0-P2-I1

**Blocked:**
- ⚠️ Preflight tests have implementation/test drift
- ⚠️ Tests expect functions that don't exist in current implementation
- ⚠️ Requires human decision on resolution strategy

---

## Changes Made

### 1. safe_run.py — M0-P1-I1 (Split stdout/stderr) ✅

**Before:**
```python
# Line 124
proc = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
# Combined output
```

**After:**
```python
proc = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
# Split streams, read concurrently with threading
# Format with === STDOUT === and === STDERR === markers
```

**Test validation:** Lines 81-84 of `test_safe_run.py` assert markers present ✅

---

### 2. safe_run.py — M0-P1-I2 (Log naming) ✅

**Before:**
```python
# Line 190
out_path = os.path.join(log_dir, f"{ts}-{slug}-{suffix}.txt")
# Format: 20251226-025959-command-fail.txt
```

**After:**
```python
out_path = os.path.join(log_dir, f"{ts}-pid{pid}-{status}.log")
# Format: 20251226T025959Z-pid1234-FAIL.log
```

**Changes:**
- Timestamp: ISO 8601 format (`YYYYMMDDTHHMMSSZ`) in UTC
- Added PID for process correlation
- Status: `FAIL`, `ABORTED`, `ERROR` (uppercase)
- Extension: `.log` (not `.txt`)
- Removed: slug (command name sanitization)

**M0-P1-I2 Compliance:** ✅ Matches `{ISO8601_TIMESTAMP}-pid{PID}-{STATUS}.log`

---

### 3. preflight_automerge_ruleset.py — M0-P2-I1 (Bearer token) ⚠️

**Before:**
```python
# Line 55
req.add_header("Authorization", f"token {token}")
```

**After:**
```python
# Line 56
req.add_header("Authorization", f"Bearer {token}")
```

**M0-P2-I1 Compliance:** ✅ Uses Bearer format

**Problem:** Tests fail because they expect different implementation structure

---

## Test Results

### safe_run tests: ✅ PASS (5/5)

```bash
$ python3 -m unittest tests.test_safe_run -v

test_custom_log_dir_env ... ok
test_failure_creates_log_and_preserves_exit_code ... ok
test_sigint_creates_aborted_log ... ok
test_snippet_lines_printed_to_stderr ... ok
test_success_creates_no_artifacts ... ok

Ran 5 tests in 10.299s
OK
```

---

### preflight tests: ⚠️ FAIL (0/6)

```bash
$ python3 -m unittest tests.test_preflight_automerge_ruleset -v

ERROR: test_auth_failure_returns_2
  AttributeError: module does not have attribute 'get_env_token'

ERROR: test_missing_required_context_fails
  AttributeError: module does not have attribute 'get_env_token'

ERROR: test_ruleset_not_found_returns_3
  AttributeError: module does not have attribute 'get_env_token'

ERROR: test_success_path_via_http
  AttributeError: module does not have attribute 'get_env_token'

FAIL: test_classify_auth_prefers_bearer_when_token
  AssertionError: False != 'bearer'
  # Tests expect classify_auth() to return 'bearer' or 'token' strings
  # Implementation returns bool

FAIL: test_parse_args_rejects_malformed_want
  AssertionError: SystemExit not raised
```

---

## Root Cause: Test/Implementation Drift

The tests in `test_preflight_automerge_ruleset.py` were written for a different version of the code:

### Expected by tests (missing):
1. `get_env_token()` function
2. `classify_auth()` returning `'bearer'` or `'token'` strings
3. `http_get()` with different signature (3-tuple return)

### Actual implementation:
1. Token fetched inline in `http_get()` (no `get_env_token()`)
2. `classify_auth()` returns `bool` (auth error detection)
3. `http_get()` returns `(status_code, body)` 2-tuple

---

## Resolution Options

### **Option A: Update tests to match current implementation** (RECOMMENDED)

**Pros:**
- Minimal scope, surgical changes
- Tests validate actual M0-aligned behavior
- Removes outdated expectations

**Cons:**
- Tests may have documented requirements we're discarding

**Effort:** Low (1-2 hours)

---

### **Option B: Refactor implementation to match test expectations**

**Pros:**
- Tests might represent better architecture
- More testable with separated concerns

**Cons:**
- Larger scope, more changes
- Tests may expect outdated pre-M0 contract
- Risk of scope creep

**Effort:** Medium (3-5 hours)

---

### **Option C: Skip preflight tests, revisit in M2** (DEFER)

**Pros:**
- Focus on successful safe_run.py work
- Defer to M2-P1-I1 when conformance vectors exist
- Minimal immediate scope

**Cons:**
- Leaves known broken tests
- Delays full M1-P2-I1 completion

**Effort:** None (defer)

---

## Recommendation

**Choose Option A or C:**

**If tests are outdated:** Option A (update tests to current impl)  
**If unclear:** Option C (defer to M2 conformance work)

**Avoid:** Option B unless tests document critical requirements

---

## Next Steps (Pending Decision)

### If Option A:
1. Remove `get_env_token` mocking from tests
2. Update `classify_auth` assertions to expect `bool`
3. Update `http_get` mocking to 2-tuple return
4. Add M0-P2-I1 Bearer token validation test
5. Run tests, verify all pass

### If Option C:
1. Mark preflight tests as `@unittest.skip("M2: needs conformance")`
2. Document skip reason in test file
3. Move to next M1 item (M1-P3-I1 or M1-P5-I1)

### If Option B:
1. **STOP and create detailed design doc first**
2. Review with human before implementing
3. Estimate full scope and timeline

---

## Files Changed

- `scripts/python3/scripts/safe_run.py` (✅ M0 compliant, tests pass)
- `scripts/python3/scripts/preflight_automerge_ruleset.py` (✅ M0 compliant, tests fail)

## Files Needing Work

- `tests/test_preflight_automerge_ruleset.py` (needs Option A, B, or C decision)

---

**Awaiting human decision:** @m1ndn1nj4 please advise on resolution option.

**Refs:** #3 (Epic Tracker)
