# Contract Extraction: Complete Behavioral Requirements

**Purpose:** This document extracts every explicit behavioral contract from the RFC and documentation, mapping each to implementation locations across all four wrappers.

**Source Documents:**
- `rfc-shared-agent-scaffolding-v0.1.0.md`
- `docs/usage/conformance-contract.md`
- `docs/architecture/wrapper-discovery.md`
- `docs/architecture/rust-canonical-tool.md`
- `conformance/vectors.json`

---

## 1. Binary Discovery Contract

### Contract ID: BIN-DISC-001
**Source:** `docs/architecture/wrapper-discovery.md:9-74`

**Contract:** Wrappers MUST attempt to locate the Rust binary in the following deterministic order:

1. **`SAFE_RUN_BIN` environment variable** (if set, use without validation)
2. **`./target/release/safe-run`** (dev mode, relative to repo root)
   - Note: The docs say `./target/release/<tool>` but implementation uses `./rust/target/release/safe-run`
3. **`./dist/<os>/<arch>/safe-run[.exe]`** (CI artifacts)
   - Platform paths:
     - Linux: `./dist/linux/x86_64/safe-run`
     - macOS Intel: `./dist/macos/x86_64/safe-run`
     - macOS ARM: `./dist/macos/aarch64/safe-run`
     - Windows: `./dist/windows/x86_64/safe-run.exe`
4. **PATH lookup** (system installation)
5. **Fail with exit 127** and actionable error message

**Implementation Locations:**
- Bash: `wrappers/bash/scripts/safe-run.sh:54-84`
- Perl: `wrappers/perl/scripts/safe-run.pl:71-103`
- Python3: `wrappers/python3/scripts/safe_run.py:58-89`
- PowerShell: `wrappers/powershell/scripts/safe-run.ps1:63-102`

**Potential Drift Vectors:**
- **P0: Path resolution relative to script vs working directory** - If wrapper is invoked from outside repo, repo root detection may fail
- **P0: SAFE_RUN_BIN validation** - Spec says "use without validation", wrappers should not check if file exists
- **P1: Platform detection accuracy** - Architecture detection may differ between languages (x86_64 vs amd64, arm64 vs aarch64)
- **P2: Binary extension on Windows** - PowerShell must handle `.exe`, others should handle both with/without

---

## 2. Repository Root Detection

### Contract ID: REPO-ROOT-001
**Source:** Implicit from wrapper implementations

**Contract:** Wrappers MUST locate the repository root by:
1. Starting from script location or current working directory
2. Walking up directory tree looking for:
   - `rfc-shared-agent-scaffolding-v0.1.0.md` OR
   - `.git` directory
3. Stopping at filesystem root if not found

**Implementation Locations:**
- Bash: `wrappers/bash/scripts/safe-run.sh:18-30`
- Perl: `wrappers/perl/scripts/safe-run.pl:21-37`
- Python3: `wrappers/python3/scripts/safe_run.py:21-32`
- PowerShell: `wrappers/powershell/scripts/safe-run.ps1:23-44`

**Potential Drift Vectors:**
- **P0: Working directory vs script location** - PowerShell uses `Get-Location` (working dir), others use script location
  - **This is a CRITICAL difference!** PowerShell wrapper will fail if script is copied to temp dir
- **P1: Symlink handling** - Different behaviors for symlinked wrapper scripts
- **P2: Case sensitivity** - Windows path comparisons may be case-insensitive

---

## 3. Argument Pass-Through Contract

### Contract ID: ARG-PASS-001
**Source:** `docs/architecture/wrapper-discovery.md:105-135`

**Contract:** Wrappers MUST:
1. Pass all arguments to Rust binary without modification or interpretation
2. NOT parse arguments (e.g., --help)
3. NOT add arguments
4. Preserve exact quoting and escaping

**Contract:** Wrappers MUST invoke with `run` subcommand:
```
$BINARY run "$@"
```

**Implementation Locations:**
- Bash: `wrappers/bash/scripts/safe-run.sh:113` - uses `exec "$BINARY" run "$@"`
- Perl: `wrappers/perl/scripts/safe-run.pl:140` - uses `exec($binary, 'run', @args)`
- Python3: `wrappers/python3/scripts/safe_run.py:126` - uses `os.execvp(binary, [binary, "run"] + args)`
- PowerShell: `wrappers/powershell/scripts/safe-run.ps1:140` - uses `& $binary run @invokeArgs`

