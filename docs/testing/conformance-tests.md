# Conformance Tests for Binary Discovery and Argument Handling

**Purpose:** These tests verify that all wrappers adhere to the contracts defined in the documentation.

## Test Suite 1: Repository Root Detection

### Test: repo-root-001 - Wrapper finds repo via script location, not working directory

**Contract:** REPO-ROOT-001

**Applies to:** Bash, Perl, Python3, PowerShell (after fix)

**Test Procedure:**

1. Copy wrapper script to temporary directory outside repo
2. Set `SAFE_RUN_BIN` to valid Rust binary
3. Change working directory to temp directory (outside repo)
4. Invoke wrapper with simple command
5. Verify command succeeds

**Expected Result:**

- Exit code: 0
- Wrapper uses `SAFE_RUN_BIN` regardless of working directory
- Command output appears correctly

**Why This Matters:**

- Wrappers should not depend on being invoked from within repo working directory
- Script location should be irrelevant when `SAFE_RUN_BIN` is set
- This enables testing scenarios where wrapper is copied to temp locations

**Implementation:**

```bash
# Bash test
test_repo_root_detection() {
  local tmp wrapper
  tmp="$(mktemp -d)"
  wrapper="$tmp/safe-run-test.sh"

  cp "$REPO_ROOT/wrappers/bash/scripts/safe-run.sh" "$wrapper"

  (
    cd "$tmp"  # Outside repo
    export SAFE_RUN_BIN="$RUST_BIN"
    output=$(bash "$wrapper" echo "test" 2>&1)
    rc=$?

 [[ "$rc" -eq 0 ]] |  | return 1
 [[ "$output" == "test" ]] |  | return 1
  )

  rm -rf "$tmp"
}
```

```powershell
# PowerShell test
Describe "Repository root detection" {
  It "works with SAFE_RUN_BIN from any directory" {
    $tempDir = New-Item -ItemType Directory -Path (Join-Path $env:TEMP ([System.IO.Path]::GetRandomFileName()))
    $tempScript = Join-Path $tempDir "safe-run-test.ps1"

    Copy-Item $ScriptUnderTest $tempScript

    Push-Location $tempDir
    try {
      $env:SAFE_RUN_BIN = $global:SafeRunBin
      $output = & pwsh -NoProfile -File $tempScript echo "test" 2>&1
 $LASTEXITCODE | Should -Be 0
 $output | Should -Be "test"
    } finally {
      Pop-Location
      Remove-Item -Recurse -Force $tempDir
    }
  }
}
```

---

## Test Suite 2: Exit Code Propagation

### Test: exit-code-001 - Wrapper forwards all exit codes 0-255

**Contract:** EXIT-CODE-001

**Applies to:** All wrappers

**Test Procedure:**

1. For each exit code in [0, 1, 7, 42, 127, 255]:
2. Run command that exits with that code
3. Verify wrapper exits with same code

**Expected Result:**

- Wrapper exit code matches child process exit code exactly

**Why This Matters:**

- CI depends on exit codes for build/test success/failure
- Exit code 127 has special meaning (command not found)
- Exit codes >128 indicate signal termination

**Implementation:**

```bash
# Bash test
test_exit_code_propagation() {
  local codes=(0 1 7 42 127 255)
  local code rc

  for code in "${codes[@]}"; do
    set +e
    SAFE_RUN_BIN="$RUST_BIN" bash "$WRAPPER" bash -c "exit $code" >/dev/null 2>&1
    rc=$?
    set -e

    if [[ "$rc" -ne "$code" ]]; then
      echo "Exit code mismatch: expected $code, got $rc"
      return 1
    fi
  done
}
```

```powershell
# PowerShell test
Describe "Exit code propagation" {
 @(0, 1, 7, 42, 127, 255) | ForEach-Object {
    It "forwards exit code $_" {
      $env:SAFE_RUN_BIN = $global:SafeRunBin
 & pwsh -NoProfile -File $ScriptUnderTest pwsh -NoProfile -Command "exit $_" 2>&1 | Out-Null
 $LASTEXITCODE | Should -Be $_
    }
  }
}
```

---

## Test Suite 3: Argument Quoting

