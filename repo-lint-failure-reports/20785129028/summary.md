# Repo Lint Summary

**Workflow Run:** https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/actions/runs/20785129028
**Timestamp:** 2026-01-07 14:41:30 UTC
**Branch:** 263/merge
**Commit:** fe87333e20f96184d1c78ee51916266bcaa70e16

## Job Results

| Job | Status |
|-----|--------|
| Auto-Fix: Black | success |
| Detect Changed Files | success |
| Repo Lint: Python | success |
| Repo Lint: Bash | success |
| Repo Lint: PowerShell | success |
| Repo Lint: Perl | success |
| Repo Lint: YAML | failure |
| Repo Lint: Rust | success |
| Vector Tests: Conformance | success |

## YAML Linting Failures

```
🔍 Running repository linters and formatters...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  YAML Linting
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                       Linting Results

  Runner            Status    Files   Violations   Duration
 ───────────────────────────────────────────────────────────
  yamllint          ✅ PASS       -            0          -
  yaml-docstrings   ❌ FAIL       -            2          -


                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            yaml-docstrings Failures
  Found 2 violation(s)


  File   Line   Message
 ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  .         -   ❌ Validation FAILED: 1 violation(s) in 1 file(s)
  .         -   ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/.github/workflows/copilot-setup-steps.yml


           Summary
  Total Runners: 2
    Passed: 1
    Failed: 1
  Total Violations: 2

  Exit Code: 1 (VIOLATIONS)

```

