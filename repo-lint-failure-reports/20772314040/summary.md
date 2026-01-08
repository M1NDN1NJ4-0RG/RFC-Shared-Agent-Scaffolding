# Repo Lint Summary

**Workflow Run:** https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/actions/runs/20772314040
**Timestamp:** 2026-01-07 06:07:54 UTC
**Branch:** 259/merge
**Commit:** 80946a6b76df5c955569e03b6105d25e5739e5f4

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
  clippy            ❌ FAIL       -            2          -
  rust-docstrings   ✅ PASS       -            0          -


                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                clippy Failures
  Found 2 violation(s)


  File                    Line   Message
 ──────────────────────────────────────────────────────────────────────────────
  src/bootstrap_main.rs    130   unused_variables: unused variable: `progress`
  src/bootstrap_main.rs    130   unused_variables: unused variable: `progress`


           Summary
  Total Runners: 3
    Passed: 2
    Failed: 1
  Total Violations: 2

  Exit Code: 1 (VIOLATIONS)

```

