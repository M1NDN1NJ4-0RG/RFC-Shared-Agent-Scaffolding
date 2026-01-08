# Repo Lint Summary

**Workflow Run:** https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/actions/runs/20635754957
**Timestamp:** 2026-01-01 08:55:29 UTC
**Branch:** 222/merge
**Commit:** bb16cd9e70e18cc0976ee7a8a7f4c642108f1498

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
  ruff                  ❌ FAIL       -           40          -
  pylint                ✅ PASS       -            0          -
  validate_docstrings   ✅ PASS       -            0          -


                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 ruff Failures
  Found 40 violation(s)


  File                          Line   Message
 ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  all-docstring-violations.py    109   E731 Do not assign a `lambda` expression, use a `def`
  black-violations.py              7   E501 Line too long (121 > 120)
  black-violations.py             52   F821 Undefined name `function_call`
  black-violations.py             52   F821 Undefined name `arg1`
  black-violations.py             52   F821 Undefined name `arg2`
  black-violations.py             52   F821 Undefined name `arg3`
  pylint-violations.py            32   F841 Local variable `var11` is assigned to but never used
  pylint-violations.py            33   F841 Local variable `var12` is assigned to but never used
  pylint-violations.py            34   F841 Local variable `var13` is assigned to but never used
  pylint-violations.py            35   F841 Local variable `var14` is assigned to but never used
  pylint-violations.py            36   F841 Local variable `var15` is assigned to but never used
  pylint-violations.py            37   F841 Local variable `var16` is assigned to but never used
  pylint-violations.py            44   F841 Local variable `x` is assigned to but never used
  pylint-violations.py            45   F841 Local variable `y` is assigned to but never used
  pylint-violations.py           136   F841 Local variable `x` is assigned to but never used
  pylint-violations.py           152   E402 Module level import not at top of file
  pylint-violations.py           152   F401 [*] `sys` imported but unused
  ruff-violations.py               6   I001 [*] Import block is un-sorted or un-formatted
  ruff-violations.py               6   F401 [*] `os` imported but unused
  ruff-violations.py               7   F401 [*] `sys` imported but unused
  ruff-violations.py               8   F401 [*] `json` imported but unused
  ruff-violations.py               9   F401 [*] `typing.List` imported but unused
  ruff-violations.py               9   F401 [*] `typing.Dict` imported but unused
  ruff-violations.py              10   F401 [*] `subprocess` imported but unused
  ruff-violations.py              16   E501 Line too long (174 > 120)
  ruff-violations.py              19   F541 [*] f-string without any placeholders
  ruff-violations.py              23   E711 Comparison to `None` should be `cond is None`
  ruff-violations.py              28   E712 Avoid equality comparisons to `True`; use `if flag:` for truth checks
  ruff-violations.py              32   F821 Undefined name `undefined_variable`
  ruff-violations.py              40   E402 Module level import not at top of file
  ruff-violations.py              40   F401 [*] `random` imported but unused
  ruff-violations.py              43   F541 [*] f-string without any placeholders
  ruff-violations.py              53   E402 Module level import not at top of file
  ruff-violations.py              73   E731 Do not assign a `lambda` expression, use a `def`
  ruff-violations.py              76   F523 [*] `.format` call has unused arguments at position(s): 1
  ruff-violations.py              76   UP030 Use implicit references for positional format fields
  ruff-violations.py              80   E741 Ambiguous variable name: `O`
  ruff-violations.py              81   E741 Ambiguous variable name: `I`
  ruff-violations.py              88   E402 Module level import not at top of file
  .                                -   ⚠️  [*] 12 fixable with the `--fix` option (14 hidden fixes can be enabled with the `--unsafe-fixes` option). (Review before applying with --unsafe-fixes)


           Summary
  Total Runners: 4
    Passed: 3
    Failed: 1
  Total Violations: 40

  Exit Code: 1 (VIOLATIONS)

```

