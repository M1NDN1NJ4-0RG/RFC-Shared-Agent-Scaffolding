# Repo Lint Summary

**Workflow Run:** https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/actions/runs/20752924922
**Timestamp:** 2026-01-06 15:29:30 UTC
**Branch:** 240/merge
**Commit:** e482509f53461538b5559635851acf6f128bb934

## Job Results

| Job | Status |
|-----|--------|
| Auto-Fix: Black | success |
| Detect Changed Files | success |
| Repo Lint: Python | failure |
| Repo Lint: Bash | failure |
| Repo Lint: PowerShell | skipped |
| Repo Lint: Perl | skipped |
| Repo Lint: YAML | skipped |
| Repo Lint: Rust | success |
| Vector Tests: Conformance | skipped |

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
  ruff                ❌ FAIL       -           10          -
  pylint              ❌ FAIL       -            9          -
  python-docstrings   ❌ FAIL       -            3          -


                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 black Failures
  Found 1 violation(s)


  File               Line   Message
 ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  <multiple files>      -   Code formatting does not match Black style. Run 'python3 -m tools.repo_lint fix' to auto-format.


                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 ruff Failures
  Found 10 violation(s)


  File                 Line   Message
 ────────────────────────────────────────────────────────────────────────────────
  bootstrap-watch.py     13   I001 [*] Import block is un-sorted or un-formatted
  bootstrap-watch.py     20   W293 [*] Blank line contains whitespace
  bootstrap-watch.py     29   W293 [*] Blank line contains whitespace
  bootstrap-watch.py     33   W293 [*] Blank line contains whitespace
  bootstrap-watch.py     36   W293 [*] Blank line contains whitespace
  bootstrap-watch.py     39   W293 [*] Blank line contains whitespace
  bootstrap-watch.py     44   W293 [*] Blank line contains whitespace
  bootstrap-watch.py     48   W293 [*] Blank line contains whitespace
  bootstrap-watch.py     53   W293 [*] Blank line contains whitespace
  bootstrap-watch.py     55   W293 [*] Blank line contains whitespace


                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                pylint Failures
  Found 9 violation(s)


  File                 Line   Message
 ──────────────────────────────────────────────────────────────────────────────
  bootstrap-watch.py     20   C0303: Trailing whitespace (trailing-whitespace)
  bootstrap-watch.py     29   C0303: Trailing whitespace (trailing-whitespace)
  bootstrap-watch.py     33   C0303: Trailing whitespace (trailing-whitespace)
  bootstrap-watch.py     36   C0303: Trailing whitespace (trailing-whitespace)
  bootstrap-watch.py     39   C0303: Trailing whitespace (trailing-whitespace)
  bootstrap-watch.py     44   C0303: Trailing whitespace (trailing-whitespace)
  bootstrap-watch.py     48   C0303: Trailing whitespace (trailing-whitespace)
  bootstrap-watch.py     53   C0303: Trailing whitespace (trailing-whitespace)
  bootstrap-watch.py     55   C0303: Trailing whitespace (trailing-whitespace)


                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           python-docstrings Failures
  Found 3 violation(s)


  File   Line   Message
 ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  .         -   ❌ Validation FAILED: 2 violation(s) in 1 file(s)
  .         -   ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/scripts/bootstrap-watch.py
  .         -   ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/scripts/bootstrap-watch.py:17


           Summary
  Total Runners: 4
    Passed: 0
    Failed: 4
  Total Violations: 23

  Exit Code: 1 (VIOLATIONS)

```

## Bash Linting Failures

```
🔍 Running repository linters and formatters...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Bash Linting
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                       Linting Results

  Runner            Status    Files   Violations   Duration
 ───────────────────────────────────────────────────────────
  shellcheck        ✅ PASS       -            0          -
  shfmt             ✅ PASS       -            0          -
  bash-docstrings   ❌ FAIL       -            3          -


                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            bash-docstrings Failures
  Found 3 violation(s)


  File   Line   Message
 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  .         -   ❌ Validation FAILED: 2 violation(s) in 1 file(s)
  .         -   ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/scripts/bootstrap-repo-lint-toolchain.sh:196
  .         -   ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/scripts/bootstrap-repo-lint-toolchain.sh:242


           Summary
  Total Runners: 3
    Passed: 2
    Failed: 1
  Total Violations: 3

  Exit Code: 1 (VIOLATIONS)

```

