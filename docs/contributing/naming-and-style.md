# Naming and Style Conventions

**Status:** Canonical source of truth for naming and casing standards (Phase 4)  
**Last Updated:** 2025-12-29  
**Enforcement:** Warn-first rollout (Phase 4), full enforcement in Phase 4.5

## Overview

This document defines the naming and casing conventions for all code, scripts, and files in the RFC-Shared-Agent-Scaffolding repository. These standards ensure consistency across multiple languages while respecting language-specific ecosystem conventions.

**Key Principle:** Script files follow their respective language naming standards. Non-script files (docs, configs, general repo files) use kebab-case by default.

---

## General File Naming (Non-Script Files)

**Convention:** `kebab-case`

Applies to:
- Documentation files: `contributing-guide.md`, `naming-and-style.md`
- Configuration files: `.perlcriticrc`, `.yamllint`
- Data files: `vectors.json`
- General repository files: `README.md`, `CONTRIBUTING.md`

**Pattern:** `^[a-z0-9]+(-[a-z0-9]+)*\.[a-z0-9]+$`

Examples:
- ✅ `contributing-guide.md`
- ✅ `wrapper-discovery.md`
- ✅ `safe-run-tests.ps1`
- ❌ `contributing_guide.md` (underscore)
- ❌ `ContributingGuide.md` (PascalCase)

---

## Script File Naming

### Python Scripts

**Convention:** `snake_case.py`

Applies to:
- Python modules: `safe_run.py`, `test_helpers.py`
- Python executables: `validate_docstrings.py`

**Pattern:** `^[a-z0-9]+(_[a-z0-9]+)*\.py$`

**Rationale:** Python's PEP 8 style guide specifies snake_case for module names.

**Current Transition:** Files currently use kebab-case (`safe_run.py`). Will transition in Phase 4.3.

Examples:
- ✅ `safe_run.py`
- ✅ `test_safe_check.py`
- ✅ `preflight_automerge_ruleset.py`
- ❌ `safe_run.py` (kebab-case, legacy)
- ❌ `SafeRun.py` (PascalCase)

### PowerShell Scripts

**Convention:** `PascalCase.ps1` (Option A - Selected)

Applies to:
- PowerShell scripts: `SafeRun.ps1`, `TestHelpers.ps1`
- PowerShell modules: `SafeArchive.ps1`

**Pattern:** `^[A-Z][a-zA-Z0-9]*\.ps1$`

**Rationale:** PowerShell community convention for script files, matches function naming.

**Current Transition:** Files currently use kebab-case (`safe-run.ps1`). Will transition in Phase 4.3.

Examples:
- ✅ `SafeRun.ps1`
- ✅ `TestHelpers.ps1`
- ✅ `PreflightAutomergeRuleset.ps1`
- ❌ `safe-run.ps1` (kebab-case, legacy)
- ❌ `safe_run.ps1` (snake_case)

### Bash Scripts

**Convention:** `kebab-case.sh`

Applies to:
- Bash scripts: `safe-run.sh`, `test-helpers.sh`
- Shell utilities: `verify-repo-references.sh`

**Pattern:** `^[a-z0-9]+(-[a-z0-9]+)*\.sh$`

**Rationale:** Common Unix/Linux convention for shell scripts.

Examples:
- ✅ `safe-run.sh`
- ✅ `test-helpers.sh`
- ✅ `preflight-automerge-ruleset.sh`
- ❌ `safe_run.sh` (underscore)
- ❌ `SafeRun.sh` (PascalCase)

### Perl Scripts

**Convention:** `kebab-case.pl`

Applies to:
- Perl scripts: `safe-run.pl`, `test-helpers.pl`
- Perl modules: Use standard Perl module naming (`TestUtil.pm` → `CamelCase.pm`)

**Pattern (scripts):** `^[a-z0-9]+(-[a-z0-9]+)*\.pl$`  
**Pattern (modules):** `^[A-Z][a-zA-Z0-9]*\.pm$`

**Rationale:** Perl scripts commonly use kebab-case; modules use CamelCase per Perl conventions.

Examples (scripts):
- ✅ `safe-run.pl`
- ✅ `preflight-automerge-ruleset.pl`
- ❌ `safe_run.pl` (underscore)

Examples (modules):
- ✅ `TestUtil.pm`
- ✅ `SafeRun.pm`
- ❌ `test-util.pm` (kebab-case for modules)

---

## Internal Symbol Naming

### Python

**Functions and Variables:** `snake_case`

