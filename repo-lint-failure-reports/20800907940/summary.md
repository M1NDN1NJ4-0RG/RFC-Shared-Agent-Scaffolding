# Repo Lint Summary

**Workflow Run:** https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/actions/runs/20800907940
**Timestamp:** 2026-01-08 00:20:08 UTC
**Branch:** 286/merge
**Commit:** 7a0575b1ac3cc4a1d6eea6ecba98e9749778b58d

## Job Results

| Job | Status |
|-----|--------|
| Auto-Fix: Black | success |
| Detect Changed Files | success |
| Repo Lint: Python | failure |
| Repo Lint: Bash | success |
| Repo Lint: PowerShell | failure |
| Repo Lint: Perl | success |
| Repo Lint: YAML | success |
| Repo Lint: Rust | failure |
| Vector Tests: Conformance | success |

## Python Linting Failures

```
🔍 Running repository linters and formatters...


                        Linting Results

  Runner              Status    Files   Violations   Duration
 ─────────────────────────────────────────────────────────────
  black               ✅ PASS       -            0          -
  ruff                ❌ FAIL       -            1          -
  pylint              ❌ FAIL       -            3          -
  python-docstrings   ✅ PASS       -            0          -


                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 ruff Failures
  Found 1 violation(s)


  File              Line   Message
 ───────────────────────────────────────────────────────────────────────────────────────────
  cli_argparse.py    559   N806 Variable `MAX_AUTO_WORKERS` in function should be lowercase


                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                pylint Failures
  Found 3 violation(s)


  File                Line   Message
 ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  yaml_validator.py     87   R1724: Unnecessary "else" after "continue", remove the "else" and de-indent the code inside it (no-else-continue)
  cli_argparse.py      193   W0511: TODO: Consider removing debug timing mode or making it development-only (fixme)
  base.py              247   W0511: TODO: CRITICAL - Replace introspection with explicit declaration pattern (fixme)


           Summary
  Total Runners: 4
    Passed: 2
    Failed: 2
  Total Violations: 4

  Exit Code: 1 (VIOLATIONS)

```

## PowerShell Linting Failures

PowerShell linting failed. See job logs for details.

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
 ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  .         -   Diff in /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/rust/crates/bootstrap-repo-cli/src/package_manager.rs:127:
  .         -   if !output.status.success() {
  .         -   let stderr = String::from_utf8_lossy(&output.stderr);
  .         -   -
  .         -   +
  .         -   // Provide helpful error message if sudo password is required
  .         -   if stderr.contains("a password is required") || stderr.contains("no password") {
  .         -   return Err(BootstrapError::CommandFailed {
  .         -   Diff in /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/rust/crates/bootstrap-repo-cli/src/package_manager.rs:179:
  .         -   if !output.status.success() {
  .         -   let stderr = String::from_utf8_lossy(&output.stderr);
  .         -   -
  .         -   +
  .         -   // Provide helpful error if sudo password required
  .         -   if stderr.contains("a password is required") || stderr.contains("no password") {
  .         -   return Err(BootstrapError::CommandFailed {
  .         -   Diff in /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/rust/crates/bootstrap-repo-cli/src/package_manager.rs:192:
  .         -   ),
  .         -   });
  .         -   }


           Summary
  Total Runners: 3
    Passed: 2
    Failed: 1
  Total Violations: 20

  Exit Code: 1 (VIOLATIONS)

```

