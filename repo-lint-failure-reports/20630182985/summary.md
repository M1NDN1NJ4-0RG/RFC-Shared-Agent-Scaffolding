# Repo Lint Summary

**Workflow Run:** https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/actions/runs/20630182985
**Timestamp:** 2026-01-01 01:05:28 UTC
**Branch:** 217/merge
**Commit:** 2e0cd2259c2cc89fd9cd5f8ef88adce05b1da0d8

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
  ruff                  ✅ PASS       -            0          -
  pylint                ❌ FAIL       -            4          -
  validate_docstrings   ❌ FAIL       -            2          -


                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                pylint Failures
  Found 4 violation(s)


  File   Line   Message
 ──────────────────────────────────────────────────────────────────────────────────────────────────────
  .         -   ************* Module repo_lint.cli
  .         -   tools/repo_lint/cli.py:309:4: W0622: Redefining built-in 'format' (redefined-builtin)
  .         -   tools/repo_lint/cli.py:495:68: W0622: Redefining built-in 'format' (redefined-builtin)
  .         -   tools/repo_lint/cli.py:718:15: W0622: Redefining built-in 'format' (redefined-builtin)


                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          validate_docstrings Failures
  Found 2 violation(s)


  File   Line   Message
 ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  .         -   ❌ Validation FAILED: 1 violation(s) in 1 file(s)
  .         -   ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/tools/repo_lint/doctor.py


                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    Summary
  Total Runners: 4
    Passed: 2
    Failed: 2
  Total Violations: 6

  Exit Code: 1 (VIOLATIONS)

```

