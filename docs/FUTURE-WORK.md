# Future Work / Deferred Ideas Tracker

**Last Updated:** 2025-12-27

This document tracks **explicitly-marked future work** found in the repository. All items are sourced from in-repo TODO comments, deferred work notes, ignored tests, or documented future enhancement sections.

**Rules:**
- ✅ Only includes work explicitly marked in code/docs as TODO, deferred, or future work
- ❌ Does NOT include speculative ideas or undocumented improvements
- 🔄 Update this doc when adding new TODOs or completing deferred work

---

## Active Items Summary

| ID | Severity | Area | Title |
|----|----------|------|-------|
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

---

## Detailed Items

### FW-001: Signal handling for safe-run

**Severity:** Low (implementation complete, test incomplete)
**Area:** Rust CLI  
**Status:** ✅ IMPLEMENTED (conformance test incomplete)

**Implementation Status:**

Signal handling for SIGTERM and SIGINT is **fully implemented** in `rust/src/safe_run.rs`:
- Signal handlers registered for both SIGTERM and SIGINT using `signal_hook::flag::register()`
- ABORTED log file created on signal interruption with full event ledger via `save_log()` function
- Correct exit codes: 130 for SIGINT, 143 for SIGTERM
- Child process properly terminated and output captured on signal
- Merged view mode supported in ABORTED logs

**Test Status:**

The conformance test `test_safe_run_003_sigterm_aborted` (marked `#[ignore]` in `rust/tests/conformance.rs`) is a placeholder that only validates the vector structure, not actual signal behavior. The test requires implementation of:
- Spawning safe-run with a long-running child command in a subprocess
- Sending SIGTERM or SIGINT to the safe-run process
- Verifying ABORTED log file creation and content
- Validating correct exit code (130 or 143)

**Source:**
- `rust/src/safe_run.rs` (signal handler registration and ABORTED log creation in `execute()` function)
- `rust/tests/conformance.rs` (incomplete test `test_safe_run_003_sigterm_aborted`)
- `conformance/vectors.json` (vector safe-run-003 definition)

**Remaining Work:**
- Implement complete signal handling test with actual signal delivery
- Remove `#[ignore]` attribute from `test_safe_run_003_sigterm_aborted`
- Validate behavior on Unix platforms (signal handling is Unix-specific)

---

### FW-002: safe-check subcommand implementation

**Severity:** Medium  
**Area:** Rust CLI  
**Status:** ✅ Complete - All 3 phases implemented

**Why it exists:**

The `safe-run check` subcommand verifies command availability, repository state, and dependencies without executing commands. All phases have been successfully implemented and tested.

**Implementation Status:**

✅ **Phase 1 Complete** (Command existence check):
- Command existence check via PATH lookup
- Exit code 0 when command is found
- Exit code 2 when command is missing
- Scaffolding error messages removed
- Unit tests added for PATH lookup behavior
- Supports absolute and relative paths
- Cross-platform support (Unix and Windows)

✅ **Phase 2 Complete** (Repository and dependency validation):
- Executable permission verification (Unix)
- Repository state validation
- Exit code 3 for non-executable files (Unix)
- Exit code 4 for repository state failures
- Meaningful error messages for all failure scenarios
- Unit tests for Phase 2 functionality

✅ **Phase 3 Complete** (Integration and conformance):
- Conformance vectors added to `conformance/vectors.json` (7 vectors)
- Full conformance tests implemented
- All tests passing (27 total: 8 Phase 1 + 3 Phase 2 + 6 conformance + 10 pre-existing)

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

1. **Multiple compression formats:**
   - tar.gz (gzip compression) - Fast, good compression
   - tar.bz2 (bzip2 compression) - Slower, better compression
   - zip - Cross-platform compatibility

2. **No-clobber semantics:**
   - Default mode: Auto-suffix (output.1.tar.gz, output.2.tar.gz, etc.)
   - Strict mode: `--no-clobber` flag fails with exit code 40 if destination exists