**Potential Drift Vectors:**
- **P0: Quoting/escaping edge cases** - Complex args with spaces, quotes, backslashes may differ
- **P1: Empty arguments** - `cmd "" "arg2"` should preserve empty string
- **P1: Special characters** - Shell metacharacters, newlines, null bytes
- **P2: Argument count limits** - Very long argument lists may hit platform limits differently

---

## 4. Exit Code Forwarding Contract

### Contract ID: EXIT-CODE-001
**Source:** `docs/architecture/wrapper-discovery.md:138-156`, `docs/usage/conformance-contract.md:90-111`

**Contract:** Wrappers MUST preserve the exit code from the Rust binary exactly:
- **Normal exit:** code 0-255 → forward as-is
- **Signal termination (Unix):** signal S → exit code (128 + S)
  - SIGTERM (15) → 143
  - SIGINT (2) → 130
  - SIGKILL (9) → 137
- **Windows termination:** preserve Windows exit codes as-is

**Implementation Locations:**
- Bash: `wrappers/bash/scripts/safe-run.sh:113` - uses `exec` (replaces process, automatic)
- Perl: `wrappers/perl/scripts/safe-run.pl:140` - uses `exec` (replaces process, automatic)
- Python3: `wrappers/python3/scripts/safe_run.py:126` - uses `os.execvp` (replaces process, automatic)
- PowerShell: `wrappers/powershell/scripts/safe-run.ps1:140-146` - uses `& $binary` then `exit $LASTEXITCODE`

**Potential Drift Vectors:**
- **P0: PowerShell exit code capture** - $LASTEXITCODE may be null or incorrect if command fails to execute
- **P0: Signal exit codes** - Platform differences in signal number → exit code mapping
- **P1: Non-exec wrapper paths** - If wrapper doesn't use exec, it must manually forward exit code
- **P2: Exit code range** - Values >255 may wrap on some platforms

---

## 5. Error Handling Contract

### Contract ID: ERROR-HAND-001
**Source:** `docs/architecture/wrapper-discovery.md:75-101`

**Contract:** If no binary is found, wrapper MUST:
1. Print actionable error message to stderr
2. Exit with code 127 (command not found convention)
3. Include:
   - Searched locations (all 4 paths)
   - Installation instructions
   - Link to documentation

**Implementation Locations:**
- Bash: `wrappers/bash/scripts/safe-run.sh:87-108`
- Perl: `wrappers/perl/scripts/safe-run.pl:108-129`
- Python3: `wrappers/python3/scripts/safe_run.py:95-115`
- PowerShell: `wrappers/powershell/scripts/safe-run.ps1:107-128`

**Potential Drift Vectors:**
- **P1: Error message format consistency** - Messages should be identical across wrappers
- **P1: Exit code on exec failure** - Python has separate handling for FileNotFoundError (127) vs PermissionError (126)
- **P2: Stderr encoding** - UTF-8 encoding may differ on Windows

---

## 6. Output Mode Contract

### Contract ID: OUTPUT-MODE-001
**Source:** `docs/usage/conformance-contract.md:14-88`

**Contract:** The Rust canonical tool (NOT wrappers) MUST support two output modes:

**Default (Event Ledger):** `SAFE_RUN_VIEW` not set or `SAFE_RUN_VIEW=ledger`
- Log file contains split sections: `=== STDOUT ===` and `=== STDERR ===`
- Log file contains event ledger: `--- BEGIN EVENTS ---` ... `--- END EVENTS ---`
- Event format: `[SEQ=<n>][<stream>] <text>`
- Sequence numbers start at 1, monotonically increasing
- Event types: META (start, exit), STDOUT, STDERR

**Merged View:** `SAFE_RUN_VIEW=merged`
- Raw stdout/stderr in temporal order
- No prefixes, no META events
- Interleaved streams

**Wrapper Responsibility:** None - wrappers pass through all env vars to Rust binary

**Implementation Locations:**
- Rust: `rust/src/contract/` (canonical implementation)
- Wrappers: No implementation needed, just pass-through

**Potential Drift Vectors:**
- **P0: Environment variable inheritance** - Wrappers must not strip or modify SAFE_RUN_VIEW
- **P1: None** - This is handled by Rust binary, not wrappers

---

## 7. Artifact Generation Contract

### Contract ID: ARTIFACT-GEN-001
**Source:** `docs/usage/conformance-contract.md:113-146`

**Contract:** Rust canonical tool MUST:
- **Success (exit 0):** No artifacts created
- **Failure (exit ≠ 0):** Create log file in `.agent/FAIL-LOGS/` (or `$SAFE_LOG_DIR`)
- **Filename pattern:** `YYYYMMDDTHHMMSSZ-pid<PID>-FAIL.log` (or `-ABORTED.log` for signals)
- **No-clobber:** Never overwrite existing logs
- **Directory creation:** Create log directory if it doesn't exist

