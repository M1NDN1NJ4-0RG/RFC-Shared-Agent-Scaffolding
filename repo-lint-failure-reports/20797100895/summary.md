# Repo Lint Summary

**Workflow Run:** https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/actions/runs/20797100895
**Timestamp:** 2026-01-07 21:30:09 UTC
**Branch:** 277/merge
**Commit:** 036b295a456ddb674a3b7e4ddc4c6f4e1b56121f

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
 ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  base.py    246   W0511: TODO: Replace introspection with explicit declaration pattern (decorator or attribute) (fixme)
  base.py    291   W1203: Use lazy % formatting in logging functions (logging-fstring-interpolation)


           Summary
  Total Runners: 4
    Passed: 3
    Failed: 1
  Total Violations: 2

  Exit Code: 1 (VIOLATIONS)

```

