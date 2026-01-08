# Repo Lint Summary

**Workflow Run:** https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/actions/runs/20757115869
**Timestamp:** 2026-01-06 17:57:49 UTC
**Branch:** 241/merge
**Commit:** 127277e1b1f10d5a69a95834144f381637204832

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
| Repo Lint: Rust | success |
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
  shellcheck        ✅ PASS       -            0          -
  shfmt             ❌ FAIL       -            1          -
  bash-docstrings   ❌ FAIL       -            2          -


                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 shfmt Failures
  Found 1 violation(s)


  File   Line   Message
 ───────────────────────────────────────────────────────────────────────────────────────────────────────────
            -   Shell scripts do not match shfmt style. Run 'python -m tools.repo_lint fix' to auto-format.


                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            bash-docstrings Failures
  Found 2 violation(s)


  File   Line   Message
 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  .         -   ❌ Validation FAILED: 1 violation(s) in 1 file(s)
  .         -   ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/scripts/bootstrap-wrapper.sh


           Summary
  Total Runners: 3
    Passed: 1
    Failed: 2
  Total Violations: 3

  Exit Code: 1 (VIOLATIONS)

```

