# Test Runner Contract - Phase 5

**Status:** Active - Phase 5 Implementation
**Last Updated:** 2025-12-29
**Purpose:** Define strict behavioral equivalence for language-native test runners

## Overview

This document defines the contract that all language-native test runners (`run_tests.py`, `RunTests.ps1`, `run_tests.pl`) must follow to maintain strict parity with the existing Bash `run-tests.sh` runners.

**Key Principle:** All test runners must be **functionally equivalent** - same behavior, exit codes, environment setup,
and output conventions, regardless of implementation language.

---

## Current State: Bash `run-tests.sh` Behavior

Each wrapper language currently has a Bash-based test runner:

- `wrappers/python3/run-tests.sh`
- `wrappers/perl/run-tests.sh`
- `wrappers/bash/run-tests.sh`
- `wrappers/powershell/RunTests.ps1` (native PowerShell, already exists)

### Common Behavior Across Bash Runners

#### 1. Environment Setup

**Repository Root Detection:**

- All runners compute repository root: `REPO_ROOT="$(cd "$ROOT/../.." && pwd)"`
- Repo root is 2 levels up from wrapper directory

**SAFE_RUN_BIN Environment Variable:**

- All runners set: `export SAFE_RUN_BIN="${SAFE_RUN_BIN:-$REPO_ROOT/rust/target/release/safe-run}"`
- Default location: `rust/target/release/safe-run` (relative to repo root)
- User can override via environment variable before running tests
- This variable is used by wrapper scripts to locate the Rust canonical binary

**Working Directory:**

- All runners change to wrapper directory: `cd "$ROOT"`
- Tests run from wrapper directory context

#### 2. Test Discovery and Execution

**Python3 (`wrappers/python3/run-tests.sh`):**

- Discovers: `tests/test_*.py` files (snake_case per Phase 4)
- Execution: Uses Python `unittest` framework with custom importlib loader
- Reason for custom loader: Explicit control over test discovery
- Verbosity: `verbosity=2` (shows individual test names and results)

**Perl (`wrappers/perl/run-tests.sh`):**

- Discovers: `tests/*.t` files
- Execution: Uses `prove -v -I tests/lib tests/*.t` (preferred) or falls back to `perl -I tests/lib <file>`
- TAP harness: `prove` provides Test Anything Protocol output
- Library path: `-I tests/lib` includes test helpers

**Bash (`wrappers/bash/run-tests.sh`):**

- Makes scripts executable: `chmod +x scripts/*.sh tests/*.sh tests/run-all.sh`
- Delegates: `exec tests/run-all.sh`
- Discovery (in run-all.sh): Runs all `test-*.sh` files in tests/ directory

**PowerShell (`wrappers/powershell/RunTests.ps1`):**

- Discovers: `tests/*Tests.ps1` files (PascalCase per Phase 4 naming)
- Execution: Uses Pester v5+ framework
- Verbosity: 'Detailed' (shows test names and results)
- Test discovery override: Explicitly resolves files matching `*Tests.ps1` pattern

#### 3. Exit Codes

**Standard exit codes (all runners):**

- `0` - All tests passed
- `1` - One or more tests failed
- `2` - Prerequisites not met (optional, used by PowerShell for missing pwsh/Pester)

**Exit code determination:**

- Python: `sys.exit(1)` if `not result.wasSuccessful()`
- Perl: `prove` exits 1 on failure; shell `for` loop continues but doesn't capture exit code properly
- Bash: Inherits exit code from `tests/run-all.sh` via `exec`
- PowerShell: `exit 1` if `$res.FailedCount -gt 0`

#### 4. Output Conventions

**Stdout/Stderr:**

- Test framework output (unittest, prove, Pester) goes to stdout
- Progress messages ("Running tests...", "Python: 3.11") go to stdout
- Error messages for missing prerequisites go to stderr

**Output verbosity:**

- All runners use verbose/detailed mode to show individual test names
- Helps with debugging in CI logs

