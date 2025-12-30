# Repo Lint Summary

**Workflow Run:** https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/actions/runs/20604911079
**Timestamp:** 2025-12-30 20:09:31 UTC
**Branch:** 145/merge
**Commit:** 034792eb96dbc014a3d1e07228c9f83100b95ae5

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

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Python Linting
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Linting Results
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ ruff: FAILED (36 violation(s))
   .: [ruff] tools/repo_lint/tests/test_cli_dispatch.py:41:121: E501 Line too long (123 > 120)
   .: [ruff] |
   .: [ruff] 39 |     Run specific test::
   .: [ruff] 40 |
   .: [ruff] 41 |         python3 -m pytest tools/repo_lint/tests/test_cli_dispatch.py::TestRunnerDispatch::test_only_flag_filters_runners -v
   .: [ruff] |                                                                                                                         ^^^ E501
   .: [ruff] 42 |
   .: [ruff] 43 | :Notes:
   .: [ruff] |
   .: [ruff] tools/repo_lint/tests/test_exit_codes.py:56:27: F401 [*] `unittest.mock.MagicMock` imported but unused
   .: [ruff] |
   .: [ruff] 54 | import unittest
   .: [ruff] 55 | from pathlib import Path
   .: [ruff] 56 | from unittest.mock import MagicMock, patch
   .: [ruff] |                           ^^^^^^^^^ F401
   .: [ruff] 57 |
   .: [ruff] 58 | # Add repo_lint parent directory to path for imports
   .: [ruff] |
   .: [ruff] = help: Remove unused import: `unittest.mock.MagicMock`
   .: [ruff] tools/repo_lint/tests/test_exit_codes.py:63:46: F401 [*] `tools.repo_lint.common.LintResult` imported but unused
   .: [ruff] |
   .: [ruff] 62 | from tools.repo_lint.cli import cmd_check, cmd_fix, cmd_install  # noqa: E402
   .: [ruff] 63 | from tools.repo_lint.common import ExitCode, LintResult  # noqa: E402
   .: [ruff] |                                              ^^^^^^^^^^ F401
   .: [ruff] |
   .: [ruff] = help: Remove unused import: `tools.repo_lint.common.LintResult`
   .: [ruff] tools/repo_lint/tests/test_output_format.py:59:36: F401 [*] `tools.repo_lint.common.ExitCode` imported but unused
   .: [ruff] |
   .: [ruff] 57 | sys.path.insert(0, str(repo_root))
   .: [ruff] 58 |
   .: [ruff] 59 | from tools.repo_lint.common import ExitCode, LintResult, Violation  # noqa: E402
   .: [ruff] |                                    ^^^^^^^^ F401
   .: [ruff] 60 | from tools.repo_lint.reporting import report_results  # noqa: E402
   .: [ruff] |
   .: [ruff] = help: Remove unused import: `tools.repo_lint.common.ExitCode`
   .: [ruff] [*] 3 fixable with the `--fix` option.

❌ pylint: FAILED (15 violation(s))
   .: [pylint] ************* Module repo_lint.tests.test_cli_dispatch
   .: [pylint] tools/repo_lint/tests/test_cli_dispatch.py:41:0: C0301: Line too long (123/120) (line-too-long)
   .: [pylint] tools/repo_lint/tests/test_cli_dispatch.py:88:4: R0913: Too many arguments (8/5) (too-many-arguments)
   .: [pylint] tools/repo_lint/tests/test_cli_dispatch.py:88:4: R0917: Too many positional arguments (8/5) (too-many-positional-arguments)
   .: [pylint] tools/repo_lint/tests/test_cli_dispatch.py:143:4: R0913: Too many arguments (8/5) (too-many-arguments)
   .: [pylint] tools/repo_lint/tests/test_cli_dispatch.py:143:4: R0917: Too many positional arguments (8/5) (too-many-positional-arguments)
   .: [pylint] tools/repo_lint/tests/test_cli_dispatch.py:197:4: R0913: Too many arguments (7/5) (too-many-arguments)
   .: [pylint] tools/repo_lint/tests/test_cli_dispatch.py:197:4: R0917: Too many positional arguments (7/5) (too-many-positional-arguments)
   .: [pylint] tools/repo_lint/tests/test_cli_dispatch.py:264:4: R0913: Too many arguments (7/5) (too-many-arguments)
   .: [pylint] tools/repo_lint/tests/test_cli_dispatch.py:264:4: R0917: Too many positional arguments (7/5) (too-many-positional-arguments)
   .: [pylint] ************* Module repo_lint.tests.test_exit_codes
   .: [pylint] tools/repo_lint/tests/test_exit_codes.py:56:0: W0611: Unused MagicMock imported from unittest.mock (unused-import)
   .: [pylint] tools/repo_lint/tests/test_exit_codes.py:63:0: W0611: Unused LintResult imported from tools.repo_lint.common (unused-import)
   .: [pylint] ************* Module repo_lint.tests.test_output_format
   .: [pylint] tools/repo_lint/tests/test_output_format.py:59:0: W0611: Unused ExitCode imported from tools.repo_lint.common (unused-import)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ Found 51 violation(s) across 2 tool(s)
```

