# Canonical Directory Structure

This document defines the required directory structure for all language bundles in the `wrappers` repository.

## Purpose

To ensure consistency, maintainability, and prevent path drift across language implementations, all language bundles **MUST** follow the identical directory structure defined below.

## Canonical Structure

All language bundles are located under:
```
wrappers/<language>/
```

Each language bundle **MUST** have the following structure:

```
wrappers/<language>/
  ├── scripts/          # Actual implementation scripts
  │   ├── safe-run.*
  │   ├── safe-check.*
  │   ├── safe-archive.*
  │   └── preflight-automerge-ruleset.*
  ├── tests/            # Test files
  │   └── ...
  ├── run-tests.*       # Test runner (executable)
  └── README.md   # Optional: per-language test documentation
```

### Language-Specific Extensions

Each language uses its conventional file extension:

| Language    | Extension | Example                  |
|-------------|-----------|--------------------------|
| Bash        | `.sh`     | `safe-run.sh`            |
| Perl        | `.pl`     | `safe_run.pl`            |
| Python 3    | `.py`     | `safe_run.py`            |
| PowerShell  | `.ps1`    | `safe-run.ps1`           |

### Naming Conventions

- **All languages**: Use hyphens (kebab-case) for all script names for consistency
  - Bash example: `safe-run.sh`, `preflight-automerge-ruleset.sh`
  - Perl example: `safe_run.pl`, `preflight_automerge_ruleset.pl`
  - Python 3 example: `safe_run.py`, `preflight_automerge_ruleset.py`
  - PowerShell example: `safe-run.ps1`, `preflight-automerge-ruleset.ps1`

## What Changed (Migration from Old Structure)

### Bash (Before → After)

**Before:**
```
scripts/bash/
  ├── scripts/bash/     # ❌ Extra nesting
  │   └── *.sh
  └── tests/bash/       # ❌ Extra nesting
      └── *.sh
```

**After:**
```
scripts/bash/
  ├── scripts/          # ✅ Flat
  │   └── *.sh
  └── tests/            # ✅ Flat
      └── *.sh
```

### PowerShell (Before → After)

**Before:**
```
scripts/powershell/
  ├── scripts/powershell/   # ❌ Extra nesting
  │   └── *.ps1
  └── tests/                # ✅ Already flat
      └── *.ps1
```

**After:**
```
scripts/powershell/
  ├── scripts/              # ✅ Flat
  │   └── *.ps1
  └── tests/                # ✅ Flat
      └── *.ps1
```

### Perl & Python3

These languages already followed the canonical structure and required no changes.

## Validation

### Automated Validation

The structure is validated automatically via CI using `scripts/validate-structure.sh`.

To run locally:
```bash
./scripts/validate-structure.sh
```

### CI Enforcement

The workflow `.github/workflows/structure-validation.yml` runs on every PR that modifies:
- `wrappers/**`
- `scripts/validate-structure.sh`
- The workflow file itself

PRs **CANNOT** merge if the structure validation fails.

## Required Files

Each language bundle **MUST** include:

### Scripts Directory (`scripts/`)
All implementation files:
- `safe-run.*` - Safe command execution wrapper
- `safe-check.*` - Contract verification script
- `safe-archive.*` - Failure log archiving utility
- `preflight-automerge-ruleset.*` - GitHub ruleset preflight check

### Tests Directory (`tests/`)
All test files and test utilities.

### Test Runner (`run-tests.*`)
An executable script that runs the full test suite for that language.

**Naming:**
- Bash/Perl: `run-tests.sh`
- Python 3: `run-tests.sh` or invoke via `python -m unittest discover`
- PowerShell: `run-tests.ps1`

## Prohibited Patterns

The following patterns are **NOT ALLOWED** and will cause CI to fail:

❌ **Nested language directories:**
```
scripts/<language>/scripts/<language>/   # WRONG
scripts/<language>/tests/<language>/     # WRONG
```

✅ **Correct:**
```
scripts/<language>/scripts/              # RIGHT
scripts/<language>/tests/                # RIGHT
```

## Rationale

### Why This Matters

1. **Consistency**: All languages follow the same layout, reducing cognitive load
2. **Predictability**: CI, tooling, and documentation can rely on known paths
3. **Maintainability**: Path references are simpler and less error-prone
4. **Future-proofing**: When Rust canonical tool is introduced, wrappers will have identical relative paths

### Why We Flattened

The old nested structure (`scripts/<language>/scripts/<language>/`) was:
- Redundant and confusing
- Inconsistent across languages (Bash/PowerShell nested, Perl/Python flat)
- Harder to reference in tests and CI
- A source of path drift

The new flat structure ensures:
- All languages are identical
- Paths are simpler and more maintainable
- Less room for error

## References

- **Epic:** [#33 - Rust Canonical Tool + Thin Compatibility Wrappers](https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/issues/33)
- **Validation Script:** `scripts/validate-structure.sh`
- **CI Workflow:** `.github/workflows/structure-validation.yml`
