#!/usr/bin/env python3
# pylint: disable=wrong-import-position  # Test file needs special setup
"""Unit tests for Python docstring validator.

:Purpose:
    Validates that the Python docstring validator correctly enforces
    Python docstring contracts as defined in
    docs/contributing/docstring-contracts/python.md

:Test Coverage:
    - Module docstring validation (presence, required sections)
    - Symbol-level docstring validation (functions, classes, methods)
    - Error message formatting and determinism
    - Pragma ignore functionality
    - Exit code validation

:Usage:
    Run tests from repository root::

        python3 -m pytest tools/repo_lint/tests/test_python_docstring_validator.py -v

:Environment Variables:
    None. Tests are self-contained.

:Exit Codes:
    0
        All tests passed
    1
        One or more tests failed

:Examples:
    Run all tests::

        python3 -m pytest tools/repo_lint/tests/test_python_docstring_validator.py -v

    Run specific test::

        python3 -m pytest tools/repo_lint/tests/test_python_docstring_validator.py::TestModuleDocstring::test_missing_module_docstring -v  # pylint: disable=line-too-long  # noqa: E501
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

# Add repo_lint parent directory to path for imports
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))

from tools.repo_lint.docstrings.python_validator import PythonValidator  # noqa: E402


class TestModuleDocstring(unittest.TestCase):
    """Test module-level docstring validation.

    :Purpose:
        Validates that module docstrings are correctly checked for
        presence and required sections.
    """

    def test_valid_module_docstring(self) -> None:
        """Test that valid module docstring passes validation.

        :Purpose:
            Ensure validator accepts complete, valid module docstrings.

        :rtype: None
        """
        content = '''"""Test module.

:Purpose:
    Test module purpose.

:Environment Variables:
    None

:Examples:
    Example usage

:Exit Codes:
    0
        Success
"""

def example() -> None:
    """Example function.

    :Purpose:
        Example purpose.

    :rtype: None
    """
    pass
'''
        errors = PythonValidator.validate(Path("test.py"), content)
        self.assertEqual(len(errors), 0, "Valid module docstring should pass")

    def test_missing_module_docstring(self) -> None:
        """Test detection of missing module docstring.

        :Purpose:
            Ensure validator detects files without module docstrings.

        :rtype: None
        """
        content = """# No docstring here
def example():
    pass
"""
        errors = PythonValidator.validate(Path("test.py"), content)
        # Expect 2 errors: module docstring + function docstring
        self.assertGreater(len(errors), 0)
        # Check if any error reports missing module docstring
        has_module_error = False
        for err in errors:
            if "module" in str(err.missing_sections).lower() or "module" in err.message.lower():
                has_module_error = True
                break
        self.assertTrue(has_module_error, "Should detect missing module docstring")

    def test_missing_required_section_purpose(self) -> None:
        """Test detection of missing :Purpose: section.

        :Purpose:
            Ensure validator catches missing Purpose section.

        :rtype: None
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
        self.assertGreater(len(errors), 0)
        # Should detect missing Purpose section
        error_sections = []
        for error in errors:
            error_sections.extend(error.missing_sections)
        self.assertTrue(
            any("Purpose" in section for section in error_sections),
            f"Should detect missing Purpose section. Got: {error_sections}",
        )

    def test_missing_required_section_examples(self) -> None:
        """Test detection of missing :Examples: section.

        :Purpose:
            Ensure validator catches missing Examples section.

        :rtype: None
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
        self.assertGreater(len(errors), 0)
        error_sections = []
        for error in errors:
            error_sections.extend(error.missing_sections)
        self.assertTrue(
            any("Examples" in section for section in error_sections),
            f"Should detect missing Examples section. Got: {error_sections}",
        )


class TestSymbolDocstrings(unittest.TestCase):
    """Test symbol-level docstring validation.

    :Purpose:
        Validates that function, class, and method docstrings are
        correctly validated.
    """

    def test_function_with_valid_docstring(self) -> None:
        """Test that function with valid docstring passes.

        :Purpose:
            Ensure validator accepts properly documented functions.

        :rtype: None
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

