Run python3 -m pytest tools/repo_lint/tests/test_vectors.py -v
============================= test session starts ==============================
platform linux -- Python 3.11.14, pytest-9.0.2, pluggy-1.6.0 -- /opt/hostedtoolcache/Python/3.11.14/x64/bin/python3
cachedir: .pytest_cache
rootdir: /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding
configfile: pyproject.toml
collecting ... collected 6 items

tools/repo_lint/tests/test_vectors.py::test_python_docstring_vectors FAILED [ 16%]
tools/repo_lint/tests/test_vectors.py::test_bash_docstring_vectors SKIPPED [ 33%]
tools/repo_lint/tests/test_vectors.py::test_powershell_docstring_vectors SKIPPED [ 50%]
tools/repo_lint/tests/test_vectors.py::test_perl_docstring_vectors SKIPPED [ 66%]
tools/repo_lint/tests/test_vectors.py::test_vector_fixtures_exist PASSED [ 83%]
tools/repo_lint/tests/test_vectors.py::test_vector_schema_validation PASSED [100%]

=================================== FAILURES ===================================
________________________ test_python_docstring_vectors _________________________

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
>           compare_violations(actual_violations, vector["expected_violations"], vector["id"])

tools/repo_lint/tests/test_vectors.py:311:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

actual = []
expected = [{'line': 27, 'message': "Function 'no_doc' is missing a docstring", 'path': 'conformance/repo-lint/vectors/fixtures/p...ring", 'path': 'conformance/repo-lint/vectors/fixtures/python/docstring_test.py', 'rule_id': 'DOCSTRING.MISSING', ...}]
vector_id = 'python-docstring-001'

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
>           pytest.fail(msg)
E           Failed:
E           python-docstring-001: Violation count mismatch
E           Expected 3 violations, got 0
E
E           Expected violations:
E             - MissingClassDoc (line 31): DOCSTRING.MISSING
E             - method_without_doc (line 36): DOCSTRING.MISSING
E             - no_doc (line 27): DOCSTRING.MISSING
E
E           Actual violations:

tools/repo_lint/tests/test_vectors.py:248: Failed
=========================== short test summary info ============================
FAILED tools/repo_lint/tests/test_vectors.py::test_python_docstring_vectors - Failed:
python-docstring-001: Violation count mismatch
Expected 3 violations, got 0

Expected violations:
  - MissingClassDoc (line 31): DOCSTRING.MISSING
  - method_without_doc (line 36): DOCSTRING.MISSING
  - no_doc (line 27): DOCSTRING.MISSING

Actual violations:
==================== 1 failed, 2 passed, 3 skipped in 0.10s ====================
Error: Process completed with exit code 1.
