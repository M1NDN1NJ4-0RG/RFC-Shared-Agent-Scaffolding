# Technical Analysis: `bootstrap-repo-lint-toolchain.sh`

## Executive Summary

The bootstrap script orchestrates installation of development toolchains (Python, Shell, PowerShell, Perl) plus required utilities (actionlint, ripgrep) to establish a reproducible development environment. After Phase 2 hardening, all critical external commands use deterministic exit codes via fail-fast wrappers, eliminating silent failures and partial-install states.

**Key characteristics:**
- **Deterministic failure:** All critical paths exit via `die()` with documented exit codes
- **Idempotent:** Safe to re-run; detects existing installs and skips them
- **Cross-platform:** macOS (Homebrew) and Linux (apt/snap) support
- **Strict activation:** Virtual environment activation failures are fatal

---

## Control Flow Architecture

### Phase Sequence

```
1. Preflight
   ├── Repository discovery (walk upward from CWD)
   ├── Exit code setup
   └── Usage validation

2. Virtual Environment
   ├── Create .venv if missing
   ├── Activate (strict validation)
   └── Upgrade pip/setuptools/wheel

3. Required Toolchains (Always)
   ├── repo-lint package (editable install)
   ├── Python tools (black/ruff/pylint/yamllint/pytest)
   ├── actionlint (via Homebrew or go install)
   └── ripgrep (REQUIRED - no fallback)

4. Optional Toolchains (Flags)
   ├── Shell (--shell): shellcheck, shfmt
   ├── PowerShell (--powershell): pwsh, PSScriptAnalyzer
   └── Perl (--perl): Perl::Critic, PPI via cpanm

5. Verification Gate
   ├── repo-lint doctor (operational self-test)
   └── repo-lint check --ci (lint validation)
```

### Function Call Graph

```
main()
├── find_repo_root()
├── validate_install_target()
├── create_venv()
├── activate_venv()
│   └── die() if activation fails
├── install_repo_lint()
│   ├── run_or_die() for pip upgrade
│   └── run_or_die() for editable install
├── install_python_dev_tools()
│   └── safe_version() for each tool
├── install_actionlint()
│   ├── run_or_die() for all install steps
│   └── safe_version() for version display
├── install_rgrep()
│   └── run_or_die() with exit 21
├── [optional] install_shell_tools()
│   └── safe_version() for tools
├── [optional] install_powershell_tools()
│   ├── run_or_die() for all apt/wget/dpkg
│   └── trap cleanup for temp files
├── [optional] install_perl_tools()
│   ├── try_run() for cpanm installs
│   └── die() if any failed_tools[]
└── run_verification_gate()
    ├── repo-lint doctor (exit 0-1 acceptable)
    └── repo-lint check --ci (exit 0-1 acceptable)
```

---

## Exit Code Contract

All exit codes are deterministic and documented:

| Code | Trigger | Message Pattern |
|------|---------|----------------|
| 0 | Success | All components installed |
| 1 | Usage error | Invalid arguments |
| 10 | Environment | Not in a git repository |
| 11 | Environment | Virtual environment activation failed |
| 12 | Prerequisites | No valid install target (no pyproject.toml) |
| 13 | Installation | repo-lint pip upgrade failed |
| 14 | Installation | repo-lint editable install failed |
| 15 | Installation | Python dev tools installation failed |
| 16 | Installation | Shell toolchain installation failed |
| 17 | Installation | PowerShell toolchain installation failed |
| 18 | Installation | Perl toolchain installation failed |
| 19 | Verification | Verification gate failed |
| 20 | Installation | actionlint installation failed |
| 21 | Installation | ripgrep installation failed (REQUIRED) |

**Exit code enforcement:**
- All critical commands wrapped via `run_or_die(exit_code, message, command...)`
- `set -euo pipefail` ensures pipeline failures propagate
- Optional steps use `try_run()` to avoid terminating on non-critical failures

---

## Fail-Fast Mechanisms

### Core Helpers

**`die(message, exit_code)`**
- Prints `[bootstrap][ERROR] $message`
- Exits with specified code
- All failure paths terminate here

**`run_or_die(exit_code, message, command...)`**
- Executes command
- On failure: calls `die(message, exit_code)`
- Ensures external commands never escape with arbitrary codes

**`try_run(command...)`**
- Executes command
- Captures exit code but does not terminate
- Used for: optional detection, fallback attempts

**`safe_version(command)`**
- Executes version command
- Returns output or empty string (never fails)
- Protected from `pipefail` killing the script

### `set -euo pipefail` Interaction

**Benefits:**
- Catches unhandled failures immediately
- Prevents undefined variable usage
- Propagates pipeline failures

**Risks (now mitigated):**
- Version parsing pipelines could terminate script → Fixed via `safe_version()`
- Optional tool detection could be fatal → Fixed via `try_run()`
- External command failures bypass custom codes → Fixed via `run_or_die()`

---

## Toolchain Installation Strategies

### macOS (Homebrew)

**Pattern:**
```bash
if command -v brew >/dev/null 2>&1; then
    run_or_die EXIT_CODE "Homebrew install failed" brew install TOOL
else
    die "Homebrew not available" EXIT_CODE
fi
```

**Used for:** shellcheck, shfmt, pwsh, actionlint

### Linux (apt)

**Pattern:**
```bash
run_or_die EXIT_CODE "apt update failed" sudo apt-get update
run_or_die EXIT_CODE "install failed" sudo apt-get install -y PACKAGE
```

**Used for:** shellcheck, golang-go (for actionlint), PowerShell prereqs