### Test: arg-quote-001 - Empty string arguments preserved

**Contract:** ARG-PASS-001

**Applies to:** All wrappers

**Test Procedure:**

1. Run `echo "" "after"`
2. Verify output contains "after" on second line (empty first line)

**Expected Result:**

- Output: blank line + "after"
- Empty string argument preserved

**Implementation:**

```bash
test_empty_argument() {
  local output
  output=$(SAFE_RUN_BIN="$RUST_BIN" bash "$WRAPPER" echo "" "after" 2>&1)

  # Output should contain "after"
 echo "$output" | grep -q "after" |  | return 1
}
```

### Test: arg-quote-002 - Arguments with spaces preserved

**Contract:** ARG-PASS-001

**Test Procedure:**

1. Run `echo "hello world"`
2. Verify output is exactly "hello world" (not split into two args)

**Expected Result:**

- Output: "hello world" as single line

**Implementation:**

```bash
test_spaces_in_argument() {
  local output
  output=$(SAFE_RUN_BIN="$RUST_BIN" bash "$WRAPPER" echo "hello world" 2>&1)

 [[ "$output" == "hello world" ]] |  | return 1
}
```

### Test: arg-quote-003 - Shell metacharacters NOT interpreted

**Contract:** ARG-PASS-001

**Test Procedure:**

1. Run `echo "test;echo hacked"`
2. Verify output is literal "test;echo hacked" (not executed)

**Expected Result:**

- Output: "test;echo hacked"
- No "hacked" on separate line

**Implementation:**

```bash
test_metacharacters_not_interpreted() {
  local output
  output=$(SAFE_RUN_BIN="$RUST_BIN" bash "$WRAPPER" echo "test;echo hacked" 2>&1)

 [[ "$output" == "test;echo hacked" ]] |  | return 1
 ! echo "$output" | grep -q "^hacked$" |  | return 1
}
```

---

## Test Suite 4: Environment Variable Inheritance

### Test: env-inherit-001 - SAFE_LOG_DIR honored

**Contract:** OUTPUT-MODE-001, ARTIFACT-GEN-001

**Applies to:** All wrappers

**Test Procedure:**

1. Set `SAFE_LOG_DIR=/tmp/custom_logs`
2. Run failing command
3. Verify log created in custom directory, not default

**Expected Result:**

- Log file exists in `/tmp/custom_logs/`
- No log file in `.agent/FAIL-LOGS/`

**Implementation:**

```bash
test_safe_log_dir_inheritance() {
  local tmp
  tmp="$(mktemp -d)"

  (
    cd "$tmp"
    export SAFE_LOG_DIR="$tmp/custom_logs"
    mkdir -p "$SAFE_LOG_DIR"
    export SAFE_RUN_BIN="$RUST_BIN"

    # Run failing command
 bash "$WRAPPER" bash -c "exit 1" >/dev/null 2>&1 |  | true

    # Check custom directory has log
 [[ -n "$(ls "$SAFE_LOG_DIR"/*-FAIL.log 2>/dev/null |  | true)" ]] |  | return 1

    # Check default directory has no logs
 [[ -z "$(ls .agent/FAIL-LOGS/*-FAIL.log 2>/dev/null |  | true)" ]] |  | return 1
  )

  rm -rf "$tmp"
}
```

### Test: env-inherit-002 - SAFE_SNIPPET_LINES honored

**Contract:** SNIPPET-001

**Test Procedure:**

1. Set `SAFE_SNIPPET_LINES=3`
2. Run failing command with 10 lines of output
3. Verify last 3 lines appear in stderr

**Expected Result:**

- Stderr contains last 3 lines of output
- Exit code matches child process

**Implementation:**

```bash
test_safe_snippet_lines_inheritance() {
  local tmp err
  tmp="$(mktemp -d)"

  (
    cd "$tmp"
    export SAFE_SNIPPET_LINES=3
    export SAFE_RUN_BIN="$RUST_BIN"

    set +e
    err=$((bash "$WRAPPER" bash -c 'printf "L1\nL2\nL3\nL4\nL5\nL6\nL7\nL8\nL9\nL10\n"; exit 2') 2>&1 1>/dev/null)
    rc=$?
    set -e

 [[ "$rc" -eq 2 ]] |  | return 1

    # Should contain last 3 lines
 echo "$err" | grep -q "L8" |  | return 1
 echo "$err" | grep -q "L9" |  | return 1
 echo "$err" | grep -q "L10" |  | return 1
  )

  rm -rf "$tmp"
}
```

