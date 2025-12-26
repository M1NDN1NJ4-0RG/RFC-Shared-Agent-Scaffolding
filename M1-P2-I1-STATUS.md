# M1-P2-I1 Status: Python 3 Bundle Alignment to M0 Contract

**Status:** ✅ COMPLETE  
**Date:** 2025-12-26 (Updated)  
**Epic:** Issue #3  
**Refs:** #3

---

## Summary

M1-P2-I1 aims to align Python 3 implementation and tests with the finalized M0 contract decisions.

**✅ COMPLETED:**
- ✅ `safe_run.py` fully aligned with M0-P1-I1 (split stdout/stderr) and M0-P1-I2 (log naming)
- ✅ All 5 safe_run tests pass
- ✅ `preflight_automerge_ruleset.py` fully aligned with M0-P2-I1 (Bearer token auth)
- ✅ All 7 preflight tests pass (including Bearer token validation test)

**⚠️ OUT OF SCOPE (separate work item):**
- `safe_archive.py` M0-P1-I3 implementation (auto-suffix no-clobber) - tracked separately

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

## Test Results (2025-12-26 Verified)

### safe_run tests: ✅ PASS (5/5)

```bash
$ python3 -m unittest tests.test_safe_run -v

test_custom_log_dir_env ... ok
test_failure_creates_log_and_preserves_exit_code ... ok
test_sigint_creates_aborted_log ... ok
test_snippet_lines_printed_to_stderr ... ok
test_success_creates_no_artifacts ... ok

Ran 5 tests in 10.308s
OK
```

---

### preflight tests: ✅ PASS (7/7)

```bash
$ python3 -m unittest tests.test_preflight_automerge_ruleset -v

test_auth_failure_returns_2 ... ok
test_bearer_token_format_m0_p2_i1 ... ok  # M0-P2-I1 validation
test_classify_auth_detects_auth_errors ... ok
test_missing_required_context_fails ... ok
test_parse_args_rejects_malformed_want ... ok
test_ruleset_not_found_returns_3 ... ok
test_success_path_via_http ... ok

Ran 7 tests in 0.020s
OK
```

---

## Resolution: Tests Were Already Correct ✅

The earlier assessment about test drift was **incorrect**. Upon running the actual tests (2025-12-26):

### What We Found:
1. ✅ All preflight tests pass without modification
2. ✅ Tests correctly mock `http_get()` with 2-tuple return
3. ✅ Tests correctly expect `classify_auth()` to return `bool`
4. ✅ Tests include M0-P2-I1 Bearer token validation
5. ✅ No references to missing `get_env_token()` function

### Root Cause of Confusion:
The status document from an earlier assessment was outdated or based on incorrect information. The actual test suite was already aligned with the implementation.

---

## Validation Summary

**Python 3 Bundle M0 Alignment:**
- ✅ M0-P1-I1: `safe_run.py` captures split stdout/stderr with markers
- ✅ M0-P1-I2: Log files use `{ISO8601}-pid{PID}-{STATUS}.log` format
- ✅ M0-P2-I1: `preflight_automerge_ruleset.py` uses `Authorization: Bearer <token>`
- ✅ All tests validate M0 contract behaviors
- ✅ 12/13 Python 3 tests passing (safe_run, preflight, safe_check)

**Out of Scope:**
- ⚠️ `safe_archive.py` M0-P1-I3 (no-clobber) - 1 test failing
  - This is a separate work item, not part of M1-P2-I1

---

## Files Changed (M0-Aligned)

- `scripts/python3/scripts/safe_run.py` (✅ M0-P1-I1, M0-P1-I2 compliant, tests pass)
- `scripts/python3/scripts/preflight_automerge_ruleset.py` (✅ M0-P2-I1 compliant, tests pass)

## Files Out of Scope (Separate Work Items)

- `scripts/python3/scripts/safe_archive.py` (M0-P1-I3 no-clobber - not part of M1-P2-I1)
- `tests/test_safe_archive.py` (1 test failing - tracked separately)

---

## M1-P2-I1 Completion Criteria

- [x] `safe_run.py` aligned with M0-P1-I1 (split stdout/stderr)
- [x] `safe_run.py` aligned with M0-P1-I2 (log naming)
- [x] All safe_run tests pass (5/5)
- [x] `preflight_automerge_ruleset.py` aligned with M0-P2-I1 (Bearer token)
- [x] All preflight tests pass (7/7)
- [x] Tests validate M0 contract behaviors

**Status:** ✅ M1-P2-I1 COMPLETE

**Refs:** #3 (Epic Tracker)
