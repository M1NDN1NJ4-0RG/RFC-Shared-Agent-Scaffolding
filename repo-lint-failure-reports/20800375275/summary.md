# Repo Lint Summary

**Workflow Run:** https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/actions/runs/20800375275
**Timestamp:** 2026-01-07 23:51:51 UTC
**Branch:** 286/merge
**Commit:** 6468f7ede9243732aa9ea0a0954bec9861307fb4

## Job Results

| Job | Status |
|-----|--------|
| Auto-Fix: Black | success |
| Detect Changed Files | success |
| Repo Lint: Python | skipped |
| Repo Lint: Bash | skipped |
| Repo Lint: PowerShell | skipped |
| Repo Lint: Perl | skipped |
| Repo Lint: YAML | skipped |
| Repo Lint: Rust | failure |
| Vector Tests: Conformance | skipped |

## Rust Linting Failures

```
🔍 Running repository linters and formatters...


                       Linting Results

  Runner            Status    Files   Violations   Duration
 ───────────────────────────────────────────────────────────
  rustfmt           ❌ FAIL       -           20          -
  clippy            ✅ PASS       -            0          -
  rust-docstrings   ✅ PASS       -            0          -


                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                rustfmt Failures
  Found 20 violation(s)


  File   Line   Message
 ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  .         -   Diff in /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/rust/crates/bootstrap-repo-cli/tests/parity_tests.rs:25:
  .         -   //! cargo test --test parity_tests
  .         -   //! ```
  .         -   -use std::process::Command;
  .         -   use std::path::PathBuf;
  .         -   +use std::process::Command;
  .         -   /// Get repository root for test execution
  .         -   fn repo_root() -> PathBuf {
  .         -   Diff in /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/rust/crates/bootstrap-repo-cli/tests/parity_tests.rs:80:
  .         -   !rust_output.stdout.is_empty(),
  .         -   "Rust --version produced no output"
  .         -   );
  .         -   -
  .         -   +
  .         -   // NOTE: Bash bootstrapper does not support --version flag
  .         -   // This is an expected behavioral difference - Rust adds version support
  .         -   // which is a usability improvement over the Bash version
  .         -   Diff in /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/rust/crates/bootstrap-repo-cli/tests/parity_tests.rs:105:
  .         -   "Rust --help failed with: {}",
  .         -   String::from_utf8_lossy(&rust_output.stderr)


           Summary
  Total Runners: 3
    Passed: 2
    Failed: 1
  Total Violations: 20

  Exit Code: 1 (VIOLATIONS)

```