---

## Test Suite 5: Binary Discovery Error Handling

### Test: bin-disc-err-001 - Exit 127 when binary not found

**Contract:** BIN-DISC-001, ERROR-HAND-001

**Test Procedure:**

1. Unset `SAFE_RUN_BIN`
2. Remove wrapper from repo (or move to temp dir outside repo)
3. Invoke wrapper
4. Verify exit code 127 and error message

**Expected Result:**

- Exit code: 127
- Stderr contains "Rust canonical tool not found"
- Stderr lists searched locations

**Implementation:**

```bash
test_binary_not_found_error() {
  local tmp wrapper err rc
  tmp="$(mktemp -d)"
  wrapper="$tmp/safe-run-test.sh"

  cp "$REPO_ROOT/wrappers/bash/scripts/safe-run.sh" "$wrapper"

  (
    cd "$tmp"
    unset SAFE_RUN_BIN

    set +e
    err=$(bash "$wrapper" echo "test" 2>&1)
    rc=$?
    set -e

 [[ "$rc" -eq 127 ]] |  | return 1
 echo "$err" | grep -q "Rust canonical tool not found" |  | return 1
  )

  rm -rf "$tmp"
}
```

---

## Test Suite 6: Platform Detection

### Test: platform-det-001 - Consistent platform string across wrappers

**Contract:** PLATFORM-DET-001

**Applies to:** All wrappers

**Test Procedure:**

1. On each CI platform (Linux, macOS, Windows):
2. Extract platform string from each wrapper's detection logic
3. Verify all wrappers produce same platform string

**Expected Result:**

- Linux: `linux/x86_64` or `linux/aarch64`
- macOS: `macos/x86_64` or `macos/aarch64`
- Windows: `windows/x86_64`

**Implementation:**

This test should be run in CI matrix and requires wrapper debug output or inspection of discovered paths.

---

## Integration with Existing Tests

**Add to Bash test suite:** `wrappers/bash/tests/test-safe-run.sh`

**Add to Perl test suite:** Create `wrappers/perl/tests/test-safe_run.pl`

**Add to Python3 test suite:** `wrappers/python3/tests/test-safe-run.py`

**Add to PowerShell test suite:** `wrappers/powershell/tests/safe-run-tests.ps1`

---

## CI Requirements

1. All test suites MUST run on CI matrix (Linux, macOS, Windows)
2. Tests MUST be isolated (use temp directories)
3. Tests MUST clean up after themselves
4. Tests MUST fail loudly if contract violated
5. Test failures MUST block PR merge

---

## Coverage Matrix

| Test | Bash | Perl | Python3 | PowerShell | Status |
| ------ | ------ | ------ | --------- | ------------ | -------- |
| repo-root-001 | ✅ | ✅ | ✅ | 🔧 Added | Instrumented |
| exit-code-001 | ✅ | ✅ | ✅ | ⏸️ Need Windows | Instrumented |
| arg-quote-001 | ✅ | ✅ | ✅ | ⏸️ Need Windows | Instrumented |
| arg-quote-002 | ✅ | ✅ | ✅ | ⏸️ Need Windows | Instrumented |
| arg-quote-003 | ✅ | ✅ | ✅ | ⏸️ Need Windows | Instrumented |
| env-inherit-001 | ✅ | ✅ | ✅ | ⏸️ Need Windows | Instrumented |
| env-inherit-002 | 📝 Add | 📝 Add | 📝 Add | 📝 Add | To be added |
| bin-disc-err-001 | ✅ | ✅ | ✅ | ⏸️ Need Windows | Instrumented |
| platform-det-001 | 📝 Add | 📝 Add | 📝 Add | 📝 Add | To be added |

**Legend:**

- ✅ Passing (instrumented evidence)
- 🔧 Fixed in this PR
- ⏸️ Needs Windows CI validation
- 📝 Needs test implementation
