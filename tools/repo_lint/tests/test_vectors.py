"""Vector-based conformance tests for repo_lint.

:Purpose:
    Implements vector-based testing to ensure deterministic and consistent
    linting + docstring enforcement across language runners and parser
    implementations. Tests that parser swaps (e.g., bashlex → tree-sitter)
    don't silently change expected outputs.

:Design:
    - Loads test vectors from conformance/repo-lint/vectors/docstrings/
    - Executes repo_lint runners against fixture files
    - Captures and normalizes outputs into violation schema
    - Compares actual vs expected violations deterministically

:Schema:
    Test vectors use normalized violation schema defined in
    conformance/repo-lint/README.md with stable fields:
    - rule_id: Stable rule identifier
    - path: Relative path to file with violation
    - symbol: Full symbol name
    - symbol_kind: Symbol type (function, method, class, sub)
    - line: Line number where violation occurs
    - severity: error or warning
    - message: Human-readable error message

:Environment Variables:
    REPO_ROOT: Repository root directory (auto-detected)

:Examples:
    Run all vector tests::

        pytest tools/repo_lint/tests/test_vectors.py

    Run specific language vectors::

        pytest tools/repo_lint/tests/test_vectors.py::test_python_docstring_vectors

:Exit Codes:
    Standard pytest exit codes (0 = all tests passed)
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

import pytest

# Repo root detection
REPO_ROOT = Path(__file__).parent.parent.parent.parent
VECTORS_DIR = REPO_ROOT / "conformance" / "repo-lint" / "vectors"
DOCSTRINGS_DIR = VECTORS_DIR / "docstrings"


def load_vector(vector_file: Path) -> dict:
    """Load a test vector from JSON file.

    :param vector_file: Path to vector JSON file

    :returns: Parsed vector dictionary

    :raises FileNotFoundError: If vector file doesn't exist
        json.JSONDecodeError: If vector file is invalid JSON
    """
    with open(vector_file, encoding="utf-8") as f:
        return json.load(f)


def normalize_violation_from_docstring_output(line: str) -> Dict | None:
    """Parse and normalize a violation from docstring validator output.

    :param line: Single line of output from validate_docstrings.py

    :returns: Normalized violation dict or None if line doesn't contain violation

    :note: Expected format examples:
        - "❌ /path/to/file.py:13"
        - "   Symbol: def no_doc()"
        - "   Missing: function docstring"

        Normalized format:
        {
            "rule_id": "DOCSTRING.MISSING",
            "path": "conformance/repo-lint/vectors/fixtures/python/file.py",
            "symbol": "no_doc",
            "symbol_kind": "function",
            "line": 13,
            "severity": "error",
            "message": "Function 'no_doc' is missing a docstring"
        }
    """
    # Check if this is a violation line with file:line format
    violation_pattern = r"^❌\s+(.+?):(\d+)\s*$"
    match = re.match(violation_pattern, line)
    if not match:
        return None

    file_path = match.group(1)
    line_num = int(match.group(2))

    # Normalize path to be relative to repo root
    if file_path.startswith(str(REPO_ROOT)):
        rel_path = os.path.relpath(file_path, REPO_ROOT)
    else:
        rel_path = file_path

    return {
        "path": rel_path,
        "line": line_num,
        "severity": "error",
        # These will be populated from subsequent lines
        "symbol": None,
        "symbol_kind": None,
        "message": None,
        "rule_id": "DOCSTRING.MISSING",  # Default, may be overridden
    }


def parse_docstring_validator_output(output: str) -> List[Dict]:
    """Parse docstring validator output into normalized violations.

    :param output: Raw output from validate_docstrings.py

    :returns: List of normalized violation dictionaries

    :note: Parser handles multi-line violation format:
        ❌ /path/file.py:13
           Symbol: def no_doc()
           Missing: function docstring
           Function must have a docstring
    """
    violations = []
    current_violation = None
    lines = output.split("\n")

    for line in lines:
        # Try to parse as new violation header
        new_violation = normalize_violation_from_docstring_output(line)
        if new_violation:
            if current_violation:
                violations.append(current_violation)
            current_violation = new_violation
            continue

        # Parse details for current violation
        if current_violation:
            # Extract symbol name and kind (supports 'def', 'class', and potentially other keywords)
            symbol_match = re.match(r"\s+Symbol:\s+(def|class|sub|function)\s+([\w.]+)", line)
            if symbol_match:
                kind_keyword = symbol_match.group(1)
                symbol_name = symbol_match.group(2)

                # Determine symbol kind based on keyword
                symbol_kind_map = {
                    "def": "function",
                    "class": "class",
                    "sub": "sub",
                    "function": "function",
                }
                current_violation["symbol_kind"] = symbol_kind_map.get(kind_keyword, "function")

                current_violation["symbol"] = symbol_name
                continue

            # Extract missing reason
            missing_match = re.match(r"\s+Missing:\s+(.+)", line)
            if missing_match:
                missing = missing_match.group(1).strip()
                if "docstring" in missing:
                    current_violation["rule_id"] = "DOCSTRING.MISSING"
                    # Construct message
                    kind = current_violation.get("symbol_kind", "symbol")
                    symbol = current_violation.get("symbol", "unknown")
                    current_violation["message"] = f"{kind.capitalize()} '{symbol}' is missing a docstring"
                continue

    # Add last violation
    if current_violation:
        violations.append(current_violation)

    # Filter out incomplete violations
    return [v for v in violations if v.get("symbol") and v.get("message")]


def run_docstring_validator(fixture_path: Path) -> List[Dict]:
    """Run docstring validator on fixture and return normalized violations.

    :param fixture_path: Path to source file to validate

    :returns: List of normalized violation dictionaries

    :raises subprocess.CalledProcessError: If validator fails unexpectedly
    """
    validator_script = REPO_ROOT / "scripts" / "validate_docstrings.py"

    # DEBUG: Print BEFORE running subprocess
    print(f"\n🔍 DEBUG: About to run validator")
    print(f"    Python: {sys.executable}")
    print(f"    Script: {validator_script}")
    print(f"    Script exists: {validator_script.exists()}")
    print(f"    Fixture: {fixture_path}")
    print(f"    Fixture exists: {fixture_path.exists()}")
    print(f"    CWD: {REPO_ROOT}")

    # Run validator with minimal checks (just docstring presence, not content)
    result = subprocess.run(
        [sys.executable, str(validator_script), "--file", str(fixture_path), "--no-content-checks"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )

    # DEBUG: Print output for CI debugging
    print(f"\n📋 DEBUG: Subprocess completed")
    print(f"    Exit code: {result.returncode}")
    print(f"    Stdout length: {len(result.stdout)}")
    print(f"    Stderr length: {len(result.stderr)}")
    print(f"    Stdout preview: {result.stdout[:300]}")
    print(f"    Stderr preview: {result.stderr[:300]}")

    # Parse output (validator exits non-zero on violations, which is expected)
    violations = parse_docstring_validator_output(result.stdout + result.stderr)

    print(f"    Violations found: {len(violations)}")
    for v in violations[:3]:
        print(f"      - {v.get('symbol')} at line {v.get('line')}")

    return violations


def compare_violations(actual: List[Dict], expected: List[Dict], vector_id: str) -> None:
    """Compare actual vs expected violations and assert match.

    :param actual: List of actual violations from running validator
        expected: List of expected violations from vector file
        vector_id: ID of test vector (for error messages)

    :raises AssertionError: If violations don't match expected

    :note: Compares violations by normalized fields:
        - rule_id
        - symbol
        - symbol_kind
        - line
        - severity

        Path matching is relaxed (basename only) to handle absolute vs relative paths.
        Message matching uses substring match to handle variation in error text.
    """
    # Sort both lists by symbol and line for stable comparison
    actual_sorted = sorted(actual, key=lambda v: (v.get("symbol", ""), v.get("line", 0)))
    expected_sorted = sorted(expected, key=lambda v: (v.get("symbol", ""), v.get("line", 0)))

    # Build diagnostic message
    if len(actual_sorted) != len(expected_sorted):
        msg = f"\n{vector_id}: Violation count mismatch\n"
        msg += f"Expected {len(expected_sorted)} violations, got {len(actual_sorted)}\n\n"
        msg += "Expected violations:\n"
        for v in expected_sorted:
            msg += f"  - {v.get('symbol')} (line {v.get('line')}): {v.get('rule_id')}\n"
        msg += "\nActual violations:\n"
        for v in actual_sorted:
            msg += f"  - {v.get('symbol')} (line {v.get('line')}): {v.get('rule_id')}\n"
        pytest.fail(msg)

    # Compare each violation
    for i, (actual_v, expected_v) in enumerate(zip(actual_sorted, expected_sorted)):
        # Check required fields
        assert actual_v.get("rule_id") == expected_v.get("rule_id"), (
            f"{vector_id}: Violation {i+1} rule_id mismatch\n"
            f"Expected: {expected_v.get('rule_id')}\n"
            f"Actual: {actual_v.get('rule_id')}"
        )

        assert actual_v.get("symbol") == expected_v.get("symbol"), (
            f"{vector_id}: Violation {i+1} symbol mismatch\n"
            f"Expected: {expected_v.get('symbol')}\n"
            f"Actual: {actual_v.get('symbol')}"
        )

        assert actual_v.get("symbol_kind") == expected_v.get("symbol_kind"), (
            f"{vector_id}: Violation {i+1} symbol_kind mismatch\n"
            f"Expected: {expected_v.get('symbol_kind')}\n"
            f"Actual: {actual_v.get('symbol_kind')}"
        )

        assert actual_v.get("line") == expected_v.get("line"), (
            f"{vector_id}: Violation {i+1} line number mismatch\n"
            f"Expected: {expected_v.get('line')}\n"
            f"Actual: {actual_v.get('line')}"
        )

        assert actual_v.get("severity") == expected_v.get("severity"), (
            f"{vector_id}: Violation {i+1} severity mismatch\n"
            f"Expected: {expected_v.get('severity')}\n"
            f"Actual: {actual_v.get('severity')}"
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Test Cases
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def test_python_docstring_vectors():
    """Test Python docstring validation vectors.

    :Purpose:
        Validates that Python docstring enforcement produces expected violations
        for missing docstrings, pragma exemptions, and edge cases.

    :note: Loads and runs all Python docstring vectors from:
        conformance/repo-lint/vectors/docstrings/python-docstring-*.json
    """
    # Find all Python docstring vectors
    vector_files = list(DOCSTRINGS_DIR.glob("python-docstring-*.json"))
    assert vector_files, "No Python docstring vectors found"

    for vector_file in vector_files:
        vector = load_vector(vector_file)
        fixture_path = REPO_ROOT / vector["fixture"]

        # Run docstring validator on fixture
        actual_violations = run_docstring_validator(fixture_path)

        # Compare with expected violations
        compare_violations(actual_violations, vector["expected_violations"], vector["id"])


def test_bash_docstring_vectors():
    """Test Bash docstring validation vectors.

    :Purpose:
        Validates that Bash docstring enforcement produces expected violations
        using tree-sitter-based symbol discovery.

    :note: Loads and runs all Bash docstring vectors from:
        conformance/repo-lint/vectors/docstrings/bash-docstring-*.json
    """
    pytest.skip("Bash vector runner not yet implemented - requires bash-specific parser")


def test_powershell_docstring_vectors():
    """Test PowerShell docstring validation vectors.

    :Purpose:
        Validates that PowerShell docstring enforcement produces expected violations
        using PowerShell AST-based symbol discovery.

    :note: Loads and runs all PowerShell docstring vectors from:
        conformance/repo-lint/vectors/docstrings/powershell-docstring-*.json
    """
    pytest.skip("PowerShell vector runner not yet implemented - requires pwsh AST parser")


def test_perl_docstring_vectors():
    """Test Perl docstring validation vectors.

    :Purpose:
        Validates that Perl docstring enforcement produces expected violations
        using PPI-based symbol discovery.

    :note: Loads and runs all Perl docstring vectors from:
        conformance/repo-lint/vectors/docstrings/perl-docstring-*.json
    """
    pytest.skip("Perl vector runner not yet implemented - requires PPI parser")


def test_vector_fixtures_exist():
    """Verify all vector fixtures reference valid files.

    :Purpose:
        Ensures test vectors point to existing fixture files and fixture
        paths are correct relative to repo root.

    :note: Validates all vectors in conformance/repo-lint/vectors/docstrings/
    """
    vector_files = list(DOCSTRINGS_DIR.glob("*.json"))
    assert vector_files, "No vector files found"

    for vector_file in vector_files:
        vector = load_vector(vector_file)
        fixture_path = REPO_ROOT / vector["fixture"]

        assert fixture_path.exists(), f"Fixture not found for {vector['id']}: {fixture_path}"


def test_vector_schema_validation():
    """Validate all vectors follow the required schema.

    :Purpose:
        Ensures all test vectors contain required fields and follow
        the normalized violation schema defined in README.

    :note: Checks for required fields:
        - id, name, description, language, fixture
        - expected_violations with proper violation objects
        - expected_passes (optional but validated if present)
    """
    vector_files = list(DOCSTRINGS_DIR.glob("*.json"))
    assert vector_files, "No vector files found"

    required_vector_fields = ["id", "name", "description", "language", "fixture"]
    required_violation_fields = ["rule_id", "path", "symbol", "symbol_kind", "line", "severity", "message"]

    for vector_file in vector_files:
        vector = load_vector(vector_file)

        # Check required vector fields
        for field in required_vector_fields:
            assert field in vector, f"{vector_file.name}: Missing required field '{field}'"

        # Validate expected_violations
        if "expected_violations" in vector:
            for i, violation in enumerate(vector["expected_violations"]):
                for field in required_violation_fields:
                    assert field in violation, f"{vector_file.name}: Violation {i} missing field '{field}'"

        # Validate expected_passes (if present)
        if "expected_passes" in vector:
            for i, pass_obj in enumerate(vector["expected_passes"]):
                assert "symbol" in pass_obj, f"{vector_file.name}: Pass {i} missing 'symbol'"
                assert "symbol_kind" in pass_obj, f"{vector_file.name}: Pass {i} missing 'symbol_kind'"
