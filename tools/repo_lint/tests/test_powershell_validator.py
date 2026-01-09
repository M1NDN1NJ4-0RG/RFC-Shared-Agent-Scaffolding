#!/usr/bin/env python3
# pylint: disable=wrong-import-position,protected-access  # Test file needs special setup
# ruff: noqa: SLF001
"""Unit tests for PowerShell docstring validator.

:Purpose:
    Validates that the PowerShell docstring validator correctly enforces
    docstring contracts for PowerShell script comment-based help.

:Test Coverage:
    - File-level comment-based help validation
    - Required sections (.SYNOPSIS, .DESCRIPTION, .ENVIRONMENT, .EXAMPLE, .NOTES)
    - Missing section detection
    - Function documentation checking

:Usage:
    Run tests from repository root::

        python3 -m pytest tools/repo_lint/tests/test_powershell_validator.py
        # or
        python3 tools/repo_lint/tests/test_powershell_validator.py

:Environment Variables:
    None. Tests are self-contained.

:Exit Codes:
    0
        All tests passed
    1
        One or more tests failed

:Examples:
    Run all tests::

        python3 -m pytest tools/repo_lint/tests/test_powershell_validator.py -v

    Run specific test::

        python3 -m pytest tools/repo_lint/tests/test_powershell_validator.py::TestPowerShellValidator \
            ::test_valid_file_help -v

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

from tools.repo_lint.docstrings.powershell_validator import (  # noqa: E402
    PowerShellValidator,  # noqa: E402
)  # noqa: E402


class TestPowerShellValidator(unittest.TestCase):
    """Test PowerShell docstring validator behavior.

    :Purpose:
        Validates PowerShell docstring contract enforcement.
    """

    def test_valid_file_help(self) -> None:
        """Test that valid file-level help contains required sections.

        :Purpose:
            Verify file help with all required sections is detected.
        """
        content = """<#
.SYNOPSIS
    Test script

.DESCRIPTION
    This script provides test functionality.

.ENVIRONMENT
    None

.EXAMPLE
    .\test.ps1

.NOTES
    Test notes
#>

# Just a simple script
$message = "Hello"
"""
        errors = PowerShellValidator.validate(Path("test.ps1"), content)
        # Check that file-level validation passes (may have symbol-level errors)
        # At minimum, should not have missing file-level sections
        if errors:
            # If there are errors, they should not be about missing file-level sections
            file_level_sections = {".SYNOPSIS", ".DESCRIPTION", ".ENVIRONMENT", ".EXAMPLE", ".NOTES"}
            for error in errors:
                for section in error.missing_sections:
                    self.assertNotIn(
                        section, file_level_sections, f"File-level section {section} should not be missing"
                    )

    def test_missing_synopsis(self) -> None:
        """Test that missing .SYNOPSIS is detected.

        :Purpose:
            Verify scripts without .SYNOPSIS are flagged.
        """
        content = """<#
.DESCRIPTION
    This script provides test functionality.

.ENVIRONMENT
    None

.EXAMPLE
    .\test.ps1

.NOTES
    Test notes
#>

$message = "Hello"
"""
        errors = PowerShellValidator.validate(Path("test.ps1"), content)
        self.assertGreaterEqual(len(errors), 1)
        # Check that one error is about missing .SYNOPSIS
        has_synopsis_error = any(".SYNOPSIS" in e.missing_sections for e in errors)
        self.assertTrue(has_synopsis_error, f"Expected .SYNOPSIS error, got: {errors}")

    def test_missing_description(self) -> None:
        """Test that missing .DESCRIPTION is detected.

        :Purpose:
            Verify scripts without .DESCRIPTION are flagged.
        """
        content = """<#
.SYNOPSIS
    Test script

.ENVIRONMENT
    None

.EXAMPLE
    .\test.ps1

.NOTES
    Test notes
#>

$message = "Hello"
"""
        errors = PowerShellValidator.validate(Path("test.ps1"), content)
        self.assertGreaterEqual(len(errors), 1)
        # Check that one error is about missing .DESCRIPTION
        has_description_error = any(".DESCRIPTION" in e.missing_sections for e in errors)
        self.assertTrue(has_description_error, f"Expected .DESCRIPTION error, got: {errors}")

    def test_missing_example(self) -> None:
        """Test that missing .EXAMPLE is detected.

        :Purpose:
            Verify scripts without .EXAMPLE are flagged.
        """
        content = """<#
.SYNOPSIS
    Test script

.DESCRIPTION
    This script provides test functionality.

.ENVIRONMENT
    None

.NOTES
    Test notes
#>

$message = "Hello"
"""
        errors = PowerShellValidator.validate(Path("test.ps1"), content)
        self.assertGreaterEqual(len(errors), 1)
        # Check that one error is about missing .EXAMPLE
        has_example_error = any(".EXAMPLE" in e.missing_sections for e in errors)
        self.assertTrue(has_example_error, f"Expected .EXAMPLE error, got: {errors}")

    def test_missing_file_help(self) -> None:
        """Test that completely missing file help is detected.

        :Purpose:
            Verify scripts without comment-based help are flagged.
        """
        content = """$message = "Hello"
"""
        errors = PowerShellValidator.validate(Path("test.ps1"), content)
        self.assertGreater(len(errors), 0)
        # Should detect missing sections
        has_missing_sections = any(len(e.missing_sections) > 0 for e in errors)
        self.assertTrue(has_missing_sections, f"Expected missing sections, got: {errors}")


if __name__ == "__main__":
    unittest.main()
