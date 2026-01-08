# Repo Lint Summary

**Workflow Run:** https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/actions/runs/20626392540
**Timestamp:** 2025-12-31 20:11:40 UTC
**Branch:** 212/merge
**Commit:** 96a3d51a05fd12a4424acb8a2a1077589f56d87b

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

  Runner                Status    Files   Violations   Duration
 ───────────────────────────────────────────────────────────────
  shellcheck            ✅ PASS       -            0          -
  shfmt                 ❌ FAIL       -            1          -
  validate_docstrings   ✅ PASS       -            0          -


                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 shfmt Failures
  Found 1 violation(s)


  File   Line   Message
 ───────────────────────────────────────────────────────────────────────────────────────────────────────────
  .         -   Shell scripts do not match shfmt style. Run 'python -m tools.repo_lint fix' to auto-format.


                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    Summary
  Total Runners: 3
    Passed: 2
    Failed: 1
  Total Violations: 1

  Exit Code: 1 (VIOLATIONS)

```

