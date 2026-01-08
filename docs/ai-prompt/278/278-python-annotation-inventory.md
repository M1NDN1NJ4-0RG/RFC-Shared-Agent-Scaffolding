# Issue #278 - Python Annotation Inventory

**Created:** 2026-01-07 **Purpose:** Comprehensive inventory of Python files and current typing/linting state for Issue
#278

## Executive Summary

- - **Total Python files:** 84 - **Product/library code:** 35 files (tools/repo_lint/*, scripts/docstring_validators/*)
  - **CLI/utility scripts:** 11 files (scripts/*.py, wrappers/python3/scripts/*.py) - **Tests:** 30 files (**/test_*.py,
  **/tests/*.py) - **Fixtures:** 8 files (intentional violations, test data)

## Python Toolchain Versions

### Current Environment (2026-01-07)

- - **Python:** 3.12.12 - **black:** 25.12.0 - **ruff:** 0.14.10 - **pylint:** 4.0.4 - **astroid:** 4.0.3

### CI/Pinned Versions (from pyproject.toml)

Per `pyproject.toml` `[project.optional-dependencies]` `lint` section:

- - **black:** 24.10.0 (pinned) - **ruff:** 0.8.4 (pinned) - **pylint:** 3.3.2 (pinned) - **yamllint:** 1.35.1 (pinned)

**Note:** Current environment has newer versions than pinned CI versions. This may cause inconsistencies.

## Python Files Classification

### Product/Library Code (35 files)

#### `tools/repo_lint/` Package (29 files)

Core repo-lint implementation:

1. `tools/repo_lint/__init__.py`
2. `tools/repo_lint/__main__.py`
3. `tools/repo_lint/cli.py`
4. `tools/repo_lint/cli_argparse.py`
5. `tools/repo_lint/common.py`
6. `tools/repo_lint/config_validator.py`
7. `tools/repo_lint/doctor.py`
8. `tools/repo_lint/forensics.py`
9. `tools/repo_lint/policy.py`
10. `tools/repo_lint/repo_utils.py`
11. `tools/repo_lint/reporting.py`
12. `tools/repo_lint/unsafe_fixers.py`
13. `tools/repo_lint/yaml_loader.py`

Environment management (2 files):
14. `tools/repo_lint/env/__init__.py`
15. `tools/repo_lint/env/venv_resolver.py`

Installation (3 files):
16. `tools/repo_lint/install/__init__.py`
17. `tools/repo_lint/install/install_helpers.py`
18. `tools/repo_lint/install/version_pins.py`

Runners (8 files):
19. `tools/repo_lint/runners/__init__.py`
20. `tools/repo_lint/runners/base.py`
21. `tools/repo_lint/runners/bash_runner.py`
22. `tools/repo_lint/runners/naming_runner.py`
23. `tools/repo_lint/runners/perl_runner.py`
24. `tools/repo_lint/runners/powershell_runner.py`
25. `tools/repo_lint/runners/python_runner.py`
26. `tools/repo_lint/runners/rust_runner.py`
27. `tools/repo_lint/runners/yaml_runner.py`

UI/Reporting (4 files):
28. `tools/repo_lint/ui/__init__.py`
29. `tools/repo_lint/ui/console.py`
30. `tools/repo_lint/ui/reporter.py`
31. `tools/repo_lint/ui/theme.py`

#### `scripts/docstring_validators/` Package (6 files)

Docstring validation implementation:

1. `scripts/docstring_validators/__init__.py`
2. `scripts/docstring_validators/bash_validator.py`
3. `scripts/docstring_validators/common.py`
4. `scripts/docstring_validators/helpers/bash_treesitter.py`
5. `scripts/docstring_validators/perl_validator.py`
6. `scripts/docstring_validators/powershell_validator.py`
7. `scripts/docstring_validators/python_validator.py`
8. `scripts/docstring_validators/rust_validator.py`
9. `scripts/docstring_validators/yaml_validator.py`

**Note:** This is a key migration target for Phase 3.4 (docstring validation consolidation).

### CLI/Utility Scripts (11 files)

#### Repository Scripts (2 files)

1. `scripts/add_future_annotations.py` - Adds `from __future__ import annotations` to Python files
2. `scripts/bootstrap_watch.py` - Bootstrap toolchain watcher
3. `scripts/validate_docstrings.py` - Standalone docstring validator (migration target for Phase 3.4)

#### Wrapper Scripts (5 files)

1. `wrappers/python3/run_tests.py` - Python test runner
2. `wrappers/python3/scripts/preflight_automerge_ruleset.py` - Pre-merge validation
3. `wrappers/python3/scripts/safe_archive.py` - Safe archiving wrapper
4. `wrappers/python3/scripts/safe_check.py` - Safe check wrapper
5. `wrappers/python3/scripts/safe_run.py` - Safe run wrapper

### Tests (30 files)

#### `scripts/tests/` (4 files)

1. `scripts/tests/test_add_future_annotations.py`
2. `scripts/tests/test_bootstrap_repo_lint_toolchain.py`
3. `scripts/tests/test_symbol_discovery.py`
4. `scripts/tests/test_validate_docstrings.py`

#### `tools/repo_lint/tests/` (22 files)

1. `tools/repo_lint/tests/__init__.py`
2. `tools/repo_lint/tests/test_base_runner.py`
3. `tools/repo_lint/tests/test_bash_runner.py`
4. `tools/repo_lint/tests/test_cli_dispatch.py`
5. `tools/repo_lint/tests/test_exit_codes.py`
6. `tools/repo_lint/tests/test_fixture_isolation_matrix.py`
7. `tools/repo_lint/tests/test_fixture_vector_mode.py`
8. `tools/repo_lint/tests/test_install_helpers.py`
9. `tools/repo_lint/tests/test_integration.py`
10. `tools/repo_lint/tests/test_output_format.py`
11. `tools/repo_lint/tests/test_perl_runner.py`
12. `tools/repo_lint/tests/test_phase_2_7_features.py`
13. `tools/repo_lint/tests/test_powershell_runner.py`
14. `tools/repo_lint/tests/test_python_runner.py`
15. `tools/repo_lint/tests/test_rust_runner.py`
16. `tools/repo_lint/tests/test_unsafe_fixes.py`
17. `tools/repo_lint/tests/test_vectors.py`
18. `tools/repo_lint/tests/test_venv_resolver.py`
19. `tools/repo_lint/tests/test_yaml_runner.py`

#### `wrappers/python3/tests/` (4 files)

1. `wrappers/python3/tests/test_preflight_automerge_ruleset.py`
2. `wrappers/python3/tests/test_safe_archive.py`
3. `wrappers/python3/tests/test_safe_check.py`
4. `wrappers/python3/tests/test_safe_run.py`

### Fixtures (8 files)

Intentional violations for testing:

1. `conformance/repo-lint/fixtures/violations/python/missing_docstring.py`
2. `conformance/repo-lint/unsafe-fix-fixtures/python/google_style_docstrings.py`
3. `conformance/repo-lint/vectors/fixtures/python/docstring_test.py`
4. `scripts/tests/fixtures/python/edge_cases.py`
5. `tools/repo_lint/tests/fixtures/python/python-naming-violations.py`
6. `tools/repo_lint/tests/fixtures/python/python_all_docstring_violations.py`
7. `tools/repo_lint/tests/fixtures/python/python_black_violations.py`
8. `tools/repo_lint/tests/fixtures/python/python_pylint_violations.py`
9. `tools/repo_lint/tests/fixtures/python/python_ruff_violations.py`

## Existing Exclusions

From `pyproject.toml` (`[tool.black]`, `[tool.ruff]`, `[tool.pylint.master]`):

**Black/Ruff excludes:**

```python
exclude = [
    ".git",
    ".venv",
    ".venv-lint",
    "dist",
    "tools/repo_lint/tests/fixtures",
    "conformance/repo-lint/fixtures",
    "conformance/repo-lint/vectors",
    "conformance/repo-lint/unsafe-fix-fixtures",
    "scripts/tests/fixtures",
]
```

**Pylint ignore-paths:**

```python
ignore-paths = [
    "tools/repo_lint/tests/fixtures/.*",
    "conformance/repo-lint/fixtures/.*",
    "conformance/repo-lint/vectors/.*",
    "conformance/repo-lint/unsafe-fix-fixtures/.*",
    "scripts/tests/fixtures/.*",
]
```

**Rationale:** Fixture files contain intentional violations for testing purposes.

## Current Python Lint/Docstring Rules

### Linting Tools (from `conformance/repo-lint/repo-lint-linting-rules.yaml`)

**Python linters:**

1. 1. **black** (v24.10.0) - Code formatter (fix-capable) 2. **ruff** (v0.8.4) - Fast linter replacing flake8/isort
   (fix-capable) 3. **pylint** (v3.3.2) - Comprehensive code analyzer (check-only)

**Config location:** `pyproject.toml`

### Docstring Rules (from `conformance/repo-lint/repo-lint-docstring-rules.yaml`)

**Python docstring requirements:**

- - Public functions must have docstrings - Docstrings must include Purpose section - Docstrings should document
  parameters and return values
- Use reST-style field lists (`:param:`, `:returns:`, `:raises:`)

**Validator script:** `scripts/validate_docstrings.py`

**Style:** reStructuredText (reST) per PEP 287

### Naming Conventions (from `docs/contributing/naming-and-style.md`)

**Python symbol naming (PEP 8):**

- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Classes: `PascalCase`
- File names: `snake_case.py`

**Enforcement:** Automated via ruff (N* rules) and pylint

### Current Ruff Configuration (from `pyproject.toml`)

**Enabled rules:**

```python
select = [
    "E",   # pycodestyle errors
    "F",   # pyflakes
    "W",   # pycodestyle warnings
    "I",   # isort
    "N",   # pep8-naming
    "UP",  # pyupgrade
]
```

**Ignored rules (for Python 3.8+ compatibility):**

```python
ignore = ["UP006", "UP007", "UP035"]
# UP006: Use `list` instead of `List` - keep typing imports for 3.8
# UP007: Use `X | Y` instead of `Optional[X]` - keep Optional for 3.8
# UP035: deprecated-import - allow typing imports for compatibility
```

**Key observation:** Ruff is already configured to PRESERVE `Optional[T]` syntax and IGNORE PEP 604 `T | None` suggestions. This aligns perfectly with Locked Decision #4 (prefer `Optional[T]` for compatibility).

### Pylint Configuration (from `pyproject.toml`)

**Disabled checks:**

```python
disable = [
    "duplicate-code",
    "too-few-public-methods",
    "too-many-return-statements",
    "no-else-return",
    "global-statement",
    "unused-argument",
    "import-outside-toplevel",
    "broad-exception-caught",
    "consider-using-with",
    "subprocess-run-check",
    "invalid-name",
    "missing-class-docstring",      # ← Docstrings NOT enforced by pylint
    "missing-function-docstring",   # ← Docstrings NOT enforced by pylint
    "inconsistent-return-statements",
    "too-many-locals",
    "too-many-branches",
    "too-many-statements"
]
```

**Key observation:** Pylint's docstring checks are DISABLED. Current docstring enforcement happens via `scripts/validate_docstrings.py` and `repo-lint`.

## Current Python Contract Documentation

**Canonical docs:**

1. **`docs/contributing/docstring-contracts/python.md`** - Python docstring contract (PEP 257 + PEP 287 reST)
   - - Module-level docstrings required
   - reST field format (`:Purpose:`, `:Examples:`, `:Exit Codes:`, etc.)
   - Function docstrings with `:param:`, `:returns:`, `:raises:`

2. **`docs/contributing/naming-and-style.md`** - Naming conventions
   - - Python section defines snake_case for functions/variables - PascalCase for classes - UPPER_SNAKE_CASE for
     constants

3. **`pyproject.toml`** - Tool configurations
   - - Black, Ruff, Pylint settings - Line length: 120 - Target: Python 3.8+

4. **`conformance/repo-lint/repo-lint-linting-rules.yaml`** - Linting tool definitions
5. **`conformance/repo-lint/repo-lint-docstring-rules.yaml`** - Docstring validation rules

## Gap Analysis: Current vs. Issue #278 Requirements

### PEP 526 Variable Annotations

**Current state:** NOT enforced **Issue #278 requirement:** Enforce module-level and class attribute annotations
(MANDATORY baseline) **Gap:** Need to add enforcement tooling

### Function Annotations

**Current state:** NOT enforced
**Issue #278 requirement:** All functions MUST have parameter + return annotations (including `-> None`)
**Gap:** Need to add enforcement tooling (likely via Ruff ANN* rules)

### Docstring `:rtype:` Enforcement

**Current state:** NOT enforced
**Issue #278 requirement:** Functions returning non-None MUST include `:rtype:` in docstring
**Gap:** Need to extend docstring validator

### Type Annotation Style (Optional vs. Union)

**Current state:** Ruff already ignores UP007 (keeps `Optional[T]` allowed)
**Issue #278 requirement:** Prefer `Optional[T]`, allow `T | None` (Locked Decision #4)
**Status:** ✅ Already aligned! No changes needed.

### `*args`/`**kwargs` Typing

**Current state:** NOT enforced
**Issue #278 requirement:** `*args: Any, **kwargs: Any` as default
**Gap:** Need to add enforcement (likely via Ruff ANN rules)

## Recommended Tooling Strategy (Preliminary)

Based on this inventory:

1. 1. **Enable Ruff ANN* rules** (flake8-annotations) for function/parameter annotations - This is the PREFERRED path
   vs. custom AST checker (less custom code)
   - Ruff supports `ANN001` (missing param annotation), `ANN201` (missing return annotation), etc.

2. **Extend `scripts/docstring_validators/python_validator.py`** to check for `:rtype:`
   - - This validator already parses Python docstrings
   - Add check: if function returns non-None, docstring MUST include `:rtype:`

3. 3. **PEP 526 enforcement:** Custom AST checker OR Ruff extension (TBD in Phase 3) - Check module-level assignments -
   Check class attributes
   - Flag ambiguous empty literals (`{}`, `[]`, etc.) without annotations

4. **Phase 3.4 migration:** Move `scripts/docstring_validators/*` into `tools/repo_lint/docstrings/`
   - - Consolidate as first-class repo-lint internal module
   - Remove subprocess dependency on `scripts/validate_docstrings.py`

## Next Steps

Per Issue #278 Phase 0:

- - [x] Phase 0.1: Snapshot repo + tooling (COMPLETE) - [x] Phase 0.2: Inventory all Python files (COMPLETE - this
  document)

**Next:** Phase 1 - Evaluate existing Python contracts and create current-violations baseline.
