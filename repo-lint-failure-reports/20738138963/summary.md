# Repo Lint Summary

**Workflow Run:** https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/actions/runs/20738138963
**Timestamp:** 2026-01-06 04:36:09 UTC
**Branch:** 237/merge
**Commit:** 1b42225e75cea5ddee6ad723dd73b651425d6dad

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

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Rust Linting
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                       Linting Results

  Runner            Status    Files   Violations   Duration
 ───────────────────────────────────────────────────────────
  rustfmt           ✅ PASS       -            0          -
  clippy            ✅ PASS       -            0          -
  rust-docstrings   ❌ FAIL       -           42          -


                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            rust-docstrings Failures
  Found 42 violation(s)


  File                        Line   Message
 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  unknown                        -   🔍 Validating docstring contracts...
  unknown                        -   Found 152 files in scope
  unknown                        -   Filtered to 22 rust file(s) (from 152 total)
  ❌ Validation FAILED           -   12 violation(s) in 12 file(s)
  unknown                        -   ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/rust/src/bootstrap_v2/cli.rs
  Missing required sections      -   # Purpose, # Examples
  unknown                        -   Expected Rustdoc sections in module docs
  unknown                        -   ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/rust/src/bootstrap_v2/config.rs
  Missing required sections      -   # Purpose, # Examples
  unknown                        -   Expected Rustdoc sections in module docs
  unknown                        -   ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/rust/src/bootstrap_v2/context.rs
  Missing required sections      -   # Purpose
  unknown                        -   Expected Rustdoc sections in module docs
  unknown                        -   ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/rust/src/bootstrap_v2/errors.rs
  Missing required sections      -   # Purpose
  unknown                        -   Expected Rustdoc sections in module docs
  unknown                        -   ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/rust/src/bootstrap_v2/exit_codes.rs
  Missing required sections      -   # Purpose
  unknown                        -   Expected Rustdoc sections in module docs
  unknown                        -   ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/rust/src/bootstrap_v2/installer.rs
  Missing required sections      -   # Purpose, # Examples
  unknown                        -   Expected Rustdoc sections in module docs
  unknown                        -   ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/rust/src/bootstrap_v2/lock.rs
  Missing required sections      -   # Purpose, # Examples
  unknown                        -   Expected Rustdoc sections in module docs
  unknown                        -   ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/rust/src/bootstrap_v2/mod.rs
  Missing required sections      -   # Purpose, # Examples
  unknown                        -   Expected Rustdoc sections in module docs
  unknown                        -   ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/rust/src/bootstrap_v2/plan.rs
  Missing required sections      -   # Purpose, # Examples
  unknown                        -   Expected Rustdoc sections in module docs
  unknown                        -   ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/rust/src/bootstrap_v2/progress.rs
  Missing required sections      -   # Purpose, # Examples
  unknown                        -   Expected Rustdoc sections in module docs
  unknown                        -   ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/rust/src/bootstrap_v2/retry.rs
  Missing required sections      -   # Purpose, # Examples
  unknown                        -   Expected Rustdoc sections in module docs
  unknown                        -   ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/rust/src/lib.rs
  Missing required sections      -   # Purpose, # Examples
  unknown                        -   Expected Rustdoc sections in module docs
  💡 Tip                         -   See docs/contributing/docstring-contracts/ for contract details and templates
  💡 Tip                         -   Use # noqa: SECTION or # noqa: D102 pragmas to exempt specific items


           Summary
  Total Runners: 3
    Passed: 2
    Failed: 1
  Total Violations: 42

  Exit Code: 1 (VIOLATIONS)

```

