# Repo Lint Summary

**Workflow Run:** https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/actions/runs/20730145226
**Timestamp:** 2026-01-05 21:48:28 UTC
**Branch:** 229/merge
**Commit:** e7c86caf034304b201e426125f318e53d8fec3f3

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

  Runner              Status    Files   Violations   Duration
 ─────────────────────────────────────────────────────────────
  black               ❌ FAIL       -            1          -
  ruff                ❌ FAIL       -            2          -
  pylint              ✅ PASS       -            0          -
  python-docstrings   ✅ PASS       -            0          -


                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 black Failures
  Found 1 violation(s)


  File               Line   Message
 ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  <multiple files>      -   Code formatting does not match Black style. Run 'python3 -m tools.repo_lint fix' to auto-format.


                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 ruff Failures
  Found 2 violation(s)


  File     Line   Message
 ─────────────────────────────────────────────────────
  cli.py    157   W293 Blank line contains whitespace
  cli.py   1767   W293 Blank line contains whitespace


  ⚠️  No fixes available (2 hidden fixes can be enabled with the `--unsafe-fixes` option). (Review before applying with --unsafe-fixes)


           Summary
  Total Runners: 4
    Passed: 2
    Failed: 2
  Total Violations: 3

  Exit Code: 1 (VIOLATIONS)

```