**Wrapper Responsibility:** None - Rust handles artifact generation

**Potential Drift Vectors:**
- **P0: Environment variable pass-through** - Wrappers must pass SAFE_LOG_DIR to Rust binary
- **P1: None** - This is handled by Rust binary

---

## 8. Snippet Lines Contract

### Contract ID: SNIPPET-001
**Source:** `conformance/vectors.json` (safe-run-005)

**Contract:** When `SAFE_SNIPPET_LINES=N` is set and command fails:
- Print last N lines of output to stderr for quick diagnostics
- This is a convenience feature, not strictly required

**Wrapper Responsibility:** None - Rust handles snippet output

**Potential Drift Vectors:**
- **P0: Environment variable pass-through** - Wrappers must pass SAFE_SNIPPET_LINES to Rust binary
- **P1: None** - This is handled by Rust binary

---

## 9. Test Invocation Contract

### Contract ID: TEST-INVOKE-001
**Source:** Test files and CI workflows

**Contract:** Tests MUST:
1. Set `SAFE_RUN_BIN` environment variable to point to Rust binary
2. Invoke wrapper from within repository (for repo root detection)
3. Use isolated temp directories for each test
4. Clean up artifacts after tests

**Implementation Locations:**
- Bash tests: `wrappers/bash/tests/test-safe-run.sh:11-20`
- PowerShell tests: `wrappers/powershell/tests/safe-run-tests.ps1:14-15`

**Potential Drift Vectors:**
- **P0: Working directory for PowerShell tests** - PowerShell wrapper uses Get-Location, tests must be in repo
- **P1: SAFE_RUN_BIN absolute vs relative paths** - Tests should use absolute paths
- **P1: Test isolation** - Each test should use separate temp directory

---

## 10. Platform Detection Contract

### Contract ID: PLATFORM-DET-001
**Source:** Wrapper implementations

**Contract:** Wrappers MUST detect OS and architecture to construct CI artifact path:
- **OS detection:**
  - Linux → `linux`
  - macOS/Darwin → `macos`
  - Windows/MSYS/Cygwin → `windows`
- **Architecture detection:**
  - x86_64/amd64/AMD64 → `x86_64`
  - aarch64/arm64 → `aarch64`

**Implementation Locations:**
- Bash: `wrappers/bash/scripts/safe-run.sh:32-49`
- Perl: `wrappers/perl/scripts/safe-run.pl:42-66`
- Python3: `wrappers/python3/scripts/safe_run.py:34-56`
- PowerShell: `wrappers/powershell/scripts/safe-run.ps1:46-61`

**Potential Drift Vectors:**
- **P1: Architecture naming** - `amd64` vs `x86_64`, `arm64` vs `aarch64` may differ
- **P1: PowerShell platform variables** - `$IsLinux`, `$IsMacOS`, `$IsWindows` may not be set in PS 5.1
- **P2: Unknown platform handling** - Should gracefully skip CI artifact path if detection fails

---

## Contract Coverage Summary

**Total Contracts Identified:** 10

**Contract Ownership:**
- **Wrappers:** 5 contracts (Binary Discovery, Repo Root, Argument Pass-Through, Exit Code, Error Handling)
- **Rust Binary:** 3 contracts (Output Mode, Artifact Generation, Snippet Lines)
- **Tests:** 1 contract (Test Invocation)
- **Shared:** 1 contract (Platform Detection)

**High-Priority Drift Vectors (P0):**
- PowerShell repo root detection uses working directory (not script location) - **CRITICAL**
- SAFE_RUN_BIN validation (spec says no validation)
- Path resolution relative to script vs working directory
- PowerShell exit code capture ($LASTEXITCODE may be null)
- Signal exit codes platform differences
- Environment variable pass-through (SAFE_RUN_VIEW, SAFE_LOG_DIR, SAFE_SNIPPET_LINES)
- Working directory for PowerShell tests

**Next Steps:**
1. ✅ Phase 1 complete: Contracts extracted and documented
2. ⏭️  Phase 2: Create detailed risk vector enumeration with test cases
3. ⏭️  Phase 3: Reproduce each P0 vector in isolation
4. ⏭️  Phase 4: Add/update conformance tests
5. ⏭️  Phase 5: Harden wrappers to fix identified issues
6. ⏭️  Phase 6: Verify CI enforcement
7. ⏭️  Phase 7: Provide evidence and documentation
