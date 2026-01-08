# Repo Lint Summary

**Workflow Run:** https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/actions/runs/20805098750
**Timestamp:** 2026-01-08 04:07:53 UTC
**Branch:** 289/merge
**Commit:** bc7d5523e7108778f2574fa8fd6bbf0cd670362c

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
  pylint              ❌ FAIL       -           10          -
  python-docstrings   ✅ PASS       -            0          -


                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 ruff Failures
  Found 1 violation(s)


  File                      Line   Message
 ──────────────────────────────────────────────────────────────────────────────
  test_markdown_runner.py     59   E402 Module level import not at top of file


                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                pylint Failures
  Found 10 violation(s)


  File                      Line   Message
 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  test_markdown_runner.py     59   C0413: Import "from tools.repo_lint.runners.markdown_runner import MarkdownRunner" should be placed at the top of the module (wrong-import-position)
  test_markdown_runner.py    151   W0212: Access to a protected member _run_markdownlint of a client class (protected-access)
  test_markdown_runner.py    174   W0212: Access to a protected member _run_markdownlint of a client class (protected-access)
  test_markdown_runner.py    194   W0212: Access to a protected member _run_markdownlint of a client class (protected-access)
  test_markdown_runner.py    208   W0212: Access to a protected member _parse_markdownlint_output of a client class (protected-access)
  test_markdown_runner.py    225   W0212: Access to a protected member _parse_markdownlint_output of a client class (protected-access)
  test_markdown_runner.py    244   W0212: Access to a protected member _parse_markdownlint_output of a client class (protected-access)
  test_markdown_runner.py    259   W0212: Access to a protected member _parse_markdownlint_output of a client class (protected-access)
  test_markdown_runner.py    269   W0212: Access to a protected member _parse_markdownlint_output of a client class (protected-access)
  test_markdown_runner.py    284   W0212: Access to a protected member _run_markdownlint of a client class (protected-access)


           Summary
  Total Runners: 4
    Passed: 2
    Failed: 2
  Total Violations: 11

  Exit Code: 1 (VIOLATIONS)

```