#### 5. Required Tools

**Python3:**

- Python 3.8+ required
- unittest (standard library, no installation needed)

**Perl:**

- Perl 5.10+ required
- prove (typically included with Perl, part of Test::Harness)
- Fallback: Direct perl execution if prove not found

**Bash:**

- Bash 4.0+ (Linux), 3.2+ (macOS)
- Standard Unix utilities (chmod, cd, pwd)

**PowerShell:**

- pwsh (PowerShell 7+) required
- Pester module required (installation instructions provided if missing)

#### 6. Platform Compatibility

**All runners support:**

- Linux (primary CI platform)
- macOS (local development)
- Windows (Git Bash, WSL for Bash runners; native PowerShell for RunTests.ps1)

---

## Parity Requirements for Language-Native Runners

### Functional Equivalence Contract

All language-native test runners must:

1. **Set SAFE_RUN_BIN environment variable**
   - Detect repository root (2 levels up from wrapper directory)
   - Default to `{repo_root}/rust/target/release/safe-run`
   - Allow override via pre-existing `SAFE_RUN_BIN` environment variable

2. **Use language-specific test framework**
   - Python: unittest (matches existing run-tests.sh)
   - Perl: Test::Harness (prove) or direct perl execution
   - PowerShell: Pester (already implemented)

3. **Discover tests with correct pattern**
   - Python: `tests/test_*.py` (snake_case, will match Phase 4 naming after transition)
   - Perl: `tests/*.t` (standard Perl test extension)
   - PowerShell: `tests/*Tests.ps1` (PascalCase, matches Phase 4 naming)

4. **Exit with standard codes**
   - 0 = all tests passed
   - 1 = one or more tests failed
   - 2 = prerequisites not met (optional, recommended for clarity)

5. **Run from wrapper directory OR repo root**
   - Must work when executed from wrapper directory: `cd wrappers/python3 && python3 run_tests.py`
   - Must work when executed from repo root: `python3 wrappers/python3/run_tests.py`
   - Absolute path resolution required

6. **Provide actionable error messages**
   - Missing prerequisites: Clear installation instructions
   - No tests found: Explicit error message
   - Test failures: Delegate to test framework output

7. **Match output verbosity**
   - Show individual test names and results
   - Match style of existing Bash runner for that language
   - Helps with debugging in CI logs

### CLI Interface Parity

**No command-line arguments required:**

- All runners currently take no arguments
- Future enhancement: Could add flags like `--verbose`, `--filter`, but not required for Phase 5

**Environment variables:**

- `SAFE_RUN_BIN` - Override binary path (all runners must respect this)

---

## Implementation Strategy: Thin Wrappers vs Native

**Phase 5 Decision:** Start with thin wrappers around existing Bash `run-tests.sh`

**Rationale:**

- Minimizes drift between Bash and native runners
- Reduces implementation complexity
- Maintains proven test discovery and execution logic
- Easy to verify parity (both call same underlying script)

**Implementation approach:**

1. Language-native runner sets up environment (`SAFE_RUN_BIN`, working directory)
2. Language-native runner invokes `run-tests.sh` via subprocess
3. Language-native runner forwards exit code
4. Language-native runner provides language-specific error handling (e.g., check for bash availability)

**Future migration path (documented in future-work.md):**

- Option to migrate to fully native implementations later
- Pros: No bash dependency, language-specific test discovery optimizations
- Cons: More code to maintain, risk of drift
- Decision deferred until there's a strong reason to migrate

---

## Naming Conventions (Per Phase 4 Standards)

**File naming:**

- Python: `run_tests.py` (snake_case per PEP 8)
- PowerShell: `RunTests.ps1` (PascalCase, already exists)
- Perl: `run_tests.pl` (snake_case, aligned with Phase 5.5 Perl naming standardization)

**Rationale for Perl choice:**

