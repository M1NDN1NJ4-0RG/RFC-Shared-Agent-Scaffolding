# Repo Lint Conformance Vectors

**Purpose:** Ensure deterministic and consistent linting + docstring enforcement across language runners and parser implementations.

**Status:** Phase 6 Item 6.5 (In Progress)

---

## Overview

This directory contains conformance test vectors for `repo_lint` linting and docstring validation. These vectors ensure:

1. **Parser swaps** (e.g., bashlex → tree-sitter, PPI fallback tweaks) don't silently change outputs
2. **Auto-fix behavior** is governed by explicit policy and is auditable
3. **Docstring enforcement** remains consistent across all language validators

---

## Directory Structure

```
conformance/repo-lint/
├── autofix-policy.json           # Deny-by-default auto-fix allow/deny policy
├── vectors/
│   ├── docstrings/                # Docstring validation test vectors (JSON)
│   │   ├── python-docstring-001.json
│   │   ├── bash-docstring-001.json
│   │   ├── powershell-docstring-001.json
│   │   ├── perl-docstring-001.json
│   │   └── ...
│   └── fixtures/                  # Source code fixtures for testing
│       ├── python/
│       │   └── docstring_test.py
│       ├── bash/
│       │   └── docstring-test.sh
│       ├── powershell/
│       │   └── DocstringTest.ps1
│       ├── perl/
│       │   └── docstring_test.pl
│       └── yaml/
└── README.md                      # This file
```

---

## Normalized Violation Schema

All test vectors use a **normalized violation schema** to ensure stable, comparable outputs across different parser implementations.

### Vector File Structure

Each vector file (e.g., `python-docstring-001.json`) contains:

```json
{
  "id": "python-docstring-001",
  "name": "Human-readable test name",
  "description": "What this vector tests",
 "language": "python | bash | powershell | perl | yaml | rust",
  "fixture": "path/to/fixture/file",
  "expected_violations": [
    {
      "rule_id": "DOCSTRING.MISSING",
      "path": "conformance/repo-lint/vectors/fixtures/python/docstring_test.py",
      "symbol": "function_name",
 "symbol_kind": "function | method | class | sub",
      "line": 12,
 "severity": "error | warning",
      "message": "Descriptive error message"
    }
  ],
  "expected_passes": [
    {
      "symbol": "properly_documented_function",
      "symbol_kind": "function",
      "reason": "Has proper docstring"
    }
  ],
  "notes": [
    "Additional context about this test vector"
  ]
}
```

### Violation Object Fields

| Field | Type | Required | Description |
| ------- | ------ | ---------- | ------------- |
| `rule_id` | string | Yes | Stable rule identifier (e.g., `DOCSTRING.MISSING`, `LINT.RUFF.E501`) |
| `path` | string | Yes | Relative path to the file with the violation |
| `symbol` | string | Yes | Full symbol name (e.g., `ClassName.method_name`) |
| `symbol_kind` | string | Yes | Symbol type: `function`, `method`, `class`, `sub`, etc. |
| `line` | number | Yes | Line number where the violation occurs |
| `severity` | string | Yes | `error` or `warning` |
| `message` | string | Yes | Human-readable error message |

### Pass Object Fields

| Field | Type | Required | Description |
| ------- | ------ | ---------- | ------------- |
| `symbol` | string | Yes | Symbol name that should not produce a violation |
| `symbol_kind` | string | Yes | Symbol type |
| `reason` | string | Yes | Why this symbol should pass |

---

## Auto-Fix Policy

The auto-fix policy (`autofix-policy.json`) defines which fix categories are allowed to run under `repo-lint fix`.

**Policy:** Deny-by-default. Only explicitly allowed categories may execute auto-fixes.

### Allowed Categories

- **`FORMAT.BLACK`**: Black Python formatter (safe, mutating)
- **`FORMAT.SHFMT`**: shfmt shell formatter (safe, mutating)
- **`LINT.RUFF.SAFE`**: Ruff safe auto-fixes only (no unsafe fixes)

