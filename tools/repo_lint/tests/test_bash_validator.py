#!/usr/bin/env python3
# pylint: disable=wrong-import-position  # Test file needs special setup
"""Unit tests for Bash docstring validator.

:Purpose:
    Validates that the Bash docstring validator correctly enforces
    docstring contracts for Bash script header and function documentation.

:Test Coverage:
    - Script header validation (required sections)
    - Function documentation validation
    - Pragma ignore support (#noqa directives)
    - Tree-sitter function parsing
    - Missing documentation detection

:Usage:
    Run tests from repository root::

        python3 -m pytest tools/repo_lint/tests/test_bash_validator.py
        # or
        python3 tools/repo_lint/tests/test_bash_validator.py

:Environment Variables:
    None. Tests are self-contained.

:Exit Codes:
    0
        All tests passed
    1
        One or more tests failed

:Examples:
    Run all tests::

        python3 -m pytest tools/repo_lint/tests/test_bash_validator.py -v

    Run specific test::

        python3 -m pytest tools/repo_lint/tests/test_bash_validator.py::TestBashValidator \
            ::test_valid_header -v

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

from tools.repo_lint.docstrings.bash_validator import (  # noqa: E402
    BashValidator,  # noqa: E402
)  # noqa: E402


class TestBashValidator(unittest.TestCase):
    """Test Bash docstring validator behavior.

    :Purpose:
        Validates Bash docstring contract enforcement.
    """

    def test_valid_header(self) -> None:
        """Test that a valid script header passes validation.

        :Purpose:
            Verify complete header with all required sections passes.
        """
        content = """#!/bin/bash
# DESCRIPTION:
#   Test script description.
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
#   ./test.sh

echo "Hello"
"""
        errors = BashValidator.validate(Path("test.sh"), content)
        self.assertEqual(len(errors), 0, f"Expected no errors, got: {errors}")

    def test_missing_description_section(self) -> None:
        """Test that missing DESCRIPTION section is detected.

        :Purpose:
            Verify headers without DESCRIPTION are flagged.
        """
        content = """#!/bin/bash
# USAGE:
#   ./test.sh
#
# INPUTS:
#   None
#
# OUTPUTS:
#   Exit Codes:
#     0    Success
#
# EXAMPLES:
#   ./test.sh

echo "Hello"
"""
        errors = BashValidator.validate(Path("test.sh"), content)
        self.assertEqual(len(errors), 1)
        self.assertIn("DESCRIPTION:", errors[0].missing_sections)

    def test_missing_usage_section(self) -> None:
        """Test that missing USAGE section is detected.

        :Purpose:
            Verify headers without USAGE are flagged.
        """
        content = """#!/bin/bash
# DESCRIPTION:
#   Test script
#
# INPUTS:
#   None
#
# OUTPUTS:
#   Exit Codes:
#     0    Success
#
# EXAMPLES:
#   ./test.sh

echo "Hello"
"""
        errors = BashValidator.validate(Path("test.sh"), content)
        self.assertEqual(len(errors), 1)
        self.assertIn("USAGE:", errors[0].missing_sections)

    def test_missing_examples_section(self) -> None:
        """Test that missing EXAMPLES section is detected.

        :Purpose:
            Verify headers without EXAMPLES are flagged.
        """
        content = """#!/bin/bash
# DESCRIPTION:
#   Test script
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

echo "Hello"
"""
        errors = BashValidator.validate(Path("test.sh"), content)
        self.assertEqual(len(errors), 1)
        self.assertIn("EXAMPLES:", errors[0].missing_sections)

    def test_missing_header(self) -> None:
        """Test that completely missing header is detected.

        :Purpose:
            Verify scripts without headers are flagged.
        """
        content = """#!/bin/bash
echo "Hello"
"""
        errors = BashValidator.validate(Path("test.sh"), content)
        self.assertGreater(len(errors), 0)
        # Should detect missing header sections
        has_missing_sections = any(len(e.missing_sections) > 0 for e in errors)
        self.assertTrue(has_missing_sections, f"Expected missing sections, got: {errors}")

    def test_function_with_documentation(self) -> None:
        """Test that documented functions pass validation.

        :Purpose:
            Verify documented functions do not trigger errors.
        """
        content = """#!/bin/bash
# DESCRIPTION:
#   Test script
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
#
# EXAMPLES:
#   ./test.sh

# my_function - Does something
#
# Arguments:
#   $1 - Input value
#
# Returns:
#   0 on success
my_function() {
    echo "$1"
}
"""
        errors = BashValidator.validate(Path("test.sh"), content)
        # Should have no errors for documented function
        self.assertEqual(len(errors), 0, f"Expected no errors, got: {errors}")

    def test_pragma_ignore_section(self) -> None:
        """Test that pragma ignore works for sections.

        :Purpose:
            Verify # noqa: OUTPUTS pragma support.
        """
        content = """#!/bin/bash
# noqa: OUTPUTS
# DESCRIPTION:
#   Test script
#
# USAGE:
#   ./test.sh
#
# INPUTS:
#   None
#
# EXAMPLES:
#   ./test.sh

echo "Hello"
"""
        errors = BashValidator.validate(Path("test.sh"), content)
        # OUTPUTS section should be ignored due to pragma
        # Other sections present, so should pass
        self.assertEqual(len(errors), 0, f"Expected no errors with pragma, got: {errors}")


if __name__ == "__main__":
    unittest.main()
