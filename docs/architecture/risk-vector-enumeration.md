# Risk Vector Enumeration & Prioritization

**Purpose:** Identify all ways each wrapper might drift from the contract, prioritized by impact.

**Priority Levels:**
- **P0 (Critical):** Will cause test failures or incorrect behavior in production
- **P1 (High):** May cause failures in edge cases or specific environments
- **P2 (Medium):** Unlikely to cause failures, but violates contract consistency

---

## Vector 1: PowerShell Repository Root Detection Inconsistency

**Priority:** P0 (CRITICAL)

**Affected Contract:** REPO-ROOT-001

**Issue:** PowerShell wrapper uses `Get-Location` (current working directory) to find repo root, while bash/perl/python3 use script location.

**Evidence:**
```powershell
# PowerShell (safe-run.ps1:29)
$current = (Get-Location).Path

# vs Bash (safe-run.sh:17)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# vs Python (safe-run.py:23-24)
script_path = Path(__file__).resolve()
current = script_path.parent
```

**Reproduction Scenario:**
1. Copy PowerShell wrapper to `/tmp/safe-run.ps1`
2. Run from within repo: `cd /path/to/repo && pwsh /tmp/safe-run.ps1 echo test`
3. **Expected:** Should work (script should find repo root from script location)
4. **Actual:** Will work because working dir IS in repo
5. Run from outside repo: `cd /tmp && pwsh /tmp/safe-run.ps1 echo test`
6. **Expected:** Should fail with "binary not found" (repo root not found)
7. **Actual:** Will fail, **BUT** for different reason than other wrappers

**Impact:**
- PowerShell tests MUST be run from within repo working directory
- Breaks if wrapper is copied elsewhere (common in testing scenarios)
- Inconsistent with other three wrappers

**Test Case to Add:**
```powershell
Describe "Repository root detection" {
  It "finds repo root from script location, not working directory" {
    # Copy script to temp location
    $tempScript = Join-Path $env:TEMP "safe-run-test.ps1"
    Copy-Item $ScriptUnderTest $tempScript
    
    # Change to temp directory (OUTSIDE repo)
    Push-Location $env:TEMP
    try {
      # Script should still find repo via SAFE_RUN_BIN or fail with proper error
      # NOT crash because it's looking in wrong directory
      $env:SAFE_RUN_BIN = "nonexistent"
      & $tempScript echo test 2>&1 | Should -Match "Rust canonical tool not found"
    } finally {
      Pop-Location
      Remove-Item $tempScript -ErrorAction SilentlyContinue
    }
  }
}
```

**Mitigation:**
- Fix PowerShell wrapper to walk up from script location like other wrappers
- OR: Document that PowerShell wrapper MUST be invoked from within repo
- OR: Make PowerShell wrapper try both strategies (script location, then working dir)

---

## Vector 2: SAFE_RUN_BIN Validation

**Priority:** P0 (CRITICAL)

**Affected Contract:** BIN-DISC-001

**Issue:** Contract says "use without validation" but wrappers may check if file exists.

**Evidence:**
```bash
# Bash (safe-run.sh:56-58) - CORRECT
if [ -n "${SAFE_RUN_BIN:-}" ]; then
  echo "$SAFE_RUN_BIN"
  return 0
fi

# Python (safe-run.py:62-64) - CORRECT
safe_run_bin = os.environ.get("SAFE_RUN_BIN")
if safe_run_bin:
    return safe_run_bin  # No validation!

# PowerShell (safe-run.ps1:65-67) - CORRECT
if ($env:SAFE_RUN_BIN) {
    return $env:SAFE_RUN_BIN
}
```

**Current Status:** All wrappers correctly return SAFE_RUN_BIN without validation ✅

**Reproduction Scenario:**
1. Set `SAFE_RUN_BIN=/does/not/exist`
2. Run wrapper: `./safe-run.sh echo test`
3. **Expected:** Wrapper attempts to exec nonexistent binary, gets clear error from exec
4. **Actual:** (Test to confirm)

**Test Case to Add:**
```bash
test_safe_run_bin_override_without_validation() {
  export SAFE_RUN_BIN=/nonexistent/binary
  # Should fail during exec, not during discovery
  # Error message should come from exec, not from wrapper's validation
  ./safe-run.sh echo test 2>&1 | grep -v "Searched locations"
}
```

**Mitigation:** None needed - wrappers already comply ✅

---

## Vector 3: Exit Code Propagation (PowerShell $LASTEXITCODE)

**Priority:** P0 (CRITICAL)

**Affected Contract:** EXIT-CODE-001

**Issue:** PowerShell's $LASTEXITCODE may be null if command fails to execute, leading to incorrect exit code.