- Phase 5.5 standardized all Perl scripts to snake_case (e.g., `safe_run.pl`, `safe_check.pl`, `safe_archive.pl`)
- Provides consistency with Python naming and test runner conventions
- Using `run_tests.pl` aligns with the snake_case decision in Phase 5.1.3

**Placement:**

- All runners at wrapper top-level: `wrappers/<lang>/run_tests.py`, `wrappers/<lang>/RunTests.ps1`, `wrappers/<lang>/run_tests.pl`
- Matches existing placement of `run-tests.sh` and `RunTests.ps1`

---

## CI Integration Strategy

**Phase 5 approach: Run both Bash and native runners**

**Rationale:**

- Validates parity during transition
- Provides redundancy (if one runner breaks, other still works)
- Builds confidence in native runners

**CI workflow changes:**

- Each wrapper test job runs BOTH:
  1. Existing Bash `run-tests.sh`
  2. New language-native runner
- Both must pass for CI to pass

**Example (Python):**

```yaml
- name: Run Python tests (Bash runner)
  run: bash run-tests.sh

- name: Run Python tests (native runner)
  run: python3 run_tests.py
```

**Future optimization (documented in future-work.md):**

- Once native runners are stable, consider:
  - Running Bash runner only on scheduled/nightly builds
  - Running native runner on all PR/push builds
  - Reduces CI runtime without losing coverage
- Decision deferred to future phase when CI runtime becomes a concern

---

## Success Criteria

**Phase 5 is complete when:**

1. ✅ All three language-native runners exist:
   - `wrappers/python3/run_tests.py`
   - `wrappers/perl/run_tests.pl`
   - `wrappers/powershell/RunTests.ps1` (confirm existing runner has parity)

2. ✅ All runners pass lint checks:
   - Python: flake8, black, pylint
   - Perl: Perl::Critic
   - PowerShell: PSScriptAnalyzer

3. ✅ All runners are functionally equivalent:
   - Same exit codes for pass/fail/error
   - Same environment setup (SAFE_RUN_BIN)
   - Same test discovery behavior
   - Work from both wrapper directory and repo root

4. ✅ CI workflows updated:
   - Each language runs both Bash and native runner
   - Both must pass

5. ✅ Documentation updated:
   - `wrappers/README.md` shows native runner usage
   - `docs/testing/test-runner-contract.md` (this doc) exists
   - `docs/future-work.md` tracks future migration options

6. ✅ Full test suite passes:
   - All wrapper tests pass (bash/perl/powershell/python3)
   - Conformance tests pass
   - CI is green

---

## Reference: Current File Locations

```
wrappers/
├── bash/
│   ├── run-tests.sh              (Bash runner, delegates to tests/run-all.sh)
│   └── tests/run-all.sh          (Actual test orchestrator)
├── perl/
│   └── run-tests.sh              (Bash runner, calls prove)
├── python3/
│   └── run-tests.sh              (Bash runner, calls Python unittest)
└── powershell/
    └── RunTests.ps1              (Native PowerShell runner, calls Pester)
```

**After Phase 5:**

```
wrappers/
├── bash/
│   ├── run-tests.sh              (Bash runner, unchanged)
│   └── tests/run-all.sh          (Actual test orchestrator, unchanged)
├── perl/
│   ├── run-tests.sh              (Bash runner, unchanged)
│   └── run_tests.pl              (NEW: Native Perl runner)
├── python3/
│   ├── run-tests.sh              (Bash runner, unchanged)
│   └── run_tests.py              (NEW: Native Python runner)
└── powershell/
    └── RunTests.ps1              (Native PowerShell runner, confirm parity)
```

---

## Document History

- **2025-12-29:** Created as part of Phase 5, Item 5.1.1-5.1.2
  - Documented existing Bash `run-tests.sh` behavior across all wrappers
  - Defined parity requirements for language-native runners
  - Established thin wrapper implementation strategy
  - Defined naming conventions per Phase 4 standards
