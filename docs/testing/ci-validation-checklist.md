# CI Validation Checklist

**Purpose:** This document specifies what CI must validate to confirm contract hardening is complete.

**Status:** Waiting for CI run on PR

---

## Required CI Jobs

### 1. Test Bash Bundle (Linux) ✅ Expected to PASS

**Runner:** `ubuntu-latest`

**What it tests:**
- All 13 bash tests including 6 new conformance tests
- Rust binary discovery from `dist/linux/x86_64/`
- Repository root detection
- Exit code propagation
- Argument quoting edge cases
- Environment variable inheritance
- Binary not found error handling

**Expected Result:** ✅ ALL TESTS PASS (already passed locally)

**Evidence:** Local run shows 13/13 passing

---

### 2. Test PowerShell Bundle (Windows) ⏸️ NEEDS VALIDATION

**Runner:** `windows-latest`

**What it tests:**
- PowerShell wrapper with fixes applied
- Repo root detection from script location (NEW FIX)
- PS 5.1 platform detection compatibility (NEW FIX)
- Exit code handling with binary existence check (NEW FIX)
- Rust binary discovery from `dist/windows/x86_64/safe-run.exe`

**Expected Result:** ✅ ALL TESTS SHOULD PASS

**Critical Validations:**
1. **Repo root detection:** Script should find repo from `$PSCommandPath`, not `Get-Location`
2. **Platform detection:** Should work on both PS 5.1 and PS 7+
3. **Exit code 127:** Binary not found should exit with 127, not 1
4. **Binary discovery:** Should find `.exe` in dist/windows/x86_64/

**What to watch for:**
- Any test failures related to working directory assumptions
- Exit code mismatches (1 vs 127)
- Platform detection failures on PS 5.1

---

### 3. Test Perl Bundle (Linux) ✅ Expected to PASS

**Runner:** `ubuntu-latest`

**What it tests:**
- Perl wrapper (no changes, but validation needed)
- Existing perl tests

**Expected Result:** ✅ ALL TESTS PASS (no changes made to perl wrapper)

**Evidence:** Instrumentation tests show perl wrapper is contract-compliant

---

### 4. Test Python3 Bundle (Linux) ✅ Expected to PASS

**Runner:** `ubuntu-latest`

**What it tests:**
- Python3 wrapper (no changes, but validation needed)
- Existing python3 tests

**Expected Result:** ✅ ALL TESTS PASS (no changes made to python3 wrapper)

**Evidence:** Instrumentation tests show python3 wrapper is contract-compliant

---

### 5. Rust Conformance (Multi-platform) ✅ Expected to PASS

**Runners:** `ubuntu-latest`, `macos-latest`, `windows-latest`

**What it tests:**
- Rust canonical tool conformance
- Event ledger format
- Exit code behavior
- Artifact generation

**Expected Result:** ✅ ALL TESTS PASS (no changes to Rust code)

**Note:** This validates the Rust binary itself, not the wrappers

---

## Success Criteria

### All CI Jobs Must Pass

For this PR to be considered complete and the repository ready for new language wrappers:

✅ **MUST PASS:**
1. Test Bash Bundle (Linux) - 13/13 tests
2. Test PowerShell Bundle (Windows) - All tests
3. Test Perl Bundle (Linux) - All tests
4. Test Python3 Bundle (Linux) - All tests
5. Rust Conformance (All platforms) - All tests

### Critical Validations Checklist

- [ ] Bash conformance tests all pass on Linux
- [ ] PowerShell wrapper works from any directory (repo root detection fix)
- [ ] PowerShell wrapper exits with 127 when binary not found
- [ ] PowerShell platform detection works on Windows
- [ ] Perl wrapper passes all tests
- [ ] Python3 wrapper passes all tests
- [ ] No regressions in existing functionality

---

## If CI Fails

### Bash Tests Fail

**Unlikely** (already passed locally)

**Debug steps:**
1. Check which conformance test failed
2. Review test output for error messages
3. Verify Rust binary was built and staged correctly
4. Check if repo root detection is working

### PowerShell Tests Fail

**Possible** (new fixes need validation)

**Debug steps:**

**If repo root detection fails:**
- Verify `$PSCommandPath` is available on Windows runner
- Check fallback to `Get-Location` works if script path unavailable
- Confirm tests are running with `pwsh -NoProfile -File`

**If platform detection fails:**
- Check PowerShell version on Windows runner (`$PSVersionTable.PSVersion`)
- Verify PS 5.1 fallback logic (`$os = "windows"`)
- Check if `[System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture` works

**If exit code handling fails:**
- Check if `Test-Path $binary` is working correctly
- Verify `$LASTEXITCODE` is being captured correctly
- Confirm try/catch is exiting with 127

**If binary discovery fails:**
- Verify `.exe` extension is being added on Windows
- Check if `dist/windows/x86_64/safe-run.exe` was staged correctly
- Confirm `Get-Command` is finding binary in PATH

### Perl/Python3 Tests Fail

**Unlikely** (no changes made)

**Debug steps:**
1. Check if failure is related to Rust binary staging
2. Verify no unexpected regressions from document changes
3. Compare test output to previous successful runs

---

## Post-CI Actions

### If All Tests Pass ✅

1. **Merge PR** - Repository is hardened and ready
2. **Update documentation** - Mark repository as ready for new language wrappers
3. **Create new language wrapper** - Follow process in `conformance-tests.md`

### If Any Tests Fail ❌

1. **DO NOT MERGE** - Fix failures first
2. **Debug using steps above** - Identify root cause
3. **Apply fixes** - Make minimal changes to address failures
4. **Re-run CI** - Validate fixes
5. **Update evidence** - Document what was fixed and why

---

## Evidence of CI Success

Once CI passes, document results here:

**Bash Tests (Linux):**
- Status: ⏸️ Waiting
- Tests passed: _/13
- Link: [CI Run URL]

**PowerShell Tests (Windows):**
- Status: ⏸️ Waiting
- Tests passed: _/_
- Link: [CI Run URL]

**Perl Tests (Linux):**
- Status: ⏸️ Waiting
- Tests passed: _/_
- Link: [CI Run URL]

**Python3 Tests (Linux):**
- Status: ⏸️ Waiting
- Tests passed: _/_
- Link: [CI Run URL]

**Rust Conformance (All platforms):**
- Status: ⏸️ Waiting
- Linux: ⏸️
- macOS: ⏸️
- Windows: ⏸️
- Link: [CI Run URL]

---

## Notes for Reviewers

**What changed:**
1. PowerShell wrapper: 3 critical fixes (101 lines)
2. Bash test suite: 6 new conformance tests (125 lines)
3. Documentation: 5 new documents (~48 KB)

**What to review:**
1. PowerShell fixes align with bash/perl/python3 behavior
2. Conformance tests are comprehensive and fail-safe
3. Documentation is complete and accurate
4. CI validation proves fixes work on all platforms

**What NOT to worry about:**
- Bash/Perl/Python3 wrappers: No changes, already compliant
- Rust canonical tool: No changes
- Existing tests: All still passing

**Approval criteria:**
- ✅ All CI jobs pass
- ✅ Evidence documents are complete
- ✅ Code changes align with documented contracts
- ✅ Tests prevent future drift

---

## Final Checklist

Before declaring work complete:

- [ ] All CI jobs pass (bash, perl, python3, powershell, rust)
- [ ] Evidence documented in this file
- [ ] No test regressions
- [ ] PowerShell fixes validated on Windows
- [ ] Repository declared ready for new language wrappers

---

**Last Updated:** 2025-12-27 (waiting for CI run)
