# Naming Convention Violations Report

**Generated:** 2025-12-29
**Phase:** 4.2 - Inventory Current Casing Deviations

## Summary

- **Total File Naming Violations:** 21
  - Python: 10
  - PowerShell: 11
  - Bash: 0
  - Perl: 0

## Python File Naming Violations

**Expected:** `snake_case.py`

- `scripts/tests/test-validate-docstrings.py` - Expected snake_case, got: test-validate-docstrings
- `scripts/validate-docstrings.py` - Expected snake_case, got: validate-docstrings
- `wrappers/python3/scripts/preflight-automerge-ruleset.py` - Expected snake_case, got: preflight-automerge-ruleset
- `wrappers/python3/scripts/safe-archive.py` - Expected snake_case, got: safe-archive
- `wrappers/python3/scripts/safe-check.py` - Expected snake_case, got: safe-check
- `wrappers/python3/scripts/safe-run.py` - Expected snake_case, got: safe-run
- `wrappers/python3/tests/test-preflight-automerge-ruleset.py` - Expected snake_case, got: test-preflight-automerge-ruleset
- `wrappers/python3/tests/test-safe-archive.py` - Expected snake_case, got: test-safe-archive
- `wrappers/python3/tests/test-safe-check.py` - Expected snake_case, got: test-safe-check
- `wrappers/python3/tests/test-safe-run.py` - Expected snake_case, got: test-safe-run

## PowerShell File Naming Violations

**Expected:** `PascalCase.ps1`

- `wrappers/powershell/run-tests.ps1` - Expected PascalCase, got: run-tests
- `wrappers/powershell/scripts/preflight-automerge-ruleset.ps1` - Expected PascalCase, got: preflight-automerge-ruleset
- `wrappers/powershell/scripts/safe-archive.ps1` - Expected PascalCase, got: safe-archive
- `wrappers/powershell/scripts/safe-check.ps1` - Expected PascalCase, got: safe-check
- `wrappers/powershell/scripts/safe-run.ps1` - Expected PascalCase, got: safe-run
- `wrappers/powershell/tests/phase3-ctrlc-probe.ps1` - Expected PascalCase, got: phase3-ctrlc-probe
- `wrappers/powershell/tests/preflight-tests.ps1` - Expected PascalCase, got: preflight-tests
- `wrappers/powershell/tests/safe-archive-tests.ps1` - Expected PascalCase, got: safe-archive-tests
- `wrappers/powershell/tests/safe-check-tests.ps1` - Expected PascalCase, got: safe-check-tests
- `wrappers/powershell/tests/safe-run-tests.ps1` - Expected PascalCase, got: safe-run-tests
- `wrappers/powershell/tests/test-helpers.ps1` - Expected PascalCase, got: test-helpers

## Next Steps

File renames will be applied in Phase 4.3 using `git mv` to preserve history.

