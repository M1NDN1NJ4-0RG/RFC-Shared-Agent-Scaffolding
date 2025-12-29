# Phase 4 Inventory Summary

**Date:** 2025-12-29  
**Phase:** 4.2 - Inventory Current Casing Deviations  
**Status:** Complete

## Overview

This document summarizes the naming convention analysis performed in Phase 4.2. It consolidates findings from automated scans and manual review.

## File Naming Violations

### Total: 21 files require renaming

- **Python:** 10 files (all using kebab-case, need snake_case)
- **PowerShell:** 11 files (all using kebab-case, need PascalCase)
- **Bash:** 0 files (already compliant with kebab-case)
- **Perl:** 0 files (already compliant with kebab-case for .pl, PascalCase for .pm)

### Python Files to Rename

All Python files currently use kebab-case and need to be converted to snake_case:

1. `scripts/validate-docstrings.py` → `scripts/validate_docstrings.py`
2. `scripts/tests/test-validate-docstrings.py` → `scripts/tests/test_validate_docstrings.py`
3. `wrappers/python3/scripts/safe-run.py` → `wrappers/python3/scripts/safe_run.py`
4. `wrappers/python3/scripts/safe-check.py` → `wrappers/python3/scripts/safe_check.py`
5. `wrappers/python3/scripts/safe-archive.py` → `wrappers/python3/scripts/safe_archive.py`
6. `wrappers/python3/scripts/preflight-automerge-ruleset.py` → `wrappers/python3/scripts/preflight_automerge_ruleset.py`
7. `wrappers/python3/tests/test-safe-run.py` → `wrappers/python3/tests/test_safe_run.py`
8. `wrappers/python3/tests/test-safe-check.py` → `wrappers/python3/tests/test_safe_check.py`
9. `wrappers/python3/tests/test-safe-archive.py` → `wrappers/python3/tests/test_safe_archive.py`
10. `wrappers/python3/tests/test-preflight-automerge-ruleset.py` → `wrappers/python3/tests/test_preflight_automerge_ruleset.py`

### PowerShell Files to Rename

All PowerShell files currently use kebab-case and need to be converted to PascalCase:

1. `wrappers/powershell/run-tests.ps1` → `wrappers/powershell/RunTests.ps1`
2. `wrappers/powershell/scripts/safe-run.ps1` → `wrappers/powershell/scripts/SafeRun.ps1`
3. `wrappers/powershell/scripts/safe-check.ps1` → `wrappers/powershell/scripts/SafeCheck.ps1`
4. `wrappers/powershell/scripts/safe-archive.ps1` → `wrappers/powershell/scripts/SafeArchive.ps1`
5. `wrappers/powershell/scripts/preflight-automerge-ruleset.ps1` → `wrappers/powershell/scripts/PreflightAutomergeRuleset.ps1`
6. `wrappers/powershell/tests/test-helpers.ps1` → `wrappers/powershell/tests/TestHelpers.ps1`
7. `wrappers/powershell/tests/safe-run-tests.ps1` → `wrappers/powershell/tests/SafeRunTests.ps1`
8. `wrappers/powershell/tests/safe-check-tests.ps1` → `wrappers/powershell/tests/SafeCheckTests.ps1`
9. `wrappers/powershell/tests/safe-archive-tests.ps1` → `wrappers/powershell/tests/SafeArchiveTests.ps1`
10. `wrappers/powershell/tests/preflight-tests.ps1` → `wrappers/powershell/tests/PreflightTests.ps1`
11. `wrappers/powershell/tests/phase3-ctrlc-probe.ps1` → `wrappers/powershell/tests/Phase3CtrlcProbe.ps1`

## Internal Symbol Naming (Functions/Variables)

### Python: ✅ Compliant

All Python functions use `snake_case` as required by PEP 8:
- `find_repo_root()`
- `detect_platform()`
- `find_safe_run_binary()`
- etc.

**No changes required.**

### PowerShell: ✅ Compliant

All PowerShell functions use `PascalCase` or `Verb-Noun` format:
- `Find-RepoRoot`
- `Detect-Platform`
- `Write-Err`
- etc.

**Variable naming:** Mixed conventions observed (`$PascalCase` and `$camelCase`). Per Phase 4 decisions, this will remain warn-only with a TODO for future enforcement.

**No immediate changes required.**

### Bash: ✅ Compliant

Bash variables follow conventions:
- Constants/env vars: `UPPER_SNAKE_CASE` (e.g., `SCRIPT_DIR`, `REPO_ROOT`)
- Local vars: `lower_snake_case` (e.g., `temp_file`, `exit_code`)
- Functions: `snake_case` (e.g., `find_repo_root`, `detect_platform`)

**No changes required.**

### Perl: ⚠️ Conventions Documented

Perl subroutines consistently use `snake_case`:
- `find_repo_root`
- `detect_platform`
- `have_cmd`
- `parse_json`
- etc.

**Convention:** `snake_case` for subroutines (standard Perl practice)

**No changes required.** Convention documented in `docs/contributing/naming-and-style.md`.

## Impact Assessment

### Low Risk
- **Internal symbols:** Already compliant, no changes needed
- **Perl files:** Already compliant, no changes needed
- **Bash files:** Already compliant, no changes needed

### Medium Risk
- **Python file renames:** 10 files, requires updates to imports and references
- **PowerShell file renames:** 11 files, requires updates to script invocations

### Reference Update Scope

After renaming, the following will need updates:
1. **CI workflows** (`.github/workflows/`)
2. **Documentation** (any code examples or file references)
3. **Import statements** (Python files that import renamed modules)
4. **Script invocations** (any place PowerShell scripts are called by name)
5. **Test discovery** (if tests rely on filename patterns)

## Next Steps (Phase 4.3)

1. Rename Python files using `git mv` (preserves history)
2. Update Python imports and references
3. Test Python wrapper suite
4. Rename PowerShell files using `git mv`
5. Update PowerShell invocations and references
6. Test PowerShell wrapper suite
7. Update all CI workflows
8. Run full test matrix

## Enforcement Plan (Phase 4.6)

The naming conventions will be enforced via:

1. **Python:** `flake8` with naming plugins (warn mode initially)
2. **PowerShell:** PSScriptAnalyzer naming rules (warn mode initially)
3. **Bash:** ShellCheck + custom validation (warn mode initially)
4. **Perl:** Perl::Critic naming rules (warn mode initially)
5. **File naming:** Enhanced version of existing `naming-kebab-case.yml` workflow

Enforcement will be converted from warn-mode to hard-fail in Phase 4.5, one language at a time.

## Related Documents

- `docs/contributing/naming-and-style.md` - Canonical naming conventions
- `docs/history/phase4-naming-violations-report.md` - Detailed file naming violations
- `docs/history/phase4-internal-symbols-report.md` - Internal symbol analysis
