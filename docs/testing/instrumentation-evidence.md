# Phase 3: Instrumentation & Reproduction Evidence

**Execution Date:** 2024-12-27
**Test Environment:** Linux (Ubuntu), Rust 0.1.1 canonical binary

## Test Setup

- **Rust Binary:** `/home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/rust/target/release/safe-run`
- **Rust Version:** `safe-run 0.1.1`
- **Test Script:** `/tmp/vector-instrumentation.sh`

## Vector 1: Repository Root Detection

### Test 1a: Bash wrapper with SAFE_RUN_BIN from outside repo

**Setup:**

- Copied bash wrapper to `/tmp/tmp.GWi3ha9zcq/safe-run-test.sh`
- Changed working directory to temp directory (outside repo)
- Set `SAFE_RUN_BIN` to point to Rust binary

**Command:**

```bash
cd /tmp/tmp.GWi3ha9zcq
export SAFE_RUN_BIN=/path/to/rust/safe-run
bash ./safe-run-test.sh echo "test from temp"
```

**Result:** ✅ PASS

- Exit code: 0
- Output: `test from temp`
- **Evidence:** Bash wrapper correctly uses SAFE_RUN_BIN regardless of working directory

### Test 1b: Bash wrapper without SAFE_RUN_BIN, from outside repo

**Setup:**

- Bash wrapper in temp directory (outside repo)
- Changed working directory to temp directory
- `SAFE_RUN_BIN` not set

**Command:**

```bash
cd /tmp/tmp.GWi3ha9zcq
unset SAFE_RUN_BIN
bash ./safe-run-test.sh echo "test"
```

**Result:** ✅ PASS

- Exit code: 127 (command not found)
- Error message: "Rust canonical tool not found"
- **Evidence:** Bash wrapper correctly fails with exit 127 and actionable error when binary cannot be found

### Test 1c: Bash wrapper from within repo

**Setup:**

- Working directory in repo root
- `SAFE_RUN_BIN` not set
- Relies on repo root detection

**Command:**

```bash
cd /path/to/repo
unset SAFE_RUN_BIN
bash ./wrappers/bash/scripts/safe-run.sh echo "test from repo"
```

**Result:** ✅ PASS

- Exit code: 0
- Output: `test from repo`
- **Evidence:** Bash wrapper successfully finds binary via repo root detection (walks up from script location)

### PowerShell Comparison

**Issue Identified:** PowerShell wrapper uses `Get-Location` (working directory) instead of script location to find repo root.

**Impact:**

- PowerShell wrapper requires being invoked from within repo working directory
- Bash/Perl/Python3 work from any working directory as long as wrapper script is in repo structure
- **This is a P0 CRITICAL inconsistency**

**Conclusion:** PowerShell wrapper needs to be fixed to walk up from script location, not working directory.

---

## Vector 3: Exit Code Propagation

### Test Matrix: All wrappers, exit codes 0, 1, 7, 42, 127, 255

**Test Command Template:**

```bash
export SAFE_RUN_BIN=/path/to/safe-run
wrapper_script bash -c "exit N"
```

### Results: Bash Wrapper

| Exit Code | Expected | Actual | Status |
|-----------|----------|--------|--------|
| 0 | 0 | 0 | ✅ |
| 1 | 1 | 1 | ✅ |
| 7 | 7 | 7 | ✅ |
| 42 | 42 | 42 | ✅ |
| 127 | 127 | 127 | ✅ |
| 255 | 255 | 255 | ✅ |

**Evidence:** Bash wrapper correctly forwards all exit codes using `exec`

### Results: Perl Wrapper

| Exit Code | Expected | Actual | Status |
|-----------|----------|--------|--------|
| 0 | 0 | 0 | ✅ |
| 1 | 1 | 1 | ✅ |
| 7 | 7 | 7 | ✅ |
| 42 | 42 | 42 | ✅ |
| 127 | 127 | 127 | ✅ |
| 255 | 255 | 255 | ✅ |

**Evidence:** Perl wrapper correctly forwards all exit codes using `exec`

### Results: Python3 Wrapper

| Exit Code | Expected | Actual | Status |
|-----------|----------|--------|--------|
| 0 | 0 | 0 | ✅ |
| 1 | 1 | 1 | ✅ |
| 7 | 7 | 7 | ✅ |
| 42 | 42 | 42 | ✅ |
| 127 | 127 | 127 | ✅ |
| 255 | 255 | 255 | ✅ |

**Evidence:** Python3 wrapper correctly forwards all exit codes using `os.execvp`

### PowerShell Status

**Not tested on Linux** (PowerShell wrapper testing requires Windows runner)

**Known Issue:** PowerShell uses `& $binary` + `$LASTEXITCODE`, which may return null if binary fails to execute.