3. **Exit codes:**
   - 0: Archive created successfully
   - 2: Invalid arguments or source not found
   - 40: No-clobber collision in strict mode
   - 50: Archive creation failed (I/O error)

**Implementation Details:**

- Module: `rust/src/safe_archive.rs`
- Dependencies added: tar, flate2, bzip2, zip
- CLI integration: `rust/src/cli.rs` with --no-clobber flag support
- All 4 conformance tests passing

**Documentation:**

- User guide: `docs/safe-archive.md`
- Examples, use cases, and technical details included
- Contract references documented

**Testing:**

- ✅ test_safe_archive_001_basic - Basic archive creation
- ✅ test_safe_archive_002_compression_formats - Multiple formats (tar.gz, tar.bz2, zip)
- ✅ test_safe_archive_003_no_clobber_auto_suffix - Auto-suffix collision handling
- ✅ test_safe_archive_004_no_clobber_strict - Strict mode collision detection

**Source:**
- `rust/src/safe_archive.rs` - Implementation module
- `rust/src/cli.rs:175-202` - Command definition with --no-clobber flag
- `rust/tests/conformance.rs:535-777` - All tests now passing (no longer ignored)
- `docs/safe-archive.md` - Complete documentation
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
- `rust/tests/CONFORMANCE_INFRASTRUCTURE.md:62` (preflight-004 status)

**Ignored tests:**
- `test_preflight_001_success` (lines 838-853)
- `test_preflight_002_auth_failure` (lines 873-888)
- `test_preflight_003_ruleset_not_found` (lines 907-922)

**Note:** Vector `preflight-004` exists in `conformance/vectors.json` (lines 264-297) but has no corresponding test function in `rust/tests/conformance.rs`. This is a test coverage gap that should be addressed when implementing FW-005 (vector-to-test mapping check).

**Suggested next steps:**
- Add GitHub API client library (e.g., `octocrab` or `github-rs`)
- Implement API mocking infrastructure for tests (e.g., `wiremock` or `mockito`)
- Define the `preflight-004` vector behavior (and add to `conformance/vectors.json` if missing)
- Implement ruleset validation logic
- Add authentication handling with appropriate error codes
- Remove `#[ignore]` from all preflight tests
- Document preflight usage and required permissions

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
- Implement reflection-based or build-time check for vector coverage
- Use macro or build script to verify 1:1 mapping
- Fail the build/test if vectors exist without corresponding tests
- Consider using test generation macros to auto-create test stubs
- Document the pattern for adding new vector tests

---

### FW-006: Conformance infrastructure enhancements

**Severity:** Low  
**Area:** Conformance  
**Status:** Future enhancements documented

**Why it exists:**

The conformance infrastructure is functional but has room for quality-of-life improvements that would enhance developer experience and test reliability.

**Source:**
- `rust/tests/CONFORMANCE_INFRASTRUCTURE.md:239-245` (Future Enhancements section)

**Proposed enhancements:**
- Add snapshot update mode (environment variable to regenerate snapshots)
- Add test coverage reporting for conformance tests
- Add benchmark tests for performance validation
- Add fuzzing for edge cases (malformed input, extreme values)
- Add integration tests with wrapper scripts (end-to-end validation)

**Suggested next steps:**
- Prioritize snapshot update mode (highest developer value)
- Add `SNAPSHOT_UPDATE=1` environment variable support
- Integrate coverage tools (e.g., `cargo-tarpaulin`)
- Evaluate fuzzing frameworks (e.g., `cargo-fuzz`)
- Create cross-language integration test suite

---

### FW-007: Rust tool performance and feature enhancements

**Severity:** Low  
**Area:** Rust CLI  
**Status:** Future enhancements documented

**Why it exists:**

The Rust canonical tool works correctly but has opportunities for optimization and feature expansion beyond the current contract requirements.

**Source:**
- `docs/rust-canonical-tool.md:165-171` (Future Enhancements section)

**Proposed enhancements:**
- **Performance:** Optimize buffering and I/O for high-throughput logs
- **Binary size:** Strip debug symbols, optimize for size with `strip = true`
- **Additional commands:** Extend beyond safe-run/safe-check/safe-archive
- **Plugin architecture:** Allow custom event handlers for extensibility
- **Telemetry:** Optional structured logging for debugging (e.g., tracing crate)