### Denied Categories

- **`LINT.RUFF.UNSAFE`**: Unsafe Ruff fixes that may change semantics
- **`REWRITE.DOCSTRING_CONTENT`**: Automatic docstring generation
- **`MODIFY_LOGIC`**: Logic-changing fixes
- **`REORDER_IMPORTS`**: Import sorting (not currently enabled)

**Enforcement:** The `repo_lint` CLI consults this policy file and:

1. Only runs fixes in the `allowed_categories` list
2. Skips denied categories with a clear message
3. Provides a deterministic summary of which categories ran

---

## Usage

### For Test Implementers

1. Load vector files from `conformance/repo-lint/vectors/docstrings/` (kebab-case JSON files)
2. For each vector:
   - Run the relevant `repo_lint` runner against the fixture file
   - Capture violations in the normalized schema format
   - Compare actual violations against `expected_violations`
   - Verify that `expected_passes` symbols do not produce violations
3. Report pass/fail per vector ID

### Example Test Pseudocode

```python
import json
from pathlib import Path
from tools.repo_lint.runners.python_runner import PythonRunner

def test_python_docstring_001():
    # Load vector
    vector_path = Path("conformance/repo-lint/vectors/docstrings/python-docstring-001.json")
    vector = json.loads(vector_path.read_text())

    # Run linter
    runner = PythonRunner(repo_root=Path.cwd())
    result = runner.check(only_docstrings=True, files=[vector["fixture"]])

    # Normalize violations to schema
    actual_violations = normalize_violations(result.violations)

    # Compare
    assert actual_violations == vector["expected_violations"]

    # Verify passes
    for expected_pass in vector["expected_passes"]:
        assert not any(v["symbol"] == expected_pass["symbol"] for v in actual_violations)
```

### For CI/CD

Vectors should be tested whenever:

- Linting or docstring validation code changes
- Parser implementations are swapped (e.g., tree-sitter upgrade)
- `autofix-policy.json` is updated

A failing vector test indicates **behavioral drift** and blocks merge.

---

## Adding New Vectors

When adding a new conformance vector:

1. **Choose a stable ID**: Use format `{language}-{category}-{number}` (e.g., `python-docstring-002`)
2. **Create fixture**: Add minimal source file to `vectors/fixtures/{language}/`
3. **Define vector**: Create JSON file in `vectors/docstrings/` with:
   - Expected violations in normalized schema
   - Expected passes with reasons
   - Clear description and notes
4. **Test locally**: Run the vector against the relevant runner to verify correctness
5. **Update this README**: Document any new rule IDs or edge cases

### Fixture File Naming Conventions

Follow language-specific naming conventions per `docs/contributing/naming-and-style.md`:

- Python: `snake_case.py` (e.g., `docstring_test.py`)
- Bash: `kebab-case.sh` (e.g., `docstring-test.sh`)
- PowerShell: `PascalCase.ps1` (e.g., `DocstringTest.ps1`)
- Perl: `snake_case.pl` (e.g., `docstring_test.pl`)
- YAML: `kebab-case.yml` (e.g., `docstring-test.yml`)

---

## Expected Output Regeneration

**CRITICAL:** Expected outputs in vector files MUST NOT be hand-edited.

To update expected outputs after intentional behavioral changes:

1. Run: `python -m tools.repo_lint vectors update --case <case_id>`
   - Example: `python -m tools.repo_lint vectors update --case python-docstring-001`
2. Review the diff carefully to ensure changes are intentional
3. Commit the updated vector file with a clear explanation

This ensures reproducibility and auditability. No casual baseline rewrites.

---

## Version History

- **v1.0** (2025-12-29): Initial repo_lint conformance vectors (Phase 6 Item 6.5)
  - Docstring validation vectors: Python, Bash, PowerShell, Perl
  - Auto-fix policy: Deny-by-default with 3 allowed categories
  - Normalized violation schema established

---

**Refs:** Phase 6 Item 6.5, Epic repo_lint
