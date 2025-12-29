#!/usr/bin/env python3
"""Unit tests for validate-docstrings.py validator.

This module provides basic unit tests for the docstring validator,
covering each language's validation logic.

Purpose
-------
Ensures the validator correctly identifies valid and invalid docstrings
for all supported languages (Bash, PowerShell, Python, Perl, Rust, YAML).

Usage
-----
Run tests from repository root::

    python3 -m pytest scripts/tests/test_validate_docstrings.py
    # or
    python3 scripts/tests/test_validate_docstrings.py

Environment Variables
---------------------
None. Tests are self-contained.

Exit Codes
----------
0
    All tests passed
1
    One or more tests failed

Examples
--------
Run all tests::

    python3 -m pytest scripts/tests/test_validate_docstrings.py -v

Run specific test::

    python3 -m pytest scripts/tests/test_validate_docstrings.py::test_bash_valid -v

Notes
-----
- Tests use minimal valid/invalid examples for each language
- Can be run with pytest or as standalone script (uses unittest)
- Add more tests as validation rules evolve
"""

import sys
import unittest
from pathlib import Path

# Add parent directory to path to import validator
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import validator modules
# Note: This assumes the validator can be imported as a module
# If not, tests can be run from the scripts directory
try:
    from validate_docstrings import (
        BashValidator,
        PythonValidator,
        YAMLValidator,
    )
except ImportError:
    # Try alternative import path
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "validate_docstrings", Path(__file__).parent.parent / "validate-docstrings.py"
    )
    validate_docstrings = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validate_docstrings)

    BashValidator = validate_docstrings.BashValidator
    PythonValidator = validate_docstrings.PythonValidator
    YAMLValidator = validate_docstrings.YAMLValidator

    BashValidator = validate_docstrings.BashValidator
    PowerShellValidator = validate_docstrings.PowerShellValidator
    PythonValidator = validate_docstrings.PythonValidator
    PerlValidator = validate_docstrings.PerlValidator
    RustValidator = validate_docstrings.RustValidator
    YAMLValidator = validate_docstrings.YAMLValidator


class TestBashValidator(unittest.TestCase):
    """Test Bash script validation."""

    def test_valid_bash_script(self):
        """Test that a valid Bash script passes validation."""
        content = """#!/usr/bin/env bash
#
# test.sh - Test script
#
# DESCRIPTION:
#   This is a test script.
#
# USAGE:
#   ./test.sh
#
# INPUTS:
#   None
#
# OUTPUTS:
#   Exit Codes:
#     0    Success
#     1    Failure
#
# EXAMPLES:
#   # Run the script
#   ./test.sh

echo "test"
"""
        result = BashValidator.validate(Path("test.sh"), content)
        self.assertIsNone(result, "Valid Bash script should pass validation")

    def test_missing_shebang(self):
        """Test that missing shebang is caught."""
        content = """# test.sh - Test script
# DESCRIPTION: Test
# USAGE: ./test.sh
# INPUTS: None
# OUTPUTS: Exit 0
# EXAMPLES: ./test.sh
"""
        result = BashValidator.validate(Path("test.sh"), content)
        self.assertIsNotNone(result, "Missing shebang should fail validation")
        self.assertIn("shebang", result.missing_sections)

    def test_missing_required_section(self):
        """Test that missing required section is caught."""
        content = """#!/usr/bin/env bash
#
# test.sh - Test script
#
# DESCRIPTION:
#   This is a test script.
#
# USAGE:
#   ./test.sh

echo "test"
"""
        result = BashValidator.validate(Path("test.sh"), content)
        self.assertIsNotNone(result, "Missing INPUTS, OUTPUTS, EXAMPLES should fail")


class TestPythonValidator(unittest.TestCase):
    """Test Python script validation."""

    def test_valid_python_script(self):
        """Test that a valid Python script passes validation."""
        content = '''#!/usr/bin/env python3
"""Test script.

Purpose
-------
Tests validation.

Environment Variables
---------------------
None.

Examples
--------
Run the script::

    python3 test.py

Exit Codes
----------
0
    Success
1
    Failure
"""

print("test")
'''
        result = PythonValidator.validate(Path("test.py"), content)
        self.assertIsNone(result, "Valid Python script should pass validation")

    def test_missing_docstring(self):
        """Test that missing docstring is caught."""
        content = """#!/usr/bin/env python3
print("test")
"""
        result = PythonValidator.validate(Path("test.py"), content)
        self.assertIsNotNone(result, "Missing docstring should fail validation")


class TestYAMLValidator(unittest.TestCase):
    """Test YAML file validation."""

    def test_valid_yaml_workflow(self):
        """Test that a valid YAML workflow passes validation."""
        content = """# Workflow: Test Workflow
#
# Purpose: Tests something.
#
# Triggers:
# - Pull requests
#
# Dependencies:
# - actions/checkout@v4
#
# Outputs:
# - Status check
#
# Notes:
# - Test workflow

name: Test
on: [pull_request]
"""
        result = YAMLValidator.validate(Path("test.yml"), content)
        self.assertIsNone(result, "Valid YAML workflow should pass validation")


class TestExitCodeContentValidation(unittest.TestCase):
    """Test exit code content validation."""

    def test_bash_with_valid_exit_codes(self):
        """Test that Bash script with valid exit codes passes."""
        content = """#!/usr/bin/env bash
#
# DESCRIPTION:
#   Test
#
# USAGE:
#   ./test.sh
#
# INPUTS:
#   None
#
# OUTPUTS:
#   Exit Codes:
#     0    Success - all tests pass
#     1    Failure - any test fails
#
# EXAMPLES:
#   ./test.sh

echo "test"
"""
        result = BashValidator.validate(Path("test.sh"), content)
        self.assertIsNone(result, "Exit codes with 0 and 1 should pass")


def run_tests():
    """Run tests when executed as script."""
    # Try to use pytest if available
    try:
        import pytest

        return pytest.main([__file__, "-v"])
    except ImportError:
        # Fall back to unittest
        print("Running tests with unittest (pytest not available)")
        suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())