Per PEP 8:
- Functions: `find_repo_root()`, `detect_platform()`
- Variables: `script_dir`, `repo_root`, `is_windows`
- Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`, `DEFAULT_TIMEOUT`)
- Classes: `PascalCase` (e.g., `SafeRunWrapper`)

**Enforcement:** Automated via `flake8`, `pylint`, and `black`.

Examples:
- ✅ `def find_safe_run_binary():`
- ✅ `repo_root = Path(...)`
- ✅ `MAX_SNIPPET_LINES = 100`
- ❌ `def findSafeRunBinary():` (camelCase)
- ❌ `RepoRoot = Path(...)` (PascalCase)

### PowerShell

**Functions:** `PascalCase` (Verb-Noun format preferred)

Per PowerShell community conventions:
- Functions: `Find-RepoRoot`, `Detect-Platform`, `Write-Err`
- Approved verbs: `Get-`, `Set-`, `Find-`, `Write-`, `Invoke-`

**Variables:** Current practice allowed; eventual TODO to enforce

Current state:
- Mix of `$PascalCase` and `$camelCase` observed
- **Phase 4 decision:** Allow current conventions, add warnings only
- **Phase 4.5 decision:** Keep variable-case as warnings, track TODO for future enforcement

**Enforcement:** PSScriptAnalyzer for functions; variable naming deferred to future phase.

Examples (functions):
- ✅ `function Find-RepoRoot { }`
- ✅ `function Detect-Platform { }`
- ✅ `function Write-Err([string]$Msg) { }`
- ❌ `function find_repo_root { }` (snake_case)
- ❌ `function findRepoRoot { }` (camelCase)

Examples (variables - current state):
- ✅ `$RepoRoot` (allowed)
- ✅ `$repoRoot` (allowed)
- ⚠️ Variable naming will be standardized in future phase

### Bash

**Constants and Environment Variables:** `UPPER_SNAKE_CASE`  
**Local Variables:** `lower_snake_case`

Per common shell scripting conventions:
- Constants/env/exported vars: `SCRIPT_DIR`, `REPO_ROOT`, `IS_WINDOWS`
- Local variables: `binary_path`, `temp_dir`, `exit_code`
- Functions: `snake_case` (e.g., `find_repo_root`, `detect_platform`)

**Enforcement:** ShellCheck for obvious violations; warn-first rollout.

Examples:
- ✅ `SCRIPT_DIR="$(pwd)"`
- ✅ `REPO_ROOT="/path/to/repo"`
- ✅ `local temp_file="/tmp/data"`
- ✅ `find_repo_root() { ... }`
- ❌ `scriptDir="$(pwd)"` (camelCase for constant)
- ❌ `TEMP_FILE="/tmp/data"` (constant style for local var)

### Perl

**Convention:** To be finalized in Phase 4.2/4.4

Current observations:
- Functions: Mix of `snake_case` and `camelCase`
- Variables: Mix of `$snake_case` and `$camelCase`

**Phase 4 plan:**
- Document current state in Item 4.2
- Choose canonical conventions in Item 4.4.4
- Apply as warn-first, then enforce in Phase 4.5.6

---

## Rust Naming

**Convention:** Standard Rust naming per rustfmt and clippy

- Functions/modules: `snake_case`
- Types/structs/enums: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Crate names: `snake_case` (e.g., `safe_run`)

**Enforcement:** Automated via `rustfmt` and `clippy` in CI.

Examples:
- ✅ `fn find_binary() { }`
- ✅ `struct SafeRunConfig { }`
- ✅ `const MAX_RETRIES: u32 = 3;`

---

## CI Enforcement Strategy

### Phase 4: Warn-First Rollout

Goal: Establish standards and identify violations without breaking CI.

**Approach:**
1. Add new naming validation jobs to CI
2. Set to **warn mode** or **no-new-violations mode**
3. Generate violation reports for review
4. Allow time for fixes before strict enforcement

**Phase 4 Enforcement Level:**
- Python: `flake8` and `pylint` warnings enabled
- PowerShell: PSScriptAnalyzer warnings for functions; variable-case warnings only
- Bash: ShellCheck warnings for obvious violations
- Perl: Perl::Critic warnings (conventions TBD)

### Phase 4.5: Full Enforcement Conversion

Goal: Convert warnings to hard pass/fail, one language at a time.

**Rollout Order:**
1. Python (Item 4.5.3)
2. PowerShell (Item 4.5.4) - functions + filenames; variables remain warn-only
3. Bash (Item 4.5.5)
4. Perl (Item 4.5.6) - after conventions finalized

**Success Criteria (per language):**
- All naming violations fixed
- CI passes with hard enforcement enabled
- No new violations introduced

---

## Existing Enforcement

### Language-Specific Naming Validation (Phase 4+)

**Workflow:** `.github/workflows/naming-enforcement.yml`

**Scope:**
- All tracked files in repository
- Language-specific rules applied per file extension

**Validation Rules:**
- Python (`.py`): `snake_case` pattern
- PowerShell (`.ps1`): `PascalCase` pattern
- Bash (`.sh`, `.bash`, `.zsh`): `kebab-case` pattern
- Perl scripts (`.pl`): `kebab-case` pattern
- Perl modules (`.pm`): `PascalCase` pattern

**Current Status (Phase 4):** WARN mode
- Violations are reported in CI output
- Build passes even with violations
- Gives contributors time to fix violations

**Future Status (Phase 4.5):** ENFORCE mode
- Violations will fail CI
- Blocks merge until violations are fixed
- Conversion will happen one language at a time

### Legacy Kebab-Case Enforcement (Pre-Phase 4)

**Status:** Replaced by `naming-enforcement.yml` in Phase 4

**Historical scope:**
- Applied uniform kebab-case to all script files
- Did not respect language-specific conventions
- Removed in favor of language-aware validation

### Language-Specific Linters

**Workflow:** `.github/workflows/lint-and-format-checker.yml`

**Current Enforcement:**
- Python: `black`, `flake8`, `pylint`
- Bash: `shellcheck`, `shfmt` (warn-only)
- PowerShell: PSScriptAnalyzer (Error severity only)
- Perl: Perl::Critic (warn-only, severity 5)

**Phase 4 Changes:**
- Add explicit naming checks to each linter
- Align severity levels with warn-first strategy
- Add unified naming validation job

---

## Migration Plan

### Item 4.3: File Renaming

**Python:**
- `safe_run.py` → `safe_run.py`
- `safe_check.py` → `safe_check.py`
- `safe_archive.py` → `safe_archive.py`
- `preflight_automerge_ruleset.py` → `preflight_automerge_ruleset.py`
- All test files: `test-*.py` → `test_*.py`

**PowerShell:**
- `safe-run.ps1` → `SafeRun.ps1`
- `safe-check.ps1` → `SafeCheck.ps1`
- `safe-archive.ps1` → `SafeArchive.ps1`
- `preflight-automerge-ruleset.ps1` → `PreflightAutomergeRuleset.ps1`
- `test-helpers.ps1` → `TestHelpers.ps1`
- All test files: `*-tests.ps1` → `*Tests.ps1`

**Bash:** No changes (already kebab-case compliant)

**Perl:** No changes (already kebab-case compliant)

### Item 4.4: Symbol Renaming

**Python:** Already compliant (snake_case throughout)

**PowerShell:** Functions already compliant (PascalCase); variables deferred

**Bash:** Already compliant (UPPER_SNAKE_CASE for constants, lower_snake_case for locals)

**Perl:** TBD based on Item 4.2 inventory

---

## Rationale

### Why Language-Specific Conventions?

Different languages have different ecosystem norms:
- **Python PEP 8** is universally accepted in the Python community
- **PowerShell** community strongly prefers PascalCase for scripts and functions
- **Bash/Shell** scripts traditionally use kebab-case
- **Perl** scripts use kebab-case; modules use CamelCase

Forcing a single convention across all languages would:
- Violate ecosystem norms
- Reduce code readability for language experts
- Create friction with external tools and linters

### Why Kebab-Case for Non-Script Files?

Kebab-case for docs/config provides:
- Consistency with existing repository structure
- URL-friendly naming (important for web-based docs)
- Clear visual distinction from code files
- Compatibility with most filesystem conventions

---

## Future Considerations

### PowerShell Variable Naming

**Current State:** Mixed conventions allowed  
**TODO:** Add to Phase 4.5.4 or later phase:
- Choose canonical convention (`$PascalCase` or `$camelCase`)
- Add PSScriptAnalyzer rule
- Run as warn-only initially
- Convert to enforcement once clean

### Perl Naming

**Current State:** Conventions to be documented in Item 4.2  
**TODO:** Item 4.5.6 will finalize and enforce

### Test File Naming

**Current Patterns:**
- Python: `test_*.py` (pytest convention) or `test-*.py` (legacy)
- PowerShell: `*Tests.ps1` or `*-tests.ps1` (legacy)
- Bash: `test-*.sh` (common convention)
- Perl: `*.t` (standard Perl test extension)

**Phase 4 alignment:** Align test file naming with script file conventions per language.

---

## References

- [PEP 8 – Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [PowerShell Practice and Style Guide](https://poshcode.gitbook.io/powershell-practice-and-style/)
- [Google Shell Style Guide](https://google.github.io/styleguide/shellguide.html)
- [Perl Best Practices (Damian Conway)](http://shop.oreilly.com/product/9780596001735.do)
- [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/naming.html)

---

## Document History

- **2025-12-29:** Created as part of Phase 4, Item 4.1.1
  - Locked naming conventions per Phase 4 decisions
  - Defined warn-first enforcement strategy
  - Documented migration plan for file and symbol renaming