**Evidence:**
```powershell
# PowerShell (safe-run.ps1:140-146)
try {
    & $binary run @invokeArgs
    $exitCode = $LASTEXITCODE
    if ($null -eq $exitCode) {
        # If LASTEXITCODE is null, the command may have failed to execute
        exit 1
    }
    exit $exitCode
```

**Reproduction Scenario:**
1. Set `SAFE_RUN_BIN=/nonexistent/binary`
2. Run wrapper: `./safe-run.ps1 echo test`
3. **Expected:** Exit code 127 or similar "command not found"
4. **Actual:** May exit with code 1 (generic error)

**Impact:**
- CI may not detect actual failure reason
- Exit code contract violated
- Inconsistent with bash/perl/python (which use exec)

**Test Case to Add:**
```powershell
Describe "Exit code propagation" {
  It "exits with 127 when binary not found" {
    $env:SAFE_RUN_BIN = "/nonexistent/binary"
    # Suppress error output
    $null = & $ScriptUnderTest echo test 2>&1
    # Exit code should be 127 (command not found), not 1
    # This may require fixing the wrapper to check file existence before invoking
    # OR catching specific exception types
  }
}
```

**Mitigation:**
- Validate binary exists before invoking (conflicts with Vector 2 for discovery, but OK for final exec)
- OR: Catch specific exceptions and map to proper exit codes
- OR: Use Start-Process with better error handling

---

## Vector 4: Argument Quoting Edge Cases

**Priority:** P0 (CRITICAL)

**Affected Contract:** ARG-PASS-001

**Issue:** Complex arguments with spaces, quotes, and special characters may be interpreted differently across wrappers.

**Test Cases:**

### 4a. Empty String Arguments
```bash
./safe-run.sh echo "" "not empty"
# Expected output: (blank line) + "not empty"
```

### 4b. Arguments with Spaces
```bash
./safe-run.sh echo "hello world"
# Expected output: "hello world"
```

### 4c. Arguments with Quotes
```bash
./safe-run.sh echo "He said \"hello\""
# Expected output: He said "hello"
```

### 4d. Arguments with Shell Metacharacters
```bash
./safe-run.sh echo "test; echo hacked"
# Expected output: test; echo hacked (NOT: test + (separate) hacked)
```

### 4e. Arguments with Newlines
```bash
./safe-run.sh printf "line1\nline2"
# Expected output: line1(newline)line2
```

**Reproduction Plan:**
Create test suite that runs identical edge-case arguments through all 4 wrappers and compares outputs.

**Test Case to Add:**
```bash
# In conformance suite
test_argument_edge_cases() {
  local cases=(
    'echo ""'
    'echo "hello world"'
    'echo "He said \"hello\""'
    'echo "\$PATH"'
    'printf "a\nb\nc"'
  )
  
  for cmd in "${cases[@]}"; do
    # Run through each wrapper and compare outputs
  done
}
```

**Mitigation:**
- Ensure all wrappers use proper quoting:
  - Bash: `"$@"` ✅
  - Perl: `@args` passed to exec ✅
  - Python: `sys.argv[1:]` as list ✅
  - PowerShell: `@invokeArgs` (splatting) ✅

---

## Vector 5: Platform Detection Accuracy

**Priority:** P1 (HIGH)

**Affected Contract:** PLATFORM-DET-001

**Issue:** Different languages may report architecture differently.

**Evidence:**
- `uname -m` on Linux: `x86_64` or `amd64`?
- Python `platform.machine()`: `x86_64` or `AMD64` (Windows)?
- PowerShell `[System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture`: `X64` → needs mapping

**Reproduction Scenario:**
1. Run on different platforms and log platform detection results
2. Verify all wrappers produce same path for same platform

**Test Case to Add:**
```bash
# CI matrix test - run on Linux, macOS, Windows
test_platform_detection_consistency() {
  # Extract platform string from wrapper debug output
  # All wrappers should produce same platform string on same runner
}
```

**Mitigation:**
- Normalize architecture names consistently:
  - `amd64` → `x86_64`
  - `AMD64` → `x86_64`
  - `arm64` → `aarch64`
- Document canonical names in contract

---

## Vector 6: PowerShell Platform Variable Availability (PS 5.1 vs 7+)

**Priority:** P1 (HIGH)

**Affected Contract:** PLATFORM-DET-001

**Issue:** PowerShell 5.1 (Windows built-in) doesn't have `$IsLinux`, `$IsMacOS`, `$IsWindows` variables.

**Evidence:**
```powershell
# PowerShell (safe-run.ps1:48-51)
$os = if ($IsLinux) { "linux" }
      elseif ($IsMacOS) { "macos" }
      elseif ($IsWindows) { "windows" }
      else { "unknown" }
```

