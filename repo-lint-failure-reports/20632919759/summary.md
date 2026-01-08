# Repo Lint Summary

**Workflow Run:** https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/actions/runs/20632919759
**Timestamp:** 2026-01-01 05:05:26 UTC
**Branch:** 220/merge
**Commit:** cf1418168c93aced14e860c3ed90cb8b1912a628

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

                         Linting Results

  Runner                Status    Files   Violations   Duration
 ───────────────────────────────────────────────────────────────
  black                 ✅ PASS       -            0          -
  ruff                  ❌ FAIL       -           10          -
  pylint                ❌ FAIL       -           10          -
  validate_docstrings   ❌ FAIL       -            5          -


                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 ruff Failures
  Found 10 violation(s)


  File   Line   Message
 ────────────────────────────────────────────────────────────────────────────────────────────────────────────
  .         -   tools/repo_lint/ui/reporter.py:444:36: F541 [*] f-string without any placeholders
  .         -   |
  .         -   442 |             else:
  .         -   443 |                 self.console.print()
  .         -   444 |                 self.console.print(f"[bold]Summary:[/bold]")
  .         -   |                                    ^^^^^^^^^^^^^^^^^^^^^^^^ F541
  .         -   445 |                 self.console.print(f"[{status_color}]{summary_line}[/{status_color}]")
  .         -   |
  .         -   = help: Remove extraneous `f` prefix
  .         -   [*] 1 fixable with the `--fix` option.


                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                pylint Failures
  Found 10 violation(s)


  File   Line   Message
 ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  .         -   ************* Module repo_lint.tests.test_phase_2_7_features
  .         -   tools/repo_lint/tests/test_phase_2_7_features.py:320:12: W0611: Unused import yaml (unused-import)
  .         -   tools/repo_lint/tests/test_phase_2_7_features.py:380:12: E0401: Unable to import 'openpyxl' (import-error)
  .         -   tools/repo_lint/tests/test_phase_2_7_features.py:359:12: W0611: Unused import openpyxl (unused-import)
  .         -   ************* Module repo_lint.ui.reporter
  .         -   tools/repo_lint/ui/reporter.py:444:35: W1309: Using an f-string that does not have any interpolated variables (f-string-without-interpolation)
  .         -   tools/repo_lint/ui/reporter.py:463:29: E1101: Instance of 'Reporter' has no '_styled' member (no-member)
  .         -   tools/repo_lint/ui/reporter.py:467:24: E1101: Instance of 'Reporter' has no '_styled' member (no-member)
  .         -   tools/repo_lint/ui/reporter.py:474:24: E1101: Instance of 'Reporter' has no '_styled' member (no-member)
  .         -   tools/repo_lint/ui/reporter.py:524:8: R1702: Too many nested blocks (6/5) (too-many-nested-blocks)


                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          validate_docstrings Failures
  Found 5 violation(s)


  File   Line   Message
 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  .         -   ❌ Validation FAILED: 4 violation(s) in 1 file(s)
  .         -   ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/tools/repo_lint/tests/test_phase_2_7_features.py
  .         -   ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/tools/repo_lint/tests/test_phase_2_7_features.py:98
  .         -   ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/tools/repo_lint/tests/test_phase_2_7_features.py:108
  .         -   ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/tools/repo_lint/tests/test_phase_2_7_features.py:116


                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    Summary
  Total Runners: 4
    Passed: 1
    Failed: 3
  Total Violations: 25

  Exit Code: 1 (VIOLATIONS)

```