**Cleanup:** PowerShell uses `trap` to delete downloaded .deb file on exit

### Linux (snap)

**Pattern:**
```bash
if command -v snap >/dev/null 2>&1; then
    run_or_die EXIT_CODE "snap install failed" sudo snap install TOOL --classic
fi
```

**Used for:** shellcheck (fallback), shfmt (fallback)

### go install

**Pattern:**
```bash
export PATH="$HOME/go/bin:$PATH"
run_or_die 20 "go install failed" go install github.com/rhysd/actionlint/cmd/actionlint@v1.7.10
```

**Pinned version:** v1.7.10 for reproducibility

### Perl (cpanm)

**Pattern:**
```bash
failed_tools=()
if ! cpanm --local-lib=~/perl5 Perl::Critic; then
    failed_tools+=("Perl::Critic")
fi
if [ ${#failed_tools[@]} -gt 0 ]; then
    die "Perl toolchain incomplete" 18
fi
```

**Error aggregation:** Attempts all installs before failing

---

## Virtual Environment Activation (Strict)

**Before Phase 2:**
- Activation mismatch was warn-only
- Risk: installs into wrong Python environment

**After Phase 2:**
- Activation mismatch is **fatal** (exit 11)
- Verification: `command -v python3` must equal `$venv_path/bin/python3`

**Rationale:**
- Prevents silent corruption of system Python
- Ensures reproducible installs
- Catches PATH configuration errors early

---

## Verification Gate Semantics

**Two-phase validation:**

1. **`repo-lint doctor`** (operational self-test)
   - Exit 0: Perfect health
   - Exit 1: Config/path issues but tools functional (acceptable)
   - Exit 2+: Critical toolchain failures (fatal)

2. **`repo-lint check --ci`** (lint validation)
   - Exit 0: No violations
   - Exit 1: Violations found but tools work (acceptable)
   - Exit 2: Missing tools (fatal)
   - Exit 3+: Other errors (fatal)

**Why accept exit 1:**
- Tools are functional (bootstrap succeeded)
- Violations are repo state issues, not toolchain issues
- Distinguishes operational failures from lint findings

---

## Remaining Edge Cases

### Network Failures
- No retry logic
- Transient network errors cause immediate failure
- **Risk:** Flaky CI on package manager refreshes

### Permission Issues
- Assumes user can `sudo` for apt/snap
- No preflight permission check
- **Risk:** Partial install if sudo fails mid-run

### Concurrent Runs
- No locking mechanism
- Multiple simultaneous bootstraps could conflict
- **Risk:** Race conditions on .venv creation, package manager locks

### PATH Mutations
- Exports `PATH` in current shell only
- New shells require re-activation or re-bootstrap
- **Impact:** Documented but can surprise users

### Homebrew Availability
- macOS path requires Homebrew present
- No automatic Homebrew installation
- **Impact:** Clear error message directs user to install Homebrew

### Shell Assumptions
- Requires Bash (uses `[[`, `${var}` syntax)
- Not POSIX sh compatible
- **Impact:** Documented in shebang (`#!/usr/bin/env bash`)

---

## Security Considerations

### Command Injection (Mitigated)
- **Before:** Variable expansion in `safe_version("$tool --version")`
- **After:** Explicit hardcoded commands per tool
- **Pattern:** Each tool has dedicated case branch with literal command

### Temp File Cleanup
- PowerShell .deb file cleaned via `trap`
- Ensures no leftover artifacts on failure

### Version Pinning
- actionlint: v1.7.10 (pinned)
- Other tools: latest from package manager
- **Tradeoff:** Reproducibility vs staying current

### Download Verification
- No checksum validation for direct downloads
- Relies on package manager signatures (brew/apt)
- **Risk:** Supply chain attacks on direct downloads

---

## Testing Strategy

**Test suite:** `scripts/tests/test_bootstrap_repo_lint_toolchain.py`

**Coverage:**
- Exit code 10: Not in repository
- Exit code 12: No pyproject.toml
- Exit code 20: actionlint failure paths (verification test)
- Exit code 21: ripgrep failure paths (verification test)
- Repository discovery from subdirectory
- Idempotency (re-run safety)

**Testing gaps:**
- No integration tests for actual package manager calls
- No failure injection for network/permission errors
- Relies on verification tests (check script content) rather than execution

---

## Performance Characteristics

**Sequential execution:**
- All installs run serially
- No parallelization of independent tools
- **Typical runtime:** 2-5 minutes (varies by network/cache)

**Bottlenecks:**
- Package manager metadata refresh (apt update)
- Python package downloads (pip install)
- go install compilation (actionlint)

**Optimization opportunities:**
- Parallel tool downloads
- Cached package metadata
- Pre-compiled binaries vs go install

---

## Maintenance Burden

**High-touch areas:**
- OS-specific install logic (macOS vs Linux divergence)
- Package manager version differences
- Dependency hell for Perl modules

**Complexity drivers:**
- String processing for version extraction
- PATH manipulation across platforms
- Error aggregation for Perl installs

**Technical debt:**
- Bash string manipulation is verbose and error-prone
- No structured logging (grep-unfriendly for CI analysis)
- Limited composability (functions tightly coupled to global state)

---

## Migration Readiness

**What works well (preserve):**
- Clear phase separation
- Deterministic exit codes
- Idempotent design

**What needs improvement:**
- Structured logging for machine parsing
- Parallel execution where safe
- Better progress indication
- Retry logic for transient failures
- Self-contained binary (no bash dependency)

**Migration risks:**
- Behavior parity validation (must match existing contract)
- CI integration (must work headless)
- User migration path (fallback to bash during transition)