**Reproduction Scenario:**
1. Run on Windows with PowerShell 5.1 (default)
2. `$IsWindows` is not defined
3. Wrapper may fail or detect as "unknown"

**Mitigation:**
- Add fallback detection for PS 5.1:
```powershell
$os = if ($PSVersionTable.PSVersion.Major -ge 6) {
    if ($IsLinux) { "linux" }
    elseif ($IsMacOS) { "macos" }
    elseif ($IsWindows) { "windows" }
    else { "unknown" }
} else {
    # PS 5.1 (Windows only)
    "windows"
}
```

---

## Vector 7: Signal Exit Code Mapping (Unix vs Windows)

**Priority:** P1 (HIGH)

**Affected Contract:** EXIT-CODE-001

**Issue:** Unix shells map signals to 128+N, but Windows doesn't have Unix signals.

**Current Implementation:** Rust binary handles this, wrappers just forward exit code.

**Test Coverage:** Need tests that verify:
- SIGTERM (Ctrl+C simulation) → exit 130 or 143 on Unix
- Windows termination → preserves Windows exit codes

**Test Case to Add:**
```bash
# Unix only
test_sigint_exit_code() {
  timeout 1s ./safe-run.sh sleep 10 || rc=$?
  # Should be 143 (SIGTERM) or 130 (SIGINT), not 1 or 124
  [[ "$rc" -eq 143 || "$rc" -eq 130 ]]
}
```

**Mitigation:** None needed for wrappers (Rust handles it), but tests should verify.

---

## Vector 8: Binary Extension on Windows (.exe)

**Priority:** P1 (HIGH)

**Affected Contract:** BIN-DISC-001

**Issue:** Windows requires `.exe` extension for executables.

**Evidence:**
```powershell
# PowerShell (safe-run.ps1:72)
$binaryName = if ($IsWindows) { "safe-run.exe" } else { "safe-run" }
```

**Reproduction Scenario:**
1. On Windows, Rust build produces `safe-run.exe`
2. CI stages it as `dist/windows/x86_64/safe-run.exe`
3. Wrapper must look for `.exe` extension
4. Unix wrappers on Windows (bash via Git Bash) may or may not need `.exe`

**Test Case to Add:**
```powershell
# Windows only
Describe "Binary discovery on Windows" {
  It "finds .exe binary in dist" {
    $env:SAFE_RUN_BIN = ""
    # Ensure dist/windows/x86_64/safe-run.exe exists
    # Wrapper should find it
  }
}
```

**Mitigation:**
- PowerShell: Already handles ✅
- Bash on Windows: May need to try both `safe-run` and `safe-run.exe`
- Perl on Windows: May need to try both
- Python on Windows: `shutil.which` should handle automatically

---

## Vector 9: Environment Variable Inheritance

**Priority:** P0 (CRITICAL)

**Affected Contract:** OUTPUT-MODE-001, ARTIFACT-GEN-001, SNIPPET-001

**Issue:** Wrappers must pass through all environment variables to Rust binary.

**Variables that MUST be inherited:**
- `SAFE_RUN_VIEW` (output mode)
- `SAFE_LOG_DIR` (artifact directory)
- `SAFE_SNIPPET_LINES` (snippet size)
- Any future env vars defined in contract

**Current Implementation:**
- Bash: `exec` inherits all env vars ✅
- Perl: `exec` inherits all env vars ✅
- Python: `os.execvp` inherits all env vars ✅
- PowerShell: `& $binary` inherits all env vars ✅

**Test Case to Add:**
```bash
test_env_var_inheritance() {
  export SAFE_RUN_VIEW=merged
  export SAFE_LOG_DIR=/tmp/custom
  export SAFE_SNIPPET_LINES=5
  
  # Run command and verify Rust binary received these env vars
  # (Check behavior changes based on these vars)
}
```

**Mitigation:** None needed - all wrappers inherit environment ✅

---

## Vector 10: Wrapper "--" Argument Handling

**Priority:** P1 (HIGH)

**Affected Contract:** ARG-PASS-001

**Issue:** Some wrappers strip leading `--` separator, others don't.

**Evidence:**
```perl
# Perl (safe_run.pl:133-136)
my @args = @ARGV;
if (@args > 0 && $args[0] eq '--') {
    shift @args;  # Strip --
}

# Python (safe-run.py:119-121)
args = sys.argv[1:]
if args and args[0] == "--":
    args = args[1:]  # Strip --
```

**Bash and PowerShell also strip `--`.**

**Question:** Why? The contract says pass args without modification.

**Possible Reason:** Shell conventions use `--` to mark end of options. Rust binary may not expect it.