**Conclusion:** Bash, Perl, Python3 wrappers correctly forward exit codes. PowerShell needs testing on Windows CI.

---

## Vector 4: Argument Quoting Edge Cases

### Test Cases

1. **Empty string argument:** `echo "" "after"`
2. **Spaces in argument:** `echo "hello world"`
3. **Shell metacharacters:** `echo "test;echo hacked"` (should be literal, not executed)

### Results: Bash Wrapper

| Test Case | Expected Output | Actual Output | Status |
|-----------|----------------|---------------|--------|
| Empty arg | `\n` + `after` | Contains `after` | ✅ |
| Spaces | `hello world` | `hello world` | ✅ |
| Metacharacters | `test;echo hacked` (literal) | `test;echo hacked` | ✅ |

**Evidence:** Bash wrapper uses `"$@"` which correctly preserves all quoting

### Results: Perl Wrapper

| Test Case | Expected Output | Actual Output | Status |
|-----------|----------------|---------------|--------|
| Empty arg | `\n` + `after` | Contains `after` | ✅ |
| Spaces | `hello world` | `hello world` | ✅ |
| Metacharacters | `test;echo hacked` (literal) | `test;echo hacked` | ✅ |

**Evidence:** Perl wrapper passes `@args` to exec as list, correctly preserving quoting

### Results: Python3 Wrapper

| Test Case | Expected Output | Actual Output | Status |
|-----------|----------------|---------------|--------|
| Empty arg | `\n` + `after` | Contains `after` | ✅ |
| Spaces | `hello world` | `hello world` | ✅ |
| Metacharacters | `test;echo hacked` (literal) | `test;echo hacked` | ✅ |

**Evidence:** Python3 wrapper passes `sys.argv[1:]` as list to execvp, correctly preserving quoting

**Conclusion:** All three Unix wrappers correctly handle argument quoting edge cases. PowerShell needs testing with `@args` splatting.

---

## Vector 9: Environment Variable Inheritance

### Test: SAFE_LOG_DIR

**Setup:**

- Set `SAFE_LOG_DIR=/tmp/custom_logs`
- Run failing command to trigger log creation
- Verify log appears in custom directory, not default `.agent/FAIL-LOGS/`

**Test Command:**

```bash
export SAFE_LOG_DIR=/tmp/custom_logs
wrapper_script bash -c "echo test; exit 1"
```

### Results: Bash Wrapper

- Custom log directory: `/tmp/custom_logs`
- Log file created: ✅ (found `*-FAIL.log` in custom directory)
- Default directory used: ❌ (no logs in `.agent/FAIL-LOGS/`)

**Evidence:** Bash wrapper correctly inherits SAFE_LOG_DIR via `exec` environment inheritance

### Results: Perl Wrapper

- Custom log directory: `/tmp/custom_logs`
- Log file created: ✅ (found `*-FAIL.log` in custom directory)
- Default directory used: ❌ (no logs in `.agent/FAIL-LOGS/`)

**Evidence:** Perl wrapper correctly inherits SAFE_LOG_DIR via `exec` environment inheritance

### Results: Python3 Wrapper

- Custom log directory: `/tmp/custom_logs`
- Log file created: ✅ (found `*-FAIL.log` in custom directory)
- Default directory used: ❌ (no logs in `.agent/FAIL-LOGS/`)

**Evidence:** Python3 wrapper correctly inherits SAFE_LOG_DIR via `os.execvp` environment inheritance

**Conclusion:** All tested wrappers correctly inherit environment variables. This is automatic for exec-based wrappers.

---

## Summary of Evidence

### Vectors Successfully Reproduced

1. ✅ **Vector 1 (Repo root detection):** Bash wrapper works correctly, PowerShell uses different strategy
2. ✅ **Vector 3 (Exit code propagation):** All Unix wrappers forward exit codes correctly
3. ✅ **Vector 4 (Argument quoting):** All Unix wrappers handle edge cases correctly
4. ✅ **Vector 9 (Env var inheritance):** All Unix wrappers inherit environment variables

### Critical Findings

1. **Bash, Perl, Python3 wrappers are contract-compliant** for all tested vectors
2. **PowerShell wrapper has known issues:**
   - Uses working directory instead of script location for repo root detection
   - Exit code handling needs verification on Windows
   - Platform variable availability needs PS 5.1 compatibility
3. **All Unix wrappers use `exec` or equivalent**, which automatically provides:
   - Correct exit code forwarding
   - Environment variable inheritance
   - No wrapper process overhead

### Next Steps

1. **Fix PowerShell wrapper issues:**
   - Change repo root detection to use script location (like other wrappers)
   - Verify exit code handling on Windows CI
   - Add PS 5.1 compatibility for platform detection
2. **Add conformance tests** for these vectors to prevent future drift
3. **Run full test suite** on Windows CI to validate PowerShell fixes