**Suggested next steps:**
- Profile memory usage with large output volumes
- Implement streaming-to-file mode to reduce peak memory (see EPIC 59 Phase 5)
- Evaluate binary size optimizations (LTO, opt-level, panic=abort)
- Design plugin/hook system for custom event processing
- Add opt-in telemetry with structured logging

---

### FW-008: PowerShell Ctrl-C / signal behavior

**Severity:** Low  
**Area:** Wrappers  
**Status:** Deferred - requires Windows-specific testing

**Why it exists:**

PowerShell Ctrl-C behavior needs validation to ensure contract alignment on Windows platforms. Testing requires native Windows environment (not WSL/Git Bash). This was Phase 3 of EPIC 59 but was deferred due to lack of Windows testing infrastructure.

**Source:**
- `EPIC-59-NEXT-STEPS.md:75-102` (Phase 3 deferred)
- `EPIC-59-NEXT-STEPS.md:199-249` (follow-up instructions)

**Why deferred:**
- Requires Windows-specific testing infrastructure not available in current CI
- Testing Ctrl-C with PowerShell's `Start-Process` vs direct invocation needs native Windows
- Current implementation uses direct invocation (`& $binary`) which should propagate signals
- This is a polish item, not a critical issue

**Suggested next steps:**
- Set up Windows testing environment (native Windows 10/11, not WSL)
- Test both direct invocation and `Start-Process` approaches
- Verify ABORTED log creation on Ctrl-C interruption
- Verify exit codes (130 or 143) match Unix behavior
- If limitation found, document in `safe-run.ps1` and `docs/rust-canonical-tool.md`
- If behavior is acceptable, document validation results

---

### FW-009: Windows .exe discovery in Python wrapper

**Severity:** Low  
**Area:** Wrappers  
**Status:** Documented as future/paper-cut

**Why it exists:**

The Python wrapper notes Windows native support as a future improvement: on Windows it should locate `safe-run.exe` during discovery instead of only `safe-run`.

**Source:**
- `wrappers/scripts/python3/scripts/safe-run.py:L77-L82`

**Suggested next steps:**
- Detect Windows (`os.name == "nt"` or `platform.system() == "Windows"`)
- Probe `safe-run.exe` in the same cascade as `safe-run`
- Add a small wrapper-level test (or integration test under conformance infra) that exercises discovery behavior

---

### FW-010: Canonical Epic Tracker placeholder

**Severity:** Low  
**Area:** Governance  
**Status:** Placeholder exists; canonical location not established

**Why it exists:**

There is an explicit placeholder indicating the need for a canonical epic/idea tracker, but no single authoritative location is currently defined.

**Source:**
- `.github/copilot-instructions.md:L50-L53`

**Suggested next steps:**
- Define the canonical location (e.g., `docs/FUTURE-WORK.md` or `docs/EPICS.md`)
- Link it from `.github/copilot-instructions.md`
- Optionally add a GitHub Issue template/category that points back to the canonical doc

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
  "TODO|FIXME|deferred|not yet implemented|scaffolding only|future (PR|implementation)|placeholder|Future (Enhancements|Work)" \
  -g "*.{rs,md,toml,sh,py,pl,ps1}" \
  --iglob "!target/*" \
  --iglob "!dist/*" \
  --iglob "!node_modules/*"
```

---

## Completion Criteria

**Item is complete when:**
1. Implementation is finished and tested
2. All related `#[ignore]` attributes are removed from tests
3. All related TODO comments are removed from code
4. Documentation is updated to reflect new functionality
5. This tracker is updated to remove or mark the item as complete

**When completing items:**
- Remove the item from this document (or move to a "Completed" section if tracking history is desired)
- Update all source files to remove TODO/deferred markers
- Ensure conformance tests pass
- Update relevant documentation (README, docs/, RFC, etc.)

---

**End of Future Work Tracker**