**Test Case to Add:**
```bash
# Does Rust binary handle -- correctly?
./safe-run.sh -- echo test  # Should work
./safe-run.sh echo -- test  # Should pass -- as arg to echo
```

**Mitigation:**
- **If Rust expects no --:** Current behavior is correct
- **If Rust handles --:** Remove the stripping logic
- **Document:** Clarify in contract whether `--` is stripped

---

## Vector 11: Test Isolation (Working Directory)

**Priority:** P0 (CRITICAL)

**Affected Contract:** TEST-INVOKE-001

**Issue:** PowerShell tests MUST run from within repository due to `Get-Location` usage.

**Impact:**
- Cannot run PowerShell tests in isolated /tmp directory
- Tests may interfere with each other if they modify repo files
- CI must ensure proper working directory

**Current CI Configuration:**
```yaml
# .github/workflows/test-powershell.yml:53-55
- name: Run PowerShell tests
  shell: pwsh
  working-directory: wrappers/powershell
```

**✅ CI already sets working directory correctly**

**Test Case to Add:**
```powershell
Describe "Test isolation" {
  It "creates isolated temp directory for artifacts" {
    # Each test should use unique temp dir
    # No test should write to repo .agent/FAIL-LOGS/
  }
}
```

**Mitigation:**
- Fix Vector 1 (PowerShell repo root detection) to use script location
- Then tests can run from anywhere

---

## Vector 12: Concurrent Invocation Safety

**Priority:** P2 (MEDIUM)

**Affected Contract:** ARTIFACT-GEN-001 (implicit)

**Issue:** Multiple simultaneous wrapper invocations should not interfere with each other.

**Test Cases:**
- Parallel safe-run invocations in same directory
- Should create separate log files (timestamp + PID makes them unique)
- No race conditions in directory creation

**Current Implementation:** Rust binary handles uniqueness via timestamp + PID

**Test Case to Add:**
```bash
test_concurrent_invocations() {
  # Launch 10 simultaneous wrapper invocations
  for i in {1..10}; do
    ./safe-run.sh bash -c "sleep 0.1; exit 1" &
  done
  wait
  
  # Should have exactly 10 distinct log files
  count=$(ls .agent/FAIL-LOGS/*.log | wc -l)
  [[ "$count" -eq 10 ]]
}
```

**Mitigation:** None needed (Rust handles it), but test should verify.

---

## Vector 13: Large Output Handling

**Priority:** P2 (MEDIUM)

**Affected Contract:** Implicit performance requirement

**Issue:** Very large output (GB-sized) should not cause wrapper to hang or run out of memory.

**Current Implementation:**
- Bash/Perl/Python: Use `exec`, so wrapper process is replaced → no memory issue
- PowerShell: Uses `& $binary` → wrapper stays alive → could be memory issue? Need to test.

**Test Case:**
```bash
# Generate 100MB of output
./safe-run.sh bash -c 'for i in {1..1000000}; do echo "line $i"; done; exit 1'
# Should complete without OOM
```

**Mitigation:** PowerShell tests already include large output test (200k lines) ✅

---

## Summary of Risk Vectors

| ID | Vector | Priority | Wrapper Affected | Needs Fix |
|----|--------|----------|------------------|-----------|
| 1 | PowerShell repo root uses working dir | P0 | PowerShell | ✅ YES |
| 2 | SAFE_RUN_BIN validation | P0 | All | ❌ No (compliant) |
| 3 | PowerShell $LASTEXITCODE null handling | P0 | PowerShell | ✅ YES |
| 4 | Argument quoting edge cases | P0 | All | 🔍 Test needed |
| 5 | Platform detection accuracy | P1 | All | 🔍 Test needed |
| 6 | PowerShell PS 5.1 platform vars | P1 | PowerShell | ✅ YES |
| 7 | Signal exit code mapping | P1 | All | 🔍 Test needed |
| 8 | Binary .exe extension on Windows | P1 | Bash/Perl/Python | 🔍 Test needed |
| 9 | Environment variable inheritance | P0 | All | ❌ No (compliant) |
| 10 | "--" argument handling | P1 | All | 📝 Document |
| 11 | Test working directory isolation | P0 | PowerShell | ✅ YES (fix Vector 1) |
| 12 | Concurrent invocation safety | P2 | All | 🔍 Test needed |
| 13 | Large output handling | P2 | PowerShell | ❌ No (tested) |

**Fix Priority:**
1. **P0 Immediate:** Vector 1, 3, 11 (PowerShell issues)
2. **P0 Test & Validate:** Vector 4, 9
3. **P1 Test & Validate:** Vector 5, 6, 7, 8
4. **P2 Nice to Have:** Vector 12, 13

**Next Phase:** Reproduce P0 vectors in isolation with instrumentation.
