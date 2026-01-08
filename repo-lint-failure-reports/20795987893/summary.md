# Repo Lint Summary

**Workflow Run:** https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/actions/runs/20795987893
**Timestamp:** 2026-01-07 20:47:46 UTC
**Branch:** 277/merge
**Commit:** 0bae6f3371afacf9c0c8c8a590f9f770d0281075

## Job Results

| Job | Status |
|-----|--------|
| Auto-Fix: Black | success |
| Detect Changed Files | success |
| Repo Lint: Python | failure |
| Repo Lint: Bash | success |
| Repo Lint: PowerShell | success |
| Repo Lint: Perl | success |
| Repo Lint: YAML | success |
| Repo Lint: Rust | success |
| Vector Tests: Conformance | success |

## Python Linting Failures

```
🔍 Running repository linters and formatters...


                        Linting Results

  Runner              Status    Files   Violations   Duration
 ─────────────────────────────────────────────────────────────
  black               ✅ PASS       -            0          -
  ruff                ✅ PASS       -            0          -
  pylint              ❌ FAIL       -            2          -
  python-docstrings   ✅ PASS       -            0          -


                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                pylint Failures
  Found 2 violation(s)


  File      Line   Message
 ────────────────────────────────────────────────────────────────────────────────────────────────────────
  base.py    269   W0621: Redefining name 'LintResult' from outer scope (line 41) (redefined-outer-name)
  base.py    269   W0404: Reimport 'LintResult' (imported line 41) (reimported)


           Summary
  Total Runners: 4
    Passed: 3
    Failed: 1
  Total Violations: 2

  Exit Code: 1 (VIOLATIONS)

```

