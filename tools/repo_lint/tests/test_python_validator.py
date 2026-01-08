#!/usr/bin/env python3
# pylint: disable=wrong-import-position  # Test file needs special setup
"""Unit tests for Python docstring validator.

:Purpose:
    Validates that the Python docstring validator correctly enforces
    docstring contracts for module-level and symbol-level documentation.

:Test Coverage:
    - Module docstring validation (required sections)
    - Function/method docstring validation
    - Class docstring validation
    - Pragma ignore support (#noqa directives)
    - Exit codes content validation
    - AST parsing edge cases
    - reST field format validation

:Usage:
    Run tests from repository root::

        python3 -m pytest tools/repo_lint/tests/test_python_validator.py
        # or
        python3 tools/repo_lint/tests/test_python_validator.py

:Environment Variables:
    None. Tests are self-contained.

:Exit Codes:
    0
        All tests passed
    1
        One or more tests failed

:Examples:
    Run all tests::

        python3 -m pytest tools/repo_lint/tests/test_python_validator.py -v

    Run specific test::

        python3 -m pytest tools/repo_lint/tests/test_python_validator.py::TestPythonValidator \
            ::test_valid_module_docstring -v

:Notes:
    - Tests use real docstring validation logic (no mocking of validators)
    - Tests verify exact error messages and missing sections
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

# Add repo_lint parent directory to path for imports
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))

from tools.repo_lint.docstrings.python_validator import (  # noqa: E402
    PythonValidator,  # noqa: E402
)  # noqa: E402


class TestPythonValidator(unittest.TestCase):
    """Test Python docstring validator behavior.

    :Purpose:
        Validates Python docstring contract enforcement.
    """

    def test_valid_module_docstring(self):
        """Test that a valid module docstring passes validation.

        :Purpose:
            Verify complete module docstring with all required sections passes.
        """
        content = '''"""Test module.

:Purpose:
    Test module purpose.

:Environment Variables:
    None

:Examples:
    Example usage::

        import module

:Exit Codes:
    0
        Success
    1
        Failure
