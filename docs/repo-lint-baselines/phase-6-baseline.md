# Phase 6 Baseline Report — Repository Lint and Docstring Violations

**Date:** 2025-12-30
**Commit:** 303ea94
**Command:** `python3 -m tools.repo_lint check --ci --verbose`

## Executive Summary

- **Total Violations:** 388
- **Tools with Violations:** 10 of 13
- **Files Impacted:** ~50+ (across all languages)
- **Status:** Baseline established prior to remediation

## Tool Versions

| Tool | Version |
|------|---------|
| Python | 3.12.3 |
| Black | 24.10.0 |
| Ruff | 0.8.4 |
| Pylint | 3.3.2 |
| ShellCheck | 0.9.0 |
| shfmt | v3.12.0 |
| PowerShell | 7.4.13 |
| PSScriptAnalyzer | 1.24.0 |
| Perl | 5.38.2 |
| Perl::Critic | 1.156 |
| yamllint | 1.35.1 |
| tree-sitter | 0.25.1 (library) |
| tree-sitter-bash | 0.25.1 |

## Violations by Tool

| Tool | Count | Status |
|------|-------|--------|
| **Ruff** | 246 | ❌ FAILED |
| **Pylint** | 20 | ❌ FAILED |
| **validate_docstrings (PowerShell)** | 60 | ❌ FAILED |
| **yamllint** | 20 | ❌ FAILED |
| **validate_docstrings (Perl)** | 20 | ❌ FAILED |
| **ShellCheck** | 12 | ❌ FAILED |
| **Perlcritic** | 9 | ❌ FAILED |
| **shfmt** | 1 | ❌ FAILED |
| **Black** | 0 | ✅ PASSED |
| **rustfmt** | 0 | ✅ PASSED |
| **clippy** | 0 | ✅ PASSED |
| **PSScriptAnalyzer** | 0 | ✅ PASSED |
| **validate_docstrings (Python)** | 0 | ✅ PASSED |
| **validate_docstrings (Bash)** | 0 | ✅ PASSED |

---

## Python Violations

### Ruff (246 violations)

**Severity:** High - blocking linter

**Categories:**

- Unused imports (`F401`)
- Unused variables (`F841`)
- Line too long (`E501`)
- Missing docstrings (`D` series)
- Complexity issues
- Import order issues

**Impacted Areas:**

- `tools/repo_lint/` - Core linting package
- `scripts/` - Utility scripts
- `wrappers/python3/` - Python wrappers
- `conformance/` - Test fixtures

**Required Fix:**

- Remove unused imports and variables
- Fix line length violations (120 char limit per `pyproject.toml`)
- Address other Ruff violations per policy (safe fixes only in `repo-lint fix`)

### Pylint (20 violations)

**Severity:** Medium - additional quality checks

**Categories:**

- Code quality issues
- Naming convention violations
- Docstring issues
- Complexity warnings

**Impacted Areas:**

- Similar to Ruff, but with stricter quality checks

**Required Fix:**

- Address Pylint-specific quality issues
- Ensure docstrings are complete
- Refactor complex functions if necessary

### Black (0 violations)

**Status:** ✅ PASSED

All Python code is correctly formatted with Black (line-length=120).

---

## Bash Violations

### ShellCheck (12 violations)

**Severity:** Medium to High

**Categories:**

- Quoting issues
- Undefined variables
- Syntax issues
- Best practice violations

**Impacted Areas:**

- `scripts/` - Shell helper scripts
- `wrappers/bash/` - Bash wrapper scripts
- Test fixtures

**Required Fix:**

- Add proper quoting around variables
- Fix undefined variable references
- Address best practice violations

### shfmt (1 violation)

**Severity:** Low - formatting only

**Categories:**

- Indentation issues (2 spaces, -i 2)
- Code formatting inconsistencies

**Impacted Areas:**

- One or more Bash scripts with formatting issues

**Required Fix:**

- Run `shfmt -i 2 -ci -w <file>` to auto-fix

### Docstring Validation (Bash) (0 violations)

**Status:** ✅ PASSED

All Bash scripts have proper docstring headers.

---

## PowerShell Violations

### PSScriptAnalyzer (0 violations)

**Status:** ✅ PASSED

No PSScriptAnalyzer violations detected (Error severity).

### Docstring Validation (PowerShell) (60 violations)

**Severity:** High - documentation contract

**Categories:**

- Missing function documentation
- Missing parameter documentation
- Incomplete docstrings

**Impacted Files:**

- `conformance/repo-lint/vectors/fixtures/powershell/DocstringTest.ps1` (intentional test fixture)
- `scripts/tests/fixtures/powershell/EdgeCases.ps1` (intentional test fixture)
- `wrappers/powershell/scripts/PreflightAutomergeRuleset.ps1` (~8 functions)
- `wrappers/powershell/scripts/SafeArchive.ps1` (~4 functions)
- `wrappers/powershell/scripts/SafeCheck.ps1` (~2 functions)
- `wrappers/powershell/scripts/SafeRun.ps1` (~2 functions)

