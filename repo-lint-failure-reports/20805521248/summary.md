# Repo Lint Summary

**Workflow Run:** https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/actions/runs/20805521248
**Timestamp:** 2026-01-08 04:32:56 UTC
**Branch:** 289/merge
**Commit:** f23c00b4cd74089efa32da3253b944d39f8b51a1

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
  ruff                ❌ FAIL       -            1          -
  pylint              ❌ FAIL       -            1          -
  python-docstrings   ✅ PASS       -            0          -


                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 ruff Failures
  Found 1 violation(s)


  File                      Line   Message
 ──────────────────────────────────────────────────────────────────────────────
  test_markdown_runner.py     59   E402 Module level import not at top of file


                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                pylint Failures
  Found 1 violation(s)


  File                      Line   Message
 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  test_markdown_runner.py     59   C0413: Import "from tools.repo_lint.runners.markdown_runner import MarkdownRunner" should be placed at the top of the module (wrong-import-position)


           Summary
  Total Runners: 4
    Passed: 2
    Failed: 2
  Total Violations: 2

  Exit Code: 1 (VIOLATIONS)

```