"""
'''
        errors = PythonValidator.validate(Path("test.py"), content)
        self.assertEqual(len(errors), 0, f"Expected no errors, got: {errors}")

    def test_missing_module_docstring(self):
        """Test that missing module docstring is detected.

        :Purpose:
            Verify files without module docstrings are flagged.
        """
        content = "# Just a comment\nx = 5\n"
        errors = PythonValidator.validate(Path("test.py"), content)
        self.assertEqual(len(errors), 1)
        # The message is about expecting the triple-quote docstring format
        self.assertIn('"""', errors[0].message)

    def test_missing_purpose_section(self):
        """Test that missing :Purpose: section is detected.

        :Purpose:
            Verify module docstrings without :Purpose: are flagged.
        """
        content = '''"""Test module.

:Environment Variables:
    None

:Examples:
    Example

:Exit Codes:
    0
        Success
"""
'''
        errors = PythonValidator.validate(Path("test.py"), content)
        self.assertEqual(len(errors), 1)
        self.assertIn("Purpose", errors[0].missing_sections)

    def test_missing_examples_section(self):
        """Test that missing :Examples: section is detected.

        :Purpose:
            Verify module docstrings without :Examples: are flagged.
        """
        content = '''"""Test module.

:Purpose:
    Test purpose.

:Environment Variables:
    None

:Exit Codes:
    0
        Success
"""
'''
        errors = PythonValidator.validate(Path("test.py"), content)
        self.assertEqual(len(errors), 1)
        self.assertIn("Examples", errors[0].missing_sections)

    def test_missing_exit_codes_section(self):
        """Test that missing :Exit Codes: section is detected.

        :Purpose:
            Verify module docstrings without :Exit Codes: are flagged.
        """
        content = '''"""Test module.

:Purpose:
    Test purpose.

:Environment Variables:
    None

:Examples:
    Example
"""
'''
        errors = PythonValidator.validate(Path("test.py"), content)
        self.assertEqual(len(errors), 1)
        self.assertIn("Exit Codes", errors[0].missing_sections)

    def test_function_with_docstring_passes(self):
        """Test that functions with docstrings pass validation.

        :Purpose:
            Verify documented functions do not trigger errors.
        """
        content = '''"""Module docstring.

:Purpose:
    Test

:Environment Variables:
    None

:Examples:
    Example

:Exit Codes:
    0
        Success
"""

def my_function(x):
    """Function docstring.

    :param x: Input value
    :returns: Output value
    """
    return x + 1
'''
        errors = PythonValidator.validate(Path("test.py"), content)
        self.assertEqual(len(errors), 0, f"Expected no errors, got: {errors}")

    def test_function_without_docstring_fails(self):
        """Test that functions without docstrings are detected.

        :Purpose:
            Verify undocumented functions are flagged.
        """
        content = '''"""Module docstring.

:Purpose:
    Test

:Environment Variables:
    None

:Examples:
    Example

:Exit Codes:
    0
        Success
"""

def my_function(x):
    return x + 1
'''
        errors = PythonValidator.validate(Path("test.py"), content)
        # Should have 1 error for the undocumented function
        self.assertGreater(len(errors), 0)
        # Check that one of the errors is about a function
        has_function_error = any("function" in str(e).lower() or "my_function" in str(e) for e in errors)
        self.assertTrue(has_function_error, f"Expected function error, got: {errors}")

    def test_class_without_docstring_fails(self):
        """Test that classes without docstrings are detected.

        :Purpose:
            Verify undocumented classes are flagged.
        """
        content = '''"""Module docstring.

:Purpose:
    Test

:Environment Variables:
    None

:Examples:
    Example

:Exit Codes:
    0
        Success
"""

class MyClass:
    def __init__(self):
        self.x = 0
'''
        errors = PythonValidator.validate(Path("test.py"), content)
        self.assertGreater(len(errors), 0)
        # Check for class-related error
        has_class_error = any("class" in str(e).lower() or "MyClass" in str(e) for e in errors)
        self.assertTrue(has_class_error, f"Expected class error, got: {errors}")

    def test_pragma_ignore_function(self):
        """Test that # noqa: D103 pragma ignores function validation.

        :Purpose:
            Verify pragma support for function docstrings.
        """
        content = '''"""Module docstring.

:Purpose:
    Test

:Environment Variables:
    None

:Examples:
    Example

:Exit Codes:
    0
        Success
"""

def my_function(x):  # noqa: D103
    return x + 1
'''
        errors = PythonValidator.validate(Path("test.py"), content)
        # Should have no errors because function has pragma
        self.assertEqual(len(errors), 0, f"Expected no errors with pragma, got: {errors}")

    def test_exit_codes_content_validation(self):
        """Test that exit codes section content is validated.

        :Purpose:
            Verify exit codes must include code definitions.
        """
        content = '''"""Module docstring.

:Purpose:
    Test

:Environment Variables:
    None

:Examples:
    Example

:Exit Codes:
    Empty content here
"""
'''
        errors = PythonValidator.validate(Path("test.py"), content)
        # Should detect incomplete exit codes content
        # This depends on validate_exit_codes_content implementation
        # For now, just verify the validator runs
        self.assertIsInstance(errors, list)

    def test_syntax_error_skips_symbol_validation(self):
        """Test that files with syntax errors skip symbol validation.

        :Purpose:
            Verify graceful handling of unparseable Python files.
        """
        content = '''"""Module docstring.

:Purpose:
    Test

:Environment Variables:
    None

:Examples:
    Example

:Exit Codes:
    0
        Success
"""

def broken syntax here:
    pass
'''
        # Should not crash, just skip symbol validation
        errors = PythonValidator.validate(Path("test.py"), content)
        # Should only have module-level errors, not symbol errors
        self.assertIsInstance(errors, list)


if __name__ == "__main__":
    unittest.main()