**Required Fix:**

- Add complete docstrings to all functions (public AND private)
- Follow PowerShell docstring contract (`.SYNOPSIS`, `.DESCRIPTION`, `.PARAMETER`, etc.)
- Test fixtures: mark with `# noqa: FUNCTION` pragma or document per contract

---

## Perl Violations

### Perl::Critic (9 violations)

**Severity:** Medium - quality checks (severity 5)

**Categories:**

- `Subroutines::ProhibitSubroutinePrototypes` (1 violation)
- `Subroutines::ProhibitExplicitReturnUndef` (8+ violations)

**Impacted Files:**

- `scripts/tests/fixtures/perl/edge_cases.pl`
- `wrappers/perl/scripts/preflight_automerge_ruleset.pl`
- `wrappers/perl/scripts/safe_run.pl`

**Required Fix:**

- Remove subroutine prototypes (use modern Perl signatures if needed)
- Replace `return undef` with `return` (Perl best practice)

### Docstring Validation (Perl) (20 violations)

**Severity:** High - documentation contract

**Categories:**

- Missing POD documentation
- Incomplete function documentation

**Impacted Files:**

- `conformance/repo-lint/vectors/fixtures/perl/docstring_test.pl` (~4 violations, intentional test fixture)
- `scripts/docstring_validators/helpers/parse_perl_ppi.pl` (1 violation)
- `scripts/tests/fixtures/perl/edge_cases.pl` (1 violation, test fixture)
- `wrappers/perl/run_tests.pl` (~4 violations)
- `wrappers/perl/scripts/preflight_automerge_ruleset.pl` (~7 violations)

**Required Fix:**

- Add POD documentation to all subroutines (public AND private)
- Follow Perl docstring contract
- Test fixtures: mark with `# noqa: FUNCTION` pragma or document per contract

---

## YAML Violations

### yamllint (20 violations)

**Severity:** Low - formatting/style warnings

**Categories:**

- `line-length` warnings (120 character limit)

**Impacted Files:**

- `.github/ISSUE_TEMPLATE/multi-phase-form.yml` (1 violation)
- `.github/workflows/drift-detection.yml` (13 violations)
- `.github/workflows/lint-and-format-checker.yml` (1 violation)
- `.github/workflows/pr-body-guardrails.yml` (5 violations)

**Required Fix:**

- Refactor long lines to fit within 120 characters
- Use YAML multiline strings where appropriate (`>`, `|`)
- May require splitting complex expressions

---

## Rust Violations

### rustfmt (0 violations)

**Status:** ✅ PASSED

Rust code is properly formatted.

### clippy (0 violations)

**Status:** ✅ PASSED

No Clippy lint issues detected.

---

## Remediation Plan

Per the Phase 6 completion instructions, violations will be remediated in this order:

1. **Python** (Black ✅ / Ruff ❌ / Pylint ❌ / Docstrings ✅)
   - Fix Ruff violations (246)
   - Fix Pylint violations (20)

2. **Bash** (ShellCheck ❌ / shfmt ❌ / Docstrings ✅)
   - Fix ShellCheck violations (12)
   - Fix shfmt violations (1)

3. **PowerShell** (PSScriptAnalyzer ✅ / Docstrings ❌)
   - Fix docstring violations (60)

4. **Perl** (Perl::Critic ❌ / Docstrings ❌)
   - Fix Perl::Critic violations (9)
   - Fix docstring violations (20)

5. **YAML** (yamllint ❌)
   - Fix yamllint violations (20)

---

## Notes

- **Test Fixtures:** Some violations are in intentional test fixtures (e.g., `conformance/repo-lint/vectors/fixtures/`) designed to trigger violations for vector testing. These may be exempt or require `# noqa` pragmas.

- **Auto-Fix Policy:** Per Phase 0 Item 0.9.1, `repo-lint fix` may only apply:
  - FORMAT.BLACK (all Python files)
  - FORMAT.SHFMT (all Bash files)
  - LINT.RUFF.SAFE (safe Ruff fixes only, no unsafe fixes)

- **Docstring Enforcement:** Per Phase 3 Item 3.7.3, ALL symbols (public and private) require documentation. No implicit skipping.

- **Flake8 Migration:** Ruff has replaced Flake8 per Phase 0 Item 0.8.1. The `.flake8` file and Flake8 CI steps will be removed after remediation is complete.

---

## Appendix: Full Baseline Output

See `/tmp/baseline-output.txt` for the complete unabridged output from `repo-lint check --ci`.

**Command used:**

```bash
python3 -m tools.repo_lint check --ci --verbose
```

**Exit Code:** 1 (violations found)

---

**Next Steps:** Proceed with language-by-language remediation as outlined above.
