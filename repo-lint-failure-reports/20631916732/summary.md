# Repo Lint Summary

**Workflow Run:** https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/actions/runs/20631916732
**Timestamp:** 2026-01-01 03:34:28 UTC
**Branch:** 219/merge
**Commit:** 5be4d28a0458256e2f0a7d484dbad1b47046760c

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
  .         -   |        ^^^^^^^ F821
  .         -   580 |         output["summary"]["tools_run"] =
  .         -   581 |         output["summary"]["failed_tool_names"] =
  .         -   |
  .         -   tools/repo_lint/reporting.py:580:9: F821 Undefined name `output`
  .         -   |
  .         -   578 |     # Verbose mode: add tool names in summary
  .         -   579 |     if verbose:
  .         -   580 |         output["summary"]["tools_run"] =
  .         -   |         ^^^^^^ F821
  .         -   581 |         output["summary"]["failed_tool_names"] =
  .         -   582 |         output["summary"]["errored_tool_names"] =
  .         -   |
  .         -   tools/repo_lint/reporting.py:581:9: F821 Undefined name `output`
  .         -   |
  .         -   579 |     if verbose:
  .         -   580 |         output["summary"]["tools_run"] =
  .         -   581 |         output["summary"]["failed_tool_names"] =
  .         -   |         ^^^^^^ F821
  .         -   582 |         output["summary"]["errored_tool_names"] =
  .         -   |
  .         -   tools/repo_lint/reporting.py:582:9: F821 Undefined name `output`
  .         -   |
  .         -   580 |         output["summary"]["tools_run"] =
  .         -   581 |         output["summary"]["failed_tool_names"] =
  .         -   582 |         output["summary"]["errored_tool_names"] =
  .         -   |         ^^^^^^ F821
  .         -   583 |
  .         -   584 |     # Print JSON output (no Reporter needed for JSON)
  .         -   |
  .         -   tools/repo_lint/reporting.py:585:22: F821 Undefined name `output`
  .         -   |
  .         -   584 |     # Print JSON output (no Reporter needed for JSON)
  .         -   585 |     print(json.dumps(output, indent=2, sort_keys=True))
  .         -   |                      ^^^^^^ F821
  .         -   586 |
  .         -   587 |     # Return appropriate exit code
  .         -   |
  .         -   tools/repo_lint/reporting.py:588:8: F821 Undefined name `has_errors`
  .         -   |
  .         -   587 |     # Return appropriate exit code
  .         -   588 |     if has_errors:
  .         -   |        ^^^^^^^^^^ F821
  .         -   589 |         return 3
  .         -   590 |     elif all_passed:
  .         -   |
  .         -   tools/repo_lint/reporting.py:590:10: F821 Undefined name `all_passed`
  .         -   |
  .         -   588 |     if has_errors:
  .         -   589 |         return 3
  .         -   590 |     elif all_passed:
  .         -   |          ^^^^^^^^^^ F821
  .         -   591 |         return 0
  .         -   592 |     else:
  .         -   |
  .         -   [*] 1 fixable with the `--fix` option.


                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                pylint Failures
  Found 16 violation(s)


  File   Line   Message
 ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  .         -   ************* Module repo_lint.reporting
  .         -   tools/repo_lint/reporting.py:259:8: W1514: Using open without explicitly specifying an encoding (unspecified-encoding)
  .         -   tools/repo_lint/reporting.py:347:12: W1514: Using open without explicitly specifying an encoding (unspecified-encoding)
  .         -   tools/repo_lint/reporting.py:438:4: W0611: Unused Path imported from pathlib (unused-import)
  .         -   tools/repo_lint/reporting.py:511:13: R1714: Consider merging these comparisons with 'in' by using 'ext in ('.yaml', '.yml')'. Use a set instead if elements are hashable. (consider-using-in)
  .         -   tools/repo_lint/reporting.py:571:4: E0602: Undefined variable 'output' (undefined-variable)
  .         -   tools/repo_lint/reporting.py:572:18: E0602: Undefined variable 'all_passed' (undefined-variable)
  .         -   tools/repo_lint/reporting.py:572:37: E0602: Undefined variable 'has_errors' (undefined-variable)
  .         -   tools/repo_lint/reporting.py:573:28: E0602: Undefined variable 'total_violations' (undefined-variable)
  .         -   tools/repo_lint/reporting.py:579:7: E0602: Undefined variable 'verbose' (undefined-variable)
  .         -   tools/repo_lint/reporting.py:580:8: E0602: Undefined variable 'output' (undefined-variable)
  .         -   tools/repo_lint/reporting.py:581:8: E0602: Undefined variable 'output' (undefined-variable)
  .         -   tools/repo_lint/reporting.py:582:8: E0602: Undefined variable 'output' (undefined-variable)
  .         -   tools/repo_lint/reporting.py:585:21: E0602: Undefined variable 'output' (undefined-variable)
  .         -   tools/repo_lint/reporting.py:588:7: E0602: Undefined variable 'has_errors' (undefined-variable)
  .         -   tools/repo_lint/reporting.py:590:9: E0602: Undefined variable 'all_passed' (undefined-variable)


                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          validate_docstrings Failures
  Found 2 violation(s)


  File   Line   Message
 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  .         -   ❌ Validation FAILED: 1 violation(s) in 1 file(s)
  .         -   ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/tools/repo_lint/reporting.py:529


                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    Summary
  Total Runners: 4
    Passed: 0
    Failed: 4
  Total Violations: 124

  Exit Code: 1 (VIOLATIONS)

```

