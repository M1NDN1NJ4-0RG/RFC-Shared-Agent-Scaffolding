# Repo Lint Summary

**Workflow Run:** https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/actions/runs/20806467339
**Timestamp:** 2026-01-08 05:29:17 UTC
**Branch:** 290/merge
**Commit:** d351e7d2c10b7fbc62d154a660fb12fe3c6e898b

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
  ruff                ❌ FAIL       -            2          -
  pylint              ✅ PASS       -            0          -
  python-docstrings   ✅ PASS       -            0          -


                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 ruff Failures
  Found 2 violation(s)


  File                      Line   Message
 ──────────────────────────────────────────────────────────────────────────────
  test_markdown_runner.py     60   E402 Module level import not at top of file
  test_toml_runner.py         61   E402 Module level import not at top of file


           Summary
  Total Runners: 4
    Passed: 3
    Failed: 1
  Total Violations: 2

  Exit Code: 1 (VIOLATIONS)

```