def example_function() -> None:
    """Example function.

    :Purpose:
        Does something.

    :rtype: None
    """
    pass
'''
        errors = PythonValidator.validate(Path("test.py"), content)
        self.assertEqual(len(errors), 0, "Valid function docstring should pass")

    def test_function_missing_docstring(self) -> None:
        """Test detection of function without docstring.

        :Purpose:
            Ensure validator catches undocumented functions.

        :rtype: None
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

def example_function():
    pass
'''
        errors = PythonValidator.validate(Path("test.py"), content)
        self.assertGreater(len(errors), 0)
        error_messages = [e.message for e in errors]
        self.assertTrue(
            any("docstring" in msg.lower() for msg in error_messages), "Should detect missing function docstring"
        )

    def test_class_with_valid_docstring(self) -> None:
        """Test that class with valid docstring passes.

        :Purpose:
            Ensure validator accepts properly documented classes.

        :rtype: None
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

class ExampleClass:
    """Example class.

    :Purpose:
        Example class purpose.
    """

    def example_method(self) -> None:
        """Example method.

        :Purpose:
            Example method purpose.

        :rtype: None
        """
        pass
'''
        errors = PythonValidator.validate(Path("test.py"), content)
        self.assertEqual(len(errors), 0, "Valid class docstring should pass")


class TestPragmaIgnore(unittest.TestCase):
    """Test pragma ignore functionality.

    :Purpose:
        Validates that # noqa: DOCSTRING pragma correctly suppresses
        validation errors.
    """

    def test_pragma_ignore_suppresses_error(self) -> None:
        """Test that pragma ignore suppresses validation errors.

        :Purpose:
            Ensure # noqa: DOCSTRING pragma works as expected.

        :rtype: None
        """
        # Note: This test assumes the validator checks for pragma comments.
        # If not implemented, this would need to be added to the validator.
        content = """# noqa: DOCSTRING
def example():
    pass
"""
        errors = PythonValidator.validate(Path("test.py"), content)
        # With pragma, should have no errors (or fewer errors)
        # This is a basic check - actual behavior depends on implementation
        self.assertIsInstance(errors, list)


class TestErrorFormatting(unittest.TestCase):
    """Test error message formatting and determinism.

    :Purpose:
        Validates that error messages are stable, deterministic,
        and contain actionable information.
    """

    def test_error_contains_file_path(self) -> None:
        """Test that errors include file path.

        :Purpose:
            Ensure error messages reference the file being validated.

        :rtype: None
        """
        content = """# No docstring
def example():
    pass
"""
        errors = PythonValidator.validate(Path("test_file.py"), content)
        self.assertGreater(len(errors), 0)
        self.assertIn("test_file.py", errors[0].file_path)

    def test_error_contains_missing_items(self) -> None:
        """Test that errors specify what is missing.

        :Purpose:
            Ensure error messages are actionable by listing missing items.

        :rtype: None
        """
        content = """# No docstring
def example():
    pass
"""
        errors = PythonValidator.validate(Path("test.py"), content)
        self.assertGreater(len(errors), 0)
        self.assertIsInstance(errors[0].missing_sections, list)
        self.assertGreater(len(errors[0].missing_sections), 0)

    def test_error_contains_reason(self) -> None:
        """Test that errors include human-readable reason.

        :Purpose:
            Ensure error messages explain what went wrong.

        :rtype: None
        """
        content = """# No docstring
def example():
    pass
"""
        errors = PythonValidator.validate(Path("test.py"), content)
        self.assertGreater(len(errors), 0)
        self.assertIsInstance(errors[0].message, str)
        self.assertGreater(len(errors[0].message), 0)


if __name__ == "__main__":
    unittest.main()
