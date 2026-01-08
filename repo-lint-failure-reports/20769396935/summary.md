# Repo Lint Summary

**Workflow Run:** https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/actions/runs/20769396935
**Timestamp:** 2026-01-07 03:15:42 UTC
**Branch:** 256/merge
**Commit:** f6dab64a13ceb6973a91b1f89711e63dcf89eb33

## Job Results

| Job | Status |
|-----|--------|
| Auto-Fix: Black | success |
| Detect Changed Files | success |
| Repo Lint: Python | skipped |
| Repo Lint: Bash | failure |
| Repo Lint: PowerShell | skipped |
| Repo Lint: Perl | skipped |
| Repo Lint: YAML | skipped |
| Repo Lint: Rust | skipped |
| Vector Tests: Conformance | skipped |

## Bash Linting Failures

```
🔍 Running repository linters and formatters...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Bash Linting
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                       Linting Results

  Runner            Status    Files   Violations   Duration
 ───────────────────────────────────────────────────────────
  shellcheck        ❌ FAIL       -            1          -
  shfmt             ❌ FAIL       -            1          -
  bash-docstrings   ❌ FAIL       -            2          -


                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              shellcheck Failures
  Found 1 violation(s)


  File   Line   Message
 ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
            -   scripts/benchmarks/benchmark-bootstrappers.sh:30:11: note: Expressions don't expand in single quotes, use double quotes for that. [SC2016]


                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 shfmt Failures
  Found 1 violation(s)


  File   Line   Message
 ───────────────────────────────────────────────────────────────────────────────────────────────────────────
            -   Shell scripts do not match shfmt style. Run 'python -m tools.repo_lint fix' to auto-format.


                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            bash-docstrings Failures
  Found 2 violation(s)


  File   Line   Message
 ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  .         -   ❌ Validation FAILED: 1 violation(s) in 1 file(s)
  .         -   ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/scripts/benchmarks/benchmark-bootstrappers.sh


           Summary
  Total Runners: 3
    Passed: 0
    Failed: 3
  Total Violations: 4

  Exit Code: 1 (VIOLATIONS)

```

