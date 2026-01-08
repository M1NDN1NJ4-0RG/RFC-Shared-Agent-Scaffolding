# Future Work / Deferred Ideas Tracker

**Last Updated:** 2025-12-30

This document tracks **explicitly-marked future work** found in the repository. All items are sourced from in-repo TODO
comments, deferred work notes, ignored tests, or documented future enhancement sections.

**Rules:**

- - ✅ Only includes work explicitly marked in code/docs as TODO, deferred, or future work - ❌ Does NOT include
  speculative ideas or undocumented improvements - 🔄 Update this doc when adding new TODOs or completing deferred work

---

## Active Items Summary

| ID | Severity | Area | Title |
| ---- | ---------- | ------ | ------- |
| [FW-001](#fw-001-signal-handling-for-safe-run) | Low | Rust CLI | Signal handling for safe-run (SIGTERM/SIGINT) - ✅ IMPLEMENTED |
| [FW-002](#fw-002-safe-check-subcommand-implementation) | Medium | Rust CLI | safe-check subcommand implementation - ✅ COMPLETE |
| [FW-003](#fw-003-safe-archive-subcommand-implementation) | Medium | Rust CLI | safe-archive subcommand implementation - ✅ COMPLETE |
| [FW-004](#fw-004-preflight-automerge-ruleset-checker) | Medium | Rust CLI | Preflight automerge ruleset checker (preflight-004 + GitHub API mocking) |
| [FW-005](#fw-005-programmatic-vector-to-test-mapping-check) | Low | Conformance | Programmatic vector-to-test mapping check |
| [FW-006](#fw-006-conformance-infrastructure-enhancements) | Low | Conformance | Conformance infrastructure enhancements |
| [FW-007](#fw-007-rust-tool-performance-and-feature-enhancements) | Low | Rust CLI | Rust tool performance and feature enhancements |
| [FW-008](#fw-008-powershell-ctrl-c-signal-behavior) | Low | Wrappers | PowerShell Ctrl-C / signal behavior validation |
| [FW-009](#fw-009-windows-exe-discovery-in-python-wrapper) | Low | Wrappers | Windows .exe discovery in Python wrapper |
| [FW-010](#fw-010-canonical-epic-tracker-placeholder) | Low | Governance | Canonical Epic Tracker placeholder |
| [FW-011](#fw-011-migrate-test-runners-to-fully-native-implementations) | Low | Testing | Migrate test runners to fully native implementations |
| [FW-012](#fw-012-optimize-ci-runtime-with-scheduled-bash-runners) | Low | CI/CD | Optimize CI runtime with scheduled Bash runners |
| [FW-013](#fw-013-make-repo-lint-installable-package) | Low | Tooling | Make repo_lint installable via pip install -e . |
| [FW-014](#fw-014-advanced-repo-local-tool-isolation) | Low | Tooling | Advanced repo-local tool isolation |
| [FW-015](#fw-015-ci-workflow-tool-installation-security-hardening) | Medium | CI/CD | Add checksum/signature verification to tool installation steps |
| [FW-016](#fw-016-ci-log-capture-retention-and-debug-mode-switch) | Medium | CI/CD | CI log capture + retention + debug-mode switch (repo-stored logs + 90-day prune) |

---

## Detailed Items

### FW-001: Signal handling for safe-run

**Severity:** Low (implementation complete, test incomplete) **Area:** Rust CLI **Status:** ✅ IMPLEMENTED (conformance
test incomplete)

**Implementation Status:**

Signal handling for SIGTERM and SIGINT is **fully implemented** in `rust/src/safe_run.rs`:

- Signal handlers registered for both SIGTERM and SIGINT using `signal_hook::flag::register()`
- ABORTED log file created on signal interruption with full event ledger via `save_log()` function
- - Correct exit codes: 130 for SIGINT, 143 for SIGTERM - Child process properly terminated and output captured on
  signal - Merged view mode supported in ABORTED logs

**Test Status:**

The conformance test `test_safe_run_003_sigterm_aborted` (marked `#[ignore]` in `rust/tests/conformance.rs`) is a placeholder that only validates the vector structure, not actual signal behavior. The test requires implementation of:

- - Spawning safe-run with a long-running child command in a subprocess - Sending SIGTERM or SIGINT to the safe-run
  process - Verifying ABORTED log file creation and content - Validating correct exit code (130 or 143)

**Source:**

- `rust/src/safe_run.rs` (signal handler registration and ABORTED log creation in `execute()` function)
- `rust/tests/conformance.rs` (incomplete test `test_safe_run_003_sigterm_aborted`)
- `conformance/vectors.json` (vector safe-run-003 definition)

**Remaining Work:**

- - Implement complete signal handling test with actual signal delivery
- Remove `#[ignore]` attribute from `test_safe_run_003_sigterm_aborted`
- - Validate behavior on Unix platforms (signal handling is Unix-specific)

---

### FW-002: safe-check subcommand implementation

**Severity:** Medium
**Area:** Rust CLI
**Status:** ✅ Complete - All 3 phases implemented

**Why it exists:**

The `safe-run check` subcommand verifies command availability, repository state, and dependencies without executing commands. All phases have been successfully implemented and tested.

**Implementation Status:**

✅ **Phase 1 Complete** (Command existence check):

- - Command existence check via PATH lookup - Exit code 0 when command is found - Exit code 2 when command is missing -
  Scaffolding error messages removed - Unit tests added for PATH lookup behavior - Supports absolute and relative paths
  - Cross-platform support (Unix and Windows)

✅ **Phase 2 Complete** (Repository and dependency validation):

- - Executable permission verification (Unix) - Repository state validation - Exit code 3 for non-executable files
  (Unix) - Exit code 4 for repository state failures - Meaningful error messages for all failure scenarios - Unit tests
  for Phase 2 functionality

✅ **Phase 3 Complete** (Integration and conformance):

- Conformance vectors added to `conformance/vectors.json` (7 vectors)
- - Full conformance tests implemented - All tests passing (27 total: 8 Phase 1 + 3 Phase 2 + 6 conformance + 10
  pre-existing)

**Source:**

- `rust/src/cli.rs:142-164` (Command definition and docs)
- `rust/src/cli.rs:276-475` (Implementation with all 3 phase features)
- `rust/tests/conformance.rs` (Unit tests: safe_check_tests, safe_check_phase2_tests, safe_check_conformance_tests modules)
- `conformance/vectors.json` (Conformance vectors: safe-check-001 through safe-check-007)

**No remaining work** - FW-002 is complete.

---

### FW-003: safe-archive subcommand implementation

**Severity:** Medium
**Area:** Rust CLI
**Status:** ✅ COMPLETE - All phases implemented

**Implementation Summary:**

The `safe-run archive` subcommand is now fully implemented with all requested features. It creates compressed archives from source directories with no-clobber protection.

**Implemented Features:**

1. 1. **Multiple compression formats:** - tar.gz (gzip compression) - Fast, good compression - tar.bz2 (bzip2
   compression) - Slower, better compression - zip - Cross-platform compatibility

2. 2. **No-clobber semantics:** - Default mode: Auto-suffix (output.1.tar.gz, output.2.tar.gz, etc.)
   - Strict mode: `--no-clobber` flag fails with exit code 40 if destination exists

3. 3. **Exit codes:** - 0: Archive created successfully - 2: Invalid arguments or source not found - 40: No-clobber
   collision in strict mode - 50: Archive creation failed (I/O error)

**Implementation Details:**

- Module: `rust/src/safe_archive.rs`
- - Dependencies added: tar, flate2, bzip2, zip
- CLI integration: `rust/src/cli.rs` with --no-clobber flag support
- - All 4 conformance tests passing

**Documentation:**

- User guide: `docs/usage/safe-archive.md`
- - Examples, use cases, and technical details included - Contract references documented

**Testing:**

- - ✅ test_safe_archive_001_basic - Basic archive creation - ✅ test_safe_archive_002_compression_formats - Multiple
  formats (tar.gz, tar.bz2, zip) - ✅ test_safe_archive_003_no_clobber_auto_suffix - Auto-suffix collision handling - ✅
  test_safe_archive_004_no_clobber_strict - Strict mode collision detection

**Source:**

- `rust/src/safe_archive.rs` - Implementation module
- `rust/src/cli.rs:175-202` - Command definition with --no-clobber flag
- `rust/tests/conformance.rs:535-777` - All tests now passing (no longer ignored)
- `docs/usage/safe-archive.md` - Complete documentation
- `conformance/vectors.json` - Conformance vectors (safe-archive-001 through safe-archive-004)

**No remaining work** - FW-003 is complete.

---

### FW-004: Preflight automerge ruleset checker

**Severity:** Medium
**Area:** Rust CLI
**Status:** Not yet implemented - requires GitHub API mocking

**Why it exists:**

The preflight automerge ruleset checker validates GitHub repository configurations before automated operations. Implementation requires GitHub API integration and mocking infrastructure for testing. Preflight coverage is currently blocked by ignored placeholder tests, and the docs call out `preflight-004` as not yet implemented.

**Source:**

- `rust/tests/conformance.rs:810-922` (placeholder tests with TODO comments)
- `rust/tests/README.md:66` (Vector preflight-004 not yet implemented)
- `rust/tests/conformance-infrastructure.md:62` (preflight-004 status)

**Ignored tests:**

- `test_preflight_001_success` (lines 838-853)
- `test_preflight_002_auth_failure` (lines 873-888)
- `test_preflight_003_ruleset_not_found` (lines 907-922)

**Note:** Vector `preflight-004` exists in `conformance/vectors.json` (lines 264-297) but has no corresponding test function in `rust/tests/conformance.rs`. This is a test coverage gap that should be addressed when implementing FW-005 (vector-to-test mapping check).

**Suggested next steps:**

- Add GitHub API client library (e.g., `octocrab` or `github-rs`)
- Implement API mocking infrastructure for tests (e.g., `wiremock` or `mockito`)
- Define the `preflight-004` vector behavior (and add to `conformance/vectors.json` if missing)
- - Implement ruleset validation logic - Add authentication handling with appropriate error codes
- Remove `#[ignore]` from all preflight tests
- - Document preflight usage and required permissions

---

### FW-005: Programmatic vector-to-test mapping check

**Severity:** Low
**Area:** Conformance
**Status:** TODO - needs build-time or runtime check

**Why it exists:**

Currently, there's no automated verification that every conformance vector in `conformance/vectors.json` has a corresponding test function. This could lead to gaps in test coverage when new vectors are added. A programmatic check would ensure 1:1 mapping between vectors and tests.

**Source:**

- `rust/tests/conformance.rs:939-965` (TODO comments and test stub)

**Suggested next steps:**

- - Implement reflection-based or build-time check for vector coverage - Use macro or build script to verify 1:1 mapping
  - Fail the build/test if vectors exist without corresponding tests - Consider using test generation macros to
  auto-create test stubs - Document the pattern for adding new vector tests

---

### FW-006: Conformance infrastructure enhancements

**Severity:** Low
**Area:** Conformance
**Status:** Future enhancements documented

**Why it exists:**

The conformance infrastructure is functional but has room for quality-of-life improvements that would enhance developer
experience and test reliability.

**Source:**

- `rust/tests/conformance-infrastructure.md:239-245` (Future Enhancements section)

**Proposed enhancements:**

- - Add snapshot update mode (environment variable to regenerate snapshots) - Add test coverage reporting for
  conformance tests - Add benchmark tests for performance validation - Add fuzzing for edge cases (malformed input,
  extreme values) - Add integration tests with wrapper scripts (end-to-end validation)

**Suggested next steps:**

- - Prioritize snapshot update mode (highest developer value)
- Add `SNAPSHOT_UPDATE=1` environment variable support
- Integrate coverage tools (e.g., `cargo-tarpaulin`)
- Evaluate fuzzing frameworks (e.g., `cargo-fuzz`)
- - Create cross-language integration test suite

---

### FW-007: Rust tool performance and feature enhancements

**Severity:** Low
**Area:** Rust CLI
**Status:** Future enhancements documented

**Why it exists:**

The Rust canonical tool works correctly but has opportunities for optimization and feature expansion beyond the current
contract requirements.

**Source:**

- `docs/architecture/rust-canonical-tool.md:165-171` (Future Enhancements section)

**Proposed enhancements:**

- - **Performance:** Optimize buffering and I/O for high-throughput logs
- **Binary size:** Strip debug symbols, optimize for size with `strip = true`
- - **Additional commands:** Extend beyond safe-run/safe-check/safe-archive - **Plugin architecture:** Allow custom
  event handlers for extensibility - **Telemetry:** Optional structured logging for debugging (e.g., tracing crate)

**Suggested next steps:**

- - Profile memory usage with large output volumes - Implement streaming-to-file mode to reduce peak memory (see EPIC 59
  Phase 5) - Evaluate binary size optimizations (LTO, opt-level, panic=abort) - Design plugin/hook system for custom
  event processing - Add opt-in telemetry with structured logging

---

### FW-008: PowerShell Ctrl-C / signal behavior

**Severity:** Low
**Area:** Wrappers
**Status:** Deferred - requires Windows-specific testing

**Why it exists:**

PowerShell Ctrl-C behavior needs validation to ensure contract alignment on Windows platforms. Testing requires native
Windows environment (not WSL/Git Bash). This was Phase 3 of EPIC 59 but was deferred due to lack of Windows testing
infrastructure.

**Source:**

- `EPIC-59-NEXT-STEPS.md:75-102` (Phase 3 deferred)
- `EPIC-59-NEXT-STEPS.md:199-249` (follow-up instructions)

**Why deferred:**

- - Requires Windows-specific testing infrastructure not available in current CI
- Testing Ctrl-C with PowerShell's `Start-Process` vs direct invocation needs native Windows
- Current implementation uses direct invocation (`& $binary`) which should propagate signals
- - This is a polish item, not a critical issue

**Suggested next steps:**

- - Set up Windows testing environment (native Windows 10/11, not WSL)
- Test both direct invocation and `Start-Process` approaches
- - Verify ABORTED log creation on Ctrl-C interruption - Verify exit codes (130 or 143) match Unix behavior
- If limitation found, document in `safe-run.ps1` and `docs/architecture/rust-canonical-tool.md`
- - If behavior is acceptable, document validation results

---

### FW-009: Windows .exe discovery in Python wrapper

**Severity:** Low
**Area:** Wrappers
**Status:** Documented as future/paper-cut

**Why it exists:**

The Python wrapper notes Windows native support as a future improvement: on Windows it should locate `safe-run.exe` during discovery instead of only `safe-run`.

**Source:**

- `wrappers/python3/scripts/safe-run.py:L77-L82`

**Suggested next steps:**

- Detect Windows (`os.name == "nt"` or `platform.system() == "Windows"`)
- Probe `safe-run.exe` in the same cascade as `safe-run`
- - Add a small wrapper-level test (or integration test under conformance infra) that exercises discovery behavior

---

### FW-010: Canonical Epic Tracker placeholder

**Severity:** Low
**Area:** Governance
**Status:** Placeholder exists; canonical location not established

**Why it exists:**

There is an explicit placeholder indicating the need for a canonical epic/idea tracker, but no single authoritative
location is currently defined.

**Source:**

- `.github/copilot-instructions.md:L50-L53`

**Suggested next steps:**

- Define the canonical location (e.g., `docs/future-work.md` or `docs/EPICS.md`)
- Link it from `.github/copilot-instructions.md`
- - Optionally add a GitHub Issue template/category that points back to the canonical doc

---

### FW-011: Migrate test runners to fully native implementations

**Severity:** Low
**Area:** Testing
**Status:** Deferred - thin wrappers sufficient for now

**Why it exists:**

Phase 5 implements language-native test runners (`run_tests.py`, `run_tests.pl`) as **thin wrappers** around the existing Bash `run-tests.sh` scripts. This approach minimizes drift and implementation complexity, but means the runners still depend on Bash being available.

A future enhancement would migrate to **fully native implementations** where each runner directly invokes its language's
test framework without calling the Bash script.

**Current Implementation (Phase 5):**

- Python `run_tests.py` → calls `subprocess.run(['bash', 'run-tests.sh'])`
- Perl `run_tests.pl` → calls `system('bash', 'run-tests.sh')`
- PowerShell `RunTests.ps1` → already fully native (calls Pester directly)

**Future Native Implementation:**

- Python `run_tests.py` → directly uses `unittest.TestLoader()` and runs tests
- Perl `run_tests.pl` → directly invokes `prove` or `perl -I tests/lib tests/*.t`
- PowerShell `RunTests.ps1` → no change (already native)

**Pros of migration:**

- - No Bash dependency (Windows native support without Git Bash/WSL) - Language-specific test discovery optimizations -
  Better error messages in native language

**Cons of migration:**

- - More code to maintain (3 implementations instead of 1) - Risk of behavioral drift between languages - Additional
  testing burden to ensure parity

**Source:**

- `docs/testing/test-runner-contract.md` (Implementation Strategy section)

**Suggested next steps:**

- - Only migrate if there's a strong reason (e.g., Windows users complaining about Bash dependency) - Migrate one
  language at a time (start with Python as proof of concept) - Run both thin wrapper and native implementation in CI
  during transition - Document parity testing strategy

---

### FW-012: Optimize CI runtime with scheduled Bash runners

**Severity:** Low
**Area:** CI/CD
**Status:** Deferred - CI runtime not currently a concern

**Why it exists:**

Phase 5 configures CI to run BOTH the Bash `run-tests.sh` and language-native runners (`run_tests.py`, `run_tests.pl`) for each wrapper language. This provides redundancy and validates parity, but doubles the wrapper test runtime.

If CI runtime becomes excessive (e.g., PR checks take >10 minutes), we could optimize by:

- - Running language-native runners on all PR/push builds (fast feedback) - Running Bash runners only on
  scheduled/nightly builds (coverage safety net)

**Current CI Strategy (Phase 5):**

```yaml
# Each wrapper workflow runs both runners
- name: Run Python tests (Bash runner)
  run: bash run-tests.sh

- name: Run Python tests (native runner)
  run: python3 run_tests.py
```

**Future Optimized Strategy:**

```yaml
# PR/push workflow (fast)
- name: Run Python tests
  run: python3 run_tests.py

# Scheduled/nightly workflow (comprehensive)
- name: Run Python tests (Bash runner)
  run: bash run-tests.sh

- name: Run Python tests (native runner)
  run: python3 run_tests.py
```

**When to implement:**

- - Monitor CI runtime after Phase 5 merges - Threshold: If total CI runtime exceeds 10 minutes consistently -
  Coordinate with team before changing (affects merge requirements)

**Source:**

- `docs/testing/test-runner-contract.md` (CI Integration Strategy section)

**Suggested next steps:**

- - Measure baseline CI runtime after Phase 5 - Set up scheduled/nightly workflow template - Document which runners are
  required for PR merge vs. optional - Consider adding "full test suite" manual trigger for pre-merge validation

---

## Grep Keywords for Future Updates

Use this command to scan for new future work items:

```bash
# Search for common future work markers
grep -rn \
  -e "TODO" \
  -e "FIXME" \
  -e "deferred" \
  -e "not yet implemented" \
  -e "scaffolding only" \
  -e "future PR" \
  -e "future implementation" \
  -e "placeholder" \
  -e "Future Enhancements" \
  -e "Future Work" \
  --include="*.rs" \
  --include="*.md" \
  --include="*.toml" \
  --include="*.sh" \
  --include="*.py" \
  --include="*.pl" \
  --include="*.ps1" \
  --exclude-dir=".git" \
  --exclude-dir="target" \
  --exclude-dir="dist" \
  --exclude-dir="node_modules" \
  .
```

**Note:** This grep command is portable and works on Unix-like systems. For cross-platform compatibility, consider using `ripgrep`:

```bash
rg -n \
 "TODO | FIXME | deferred | not yet implemented | scaffolding only | future (PR | implementation) | placeholder | Future (Enhancements | Work)" \
  -g "*.{rs,md,toml,sh,py,pl,ps1}" \
  --iglob "!target/*" \
  --iglob "!dist/*" \
  --iglob "!node_modules/*"
```

---

## Completion Criteria

**Item is complete when:**

1. 1. Implementation is finished and tested
2. All related `#[ignore]` attributes are removed from tests
3. 3. All related TODO comments are removed from code 4. Documentation is updated to reflect new functionality 5. This
   tracker is updated to remove or mark the item as complete

**When completing items:**

- - Remove the item from this document (or move to a "Completed" section if tracking history is desired) - Update all
  source files to remove TODO/deferred markers - Ensure conformance tests pass - Update relevant documentation (README,
  docs/, RFC, etc.)

---

### FW-013: Make repo_lint installable package

**Severity:** Low
**Area:** Tooling
**Status:** 🔮 DEFERRED

**Description:**

Currently, `repo_lint` is run in-place using `python3 -m tools.repo_lint`. Future work should make it installable as a proper Python package with console script entry points.

**Proposed Changes:**

1. Add `setup.py` or update `pyproject.toml` with package metadata
2. Define console script entry point: `repo-lint` → `tools.repo_lint.cli:main`
3. Support `pip install -e .` for local development
4. 4. Document installation in CONTRIBUTING.md
5. Integrate naming enforcement into `repo_lint` so `python3 -m tools.repo_lint check --ci` also validates repo naming contracts (per `docs/contributing/naming-and-style.md`) and reports violations deterministically.

**Current Workaround:**

Run in-place from repo root:

```bash
python3 -m tools.repo_lint check
python3 -m tools.repo_lint fix
python3 -m tools.repo_lint install
```

**Source:**

- - Decision Item 0.2.2 in EPIC issue (Phase 0 - Execution Model) - Added during Phase 1 implementation

---

### FW-014: Advanced repo-local tool isolation

**Severity:** Low
**Area:** Tooling
**Status:** 🔮 DEFERRED

**Description:**

Phase 4 implements basic repo-local tool installation (`.venv-lint/` for Python tools). Future enhancements could extend this to other languages and add more sophisticated isolation mechanisms.

**Proposed Enhancements:**

1. **PowerShell module isolation (`.psmodules/`):**
   - - Install PSScriptAnalyzer to repo-local directory
   - Use `Import-Module -Path .psmodules/...` instead of system-wide install
   - - Requires PowerShell module path manipulation

2. **Perl CPAN local install (`.cpan-local/`):**
   - Use `local::lib` to install Perl::Critic locally
   - Set PERL5LIB to include `.cpan-local/lib/perl5`
   - - Avoids system-wide CPAN installs

3. **Bash tool binaries (`.tools/`):**
   - - Download pre-built shellcheck binaries - Build shfmt from source or download releases
   - Add `.tools/bin` to PATH during linting

4. 4. **Version lock files:**
   - Create `.tool-versions` or similar lock file
   - - Pin exact versions of all tools (including non-Python)
   - Auto-verify and update on `repo-lint install`

5. 5. **Cleanup improvements:** - Track what was installed where
   - Add `repo-lint install --verify` to check tool integrity
   - Add `repo-lint install --upgrade` to update tools

**Current Implementation (Phase 4):**

- Python tools: Installed in `.venv-lint/` with pinned versions
- - Other tools: Manual installation with printed instructions
- Cleanup: `--cleanup` removes `.venv-lint/`, `.tools/`, `.psmodules/`, `.cpan-local/`

**Source:**

- - Decision Item 0.2.2 in EPIC issue (Phase 0 - Execution Model) - Implemented during Phase 4

---

### FW-015: CI workflow tool installation security hardening

**Severity:** Medium
**Area:** CI/CD
**Status:** 🔮 DEFERRED

**Description:**

Code review identified security hardening opportunities in GitHub Actions workflow tool installation steps. Currently,
workflows download and install tools without checksum verification or signature validation.

**Affected Workflows:**

- `.github/workflows/repo-lint-weekly-full-scan.yml`
- `.github/workflows/repo-lint-and-docstring-enforcement.yml`

**Proposed Security Hardening:**

1. 1. **shfmt binary download (lines 79-82 in weekly workflow, ~449-453 in umbrella):** - Add SHA256 checksum
   verification after download - Verify checksum matches known-good value before installation - Example:

     ```bash
     wget -qO /tmp/shfmt https://github.com/mvdan/sh/releases/download/v3.12.0/shfmt_v3.12.0_linux_amd64

 echo "EXPECTED_SHA256  /tmp/shfmt" | sha256sum -c -
     chmod +x /tmp/shfmt
     sudo mv /tmp/shfmt /usr/local/bin/shfmt
     ```

1. 1. **PowerShell repository setup (lines 85-88 in weekly workflow):** - Add GPG key verification for Microsoft APT
   repository - Verify package signatures before installation - Example:

     ```bash

 wget -qO- <https://packages.microsoft.com/keys/microsoft.asc> | gpg --dearmor > microsoft.gpg
     sudo install -o root -g root -m 644 microsoft.gpg /etc/apt/trusted.gpg.d/
     ```

1. 1. **PSScriptAnalyzer installation (line 95 in weekly workflow):**
   - Consider adding `-SkipPublisherCheck` only when necessary
   - - Verify module publisher/signature when possible - Document why signature checks are skipped if needed

**Current Implementation:**

- - All workflows download tools over HTTPS (transport-level security) - All third-party actions pinned by commit SHA
  (per Phase 0 Item 0.4.2) - No checksum or signature verification for downloaded binaries

**Impact:**

- - Low immediate risk (HTTPS + pinned versions provide basic protection) - Hardening would provide defense-in-depth

**Source:**

- - Code review feedback on PR #137 (2025-12-30) - Applies to both weekly full scan workflow and umbrella workflow

**Related:**

- - Phase 0 Item 0.4.2: Pin third-party actions by commit SHA (COMPLETE) - Phase 0 Item 0.7.1: Pin tool versions in CI
  (COMPLETE)

---

### FW-016: CI log capture, retention, and debug-mode switch

**Severity:** Medium
**Area:** CI/CD
**Status:** 🔮 DEFERRED

**Description:**

We want CI failures (and their forensic context) to be **reviewable from the repository** without requiring
humans/agents to scrape GitHub Actions UI logs.

**Goals:**

1. 1. **Commit log artifacts to the repo** using a consistent directory structure. 2. **Retain failure logs** for up to
   **90 days** (tunable downward if noise/cost warrants). 3. Provide a **debug-mode switch** so a human can re-run a
   workflow with deeper logging when needed.

**Proposed repo log layout (example):**

- `logs/ci/<workflow-name>/<YYYY-MM-DD>/<run-id>/...`

**Retention / pruning policy (starting point):**

- - Automatically prune logs older than **90 days**. - If this becomes too noisy or large, reduce retention (e.g., 30
  days).

**Debug-mode switch (repo-controlled):** GitHub’s UI “Enable debug logging” toggle cannot be enabled programmatically by
workflows, so implement debug mode via one of:

- **Workflow dispatch input** (preferred): `debug_logging: true | false`
- **Separate debug workflow**: e.g., `Umbrella CI (Debug)` / `Repo Lint (Debug)`

When debug mode is enabled, increase verbosity consistently (examples):

- Set `ACTIONS_STEP_DEBUG=true` / `ACTIONS_RUNNER_DEBUG=true` when available (manual rerun input can set these)
- Add verbose flags to tools (`--verbose`, `--debug`, `set -x`, etc.)
- - Ensure debug runs write the expanded logs into the repo log path above

**Auto-rerun-on-failure (optional but desirable):**

- Add orchestration using `workflow_run` (or equivalent) so that when the normal workflow fails, it triggers a debug run against the **same SHA**.
- - Ensure the debug run is the one that writes the *most useful* log output into the repo log directory.

**Why this matters:**

- Humans can quickly review failures via `logs/ci/...`.
- - AI coding agents can be directed at repo-stored log artifacts without API calls. - Failure evidence persists across
  time and is easy to link from PR reviews.

**Notes:**

- - If adopting this repo-log strategy broadly, ensure it does **not** create a bot-commit loop (guardrails needed). -
  Prefer storing logs on failure; if logs are stored on success too, consider much shorter retention.

---

**End of Future Work Tracker**
