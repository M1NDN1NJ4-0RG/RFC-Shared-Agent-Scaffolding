# Repo Lint Summary

**Workflow Run:** https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/actions/runs/20636654971
**Timestamp:** 2026-01-01 10:05:10 UTC
**Branch:** 222/merge
**Commit:** 359d03de8c104155fa683c2220164b55ed54abd7

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
 ────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  .         -   Code formatting does not match Black style. Run 'python3 -m tools.repo_lint fix' to auto-format.


                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 ruff Failures
  Found 56 violation(s)


  File                          Line   Message
 ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  all-docstring-violations.py     30   W293 [*] Blank line contains whitespace
  all-docstring-violations.py     33   W293 [*] Blank line contains whitespace
  all-docstring-violations.py     54   W293 [*] Blank line contains whitespace
  all-docstring-violations.py     57   W293 [*] Blank line contains whitespace
  all-docstring-violations.py     64   W293 [*] Blank line contains whitespace
  all-docstring-violations.py     72   W293 [*] Blank line contains whitespace
  all-docstring-violations.py     80   W293 [*] Blank line contains whitespace
  all-docstring-violations.py     93   E731 Do not assign a `lambda` expression, use a `def`
  all-docstring-violations.py     98   W293 Blank line contains whitespace
  black-violations.py              7   E501 Line too long (121 > 120)
  black-violations.py             27   E701 Multiple statements on one line (colon)
  black-violations.py             27   E702 Multiple statements on one line (semicolon)
  black-violations.py             33   W293 [*] Blank line contains whitespace
  black-violations.py             53   F821 Undefined name `function_call`
  black-violations.py             53   F821 Undefined name `arg1`
  black-violations.py             53   F821 Undefined name `arg2`
  black-violations.py             53   F821 Undefined name `arg3`
  pylint-violations.py            29   F841 Local variable `var11` is assigned to but never used
  pylint-violations.py            30   F841 Local variable `var12` is assigned to but never used
  pylint-violations.py            31   F841 Local variable `var13` is assigned to but never used
  pylint-violations.py            32   F841 Local variable `var14` is assigned to but never used
  pylint-violations.py            33   F841 Local variable `var15` is assigned to but never used
  pylint-violations.py            34   F841 Local variable `var16` is assigned to but never used
  pylint-violations.py            40   F841 Local variable `x` is assigned to but never used
  pylint-violations.py            41   F841 Local variable `y` is assigned to but never used
  pylint-violations.py           127   F841 Local variable `x` is assigned to but never used
  pylint-violations.py           139   E402 Module level import not at top of file
  pylint-violations.py           139   I001 [*] Import block is un-sorted or un-formatted
  pylint-violations.py           139   F401 [*] `sys` imported but unused
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
  ruff-violations.py              38   E402 Module level import not at top of file
  ruff-violations.py              38   F401 [*] `random` imported but unused
  ruff-violations.py              41   F541 [*] f-string without any placeholders
  ruff-violations.py              49   E402 Module level import not at top of file
  ruff-violations.py              49   I001 [*] Import block is un-sorted or un-formatted
  ruff-violations.py              65   E731 Do not assign a `lambda` expression, use a `def`
  ruff-violations.py              68   F523 [*] `.format` call has unused arguments at position(s): 1
  ruff-violations.py              68   UP030 Use implicit references for positional format fields
  ruff-violations.py              72   E741 Ambiguous variable name: `O`
  ruff-violations.py              73   E741 Ambiguous variable name: `I`
  ruff-violations.py              80   E402 Module level import not at top of file
  ruff-violations.py              80   I001 [*] Import block is un-sorted or un-formatted
  ruff-violations.py              85   UP039 [*] Unnecessary parentheses after class definition
  test_fixture_vector_mode.py    203   F841 Local variable `result` is assigned to but never used
  .                                -   ⚠️  [*] 24 fixable with the `--fix` option (16 hidden fixes can be enabled with the `--unsafe-fixes` option). (Review before applying with --unsafe-fixes)


                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                pylint Failures
  Found 6 violation(s)


  File                          Line   Message
 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  test_fixture_vector_mode.py     82   W0621: Redefining name 'temp_fixtures_dir' from outer scope (line 42) (redefined-outer-name)
  test_fixture_vector_mode.py    112   W0621: Redefining name 'temp_fixtures_dir' from outer scope (line 42) (redefined-outer-name)
  test_fixture_vector_mode.py    154   W0621: Redefining name 'temp_fixtures_dir' from outer scope (line 42) (redefined-outer-name)
  test_fixture_vector_mode.py    203   W0612: Unused variable 'result' (unused-variable)
  test_fixture_vector_mode.py    214   W0621: Redefining name 'temp_fixtures_dir' from outer scope (line 42) (redefined-outer-name)
  test_fixture_vector_mode.py    257   W0621: Redefining name 'temp_fixtures_dir' from outer scope (line 42) (redefined-outer-name)


                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          validate_docstrings Failures
  Found 2 violation(s)


  File   Line   Message
 ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  .         -   ❌ Validation FAILED: 1 violation(s) in 1 file(s)
  .         -   ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/tests/test_fixture_vector_mode.py


           Summary
  Total Runners: 4
    Passed: 0
    Failed: 4
  Total Violations: 65

  Exit Code: 1 (VIOLATIONS)

```

