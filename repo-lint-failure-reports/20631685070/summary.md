# Repo Lint Summary

**Workflow Run:** https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/actions/runs/20631685070
**Timestamp:** 2026-01-01 03:14:26 UTC
**Branch:** 219/merge
**Commit:** c92347b6f8be794112bf7505b808474acb615ce1

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
  .         -   tools/repo_lint/reporting.py:572:9: F821 Undefined name `output`
  .         -   |
  .         -   570 |     # Verbose mode: add tool names in summary
  .         -   571 |     if verbose:
  .         -   572 |         output["summary"]["tools_run"] =
  .         -   |         ^^^^^^ F821
  .         -   573 |         output["summary"]["failed_tool_names"] =
  .         -   574 |         output["summary"]["errored_tool_names"] =
  .         -   |
  .         -   tools/repo_lint/reporting.py:573:9: F821 Undefined name `output`
  .         -   |
  .         -   571 |     if verbose:
  .         -   572 |         output["summary"]["tools_run"] =
  .         -   573 |         output["summary"]["failed_tool_names"] =
  .         -   |         ^^^^^^ F821
  .         -   574 |         output["summary"]["errored_tool_names"] =
  .         -   |
  .         -   tools/repo_lint/reporting.py:574:9: F821 Undefined name `output`
  .         -   |
  .         -   572 |         output["summary"]["tools_run"] =
  .         -   573 |         output["summary"]["failed_tool_names"] =
  .         -   574 |         output["summary"]["errored_tool_names"] =
  .         -   |         ^^^^^^ F821
  .         -   575 |
  .         -   576 |     # Print JSON output (no Reporter needed for JSON)
  .         -   |
  .         -   tools/repo_lint/reporting.py:577:22: F821 Undefined name `output`
  .         -   |
  .         -   576 |     # Print JSON output (no Reporter needed for JSON)
  .         -   577 |     print(json.dumps(output, indent=2, sort_keys=True))
  .         -   |                      ^^^^^^ F821
  .         -   578 |
  .         -   579 |     # Return appropriate exit code
  .         -   |
  .         -   tools/repo_lint/reporting.py:580:8: F821 Undefined name `has_errors`
  .         -   |
  .         -   579 |     # Return appropriate exit code
  .         -   580 |     if has_errors:
  .         -   |        ^^^^^^^^^^ F821
  .         -   581 |         return 3
  .         -   582 |     elif all_passed:
  .         -   |
  .         -   tools/repo_lint/reporting.py:582:10: F821 Undefined name `all_passed`
  .         -   |
  .         -   580 |     if has_errors:
  .         -   581 |         return 3
  .         -   582 |     elif all_passed:
  .         -   |          ^^^^^^^^^^ F821
  .         -   583 |         return 0
  .         -   584 |     else:
  .         -   |
  .         -   [*] 13 fixable with the `--fix` option.


                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                pylint Failures
  Found 20 violation(s)


  File   Line   Message
 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  .         -   ************* Module repo_lint.reporting
  .         -   tools/repo_lint/reporting.py:96:0: C0303: Trailing whitespace (trailing-whitespace)
  .         -   tools/repo_lint/reporting.py:100:0: C0303: Trailing whitespace (trailing-whitespace)
  .         -   tools/repo_lint/reporting.py:146:0: C0303: Trailing whitespace (trailing-whitespace)
  .         -   tools/repo_lint/reporting.py:441:0: C0303: Trailing whitespace (trailing-whitespace)
  .         -   tools/repo_lint/reporting.py:446:0: C0303: Trailing whitespace (trailing-whitespace)
  .         -   tools/repo_lint/reporting.py:466:0: C0303: Trailing whitespace (trailing-whitespace)
  .         -   tools/repo_lint/reporting.py:497:0: C0303: Trailing whitespace (trailing-whitespace)
  .         -   tools/repo_lint/reporting.py:509:0: C0303: Trailing whitespace (trailing-whitespace)
  .         -   tools/repo_lint/reporting.py:528:0: C0303: Trailing whitespace (trailing-whitespace)
  .         -   tools/repo_lint/reporting.py:531:0: C0303: Trailing whitespace (trailing-whitespace)
  .         -   tools/repo_lint/reporting.py:549:0: C0303: Trailing whitespace (trailing-whitespace)
  .         -   tools/repo_lint/reporting.py:561:0: C0303: Trailing whitespace (trailing-whitespace)
  .         -   tools/repo_lint/reporting.py:57:0: R0913: Too many arguments (12/5) (too-many-arguments)
  .         -   tools/repo_lint/reporting.py:57:0: R0917: Too many positional arguments (12/5) (too-many-positional-arguments)
  .         -   tools/repo_lint/reporting.py:258:8: W1514: Using open without explicitly specifying an encoding (unspecified-encoding)
  .         -   tools/repo_lint/reporting.py:344:12: W1514: Using open without explicitly specifying an encoding (unspecified-encoding)
  .         -   tools/repo_lint/reporting.py:375:9: W1514: Using open without explicitly specifying an encoding (unspecified-encoding)
  .         -   tools/repo_lint/reporting.py:395:9: W1514: Using open without explicitly specifying an encoding (unspecified-encoding)
  .         -   tools/repo_lint/reporting.py:426:8: W0611: Unused import openpyxl (unused-import)


                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          validate_docstrings Failures
  Found 2 violation(s)


  File   Line   Message
 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  .         -   ❌ Validation FAILED: 1 violation(s) in 1 file(s)
  .         -   ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/tools/repo_lint/reporting.py:521


                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    Summary
  Total Runners: 4
    Passed: 0
    Failed: 4
  Total Violations: 278

  Exit Code: 1 (VIOLATIONS)

```

