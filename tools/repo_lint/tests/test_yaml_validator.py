#!/usr/bin/env python3
# pylint: disable=wrong-import-position,protected-access  # Test file needs special setup
# ruff: noqa: SLF001
"""Unit tests for YAML docstring validator.

:Purpose:
    Validates that the YAML docstring validator correctly enforces
    docstring contracts for YAML file headers and workflow documentation.

:Test Coverage:
    - File header validation (required sections)
    - Missing section detection
    - Comment block extraction
    - YAML workflow vs config file validation

:Usage:
    Run tests from repository root::

        python3 -m pytest tools/repo_lint/tests/test_yaml_validator.py
        # or
        python3 tools/repo_lint/tests/test_yaml_validator.py

:Environment Variables:
    None. Tests are self-contained.

:Exit Codes:
    0
        All tests passed
    1
        One or more tests failed

:Examples:
    Run all tests::

        python3 -m pytest tools/repo_lint/tests/test_yaml_validator.py -v

    Run specific test::

        python3 -m pytest tools/repo_lint/tests/test_yaml_validator.py::TestYAMLValidator \
            ::test_valid_workflow_header -v

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

from tools.repo_lint.docstrings.yaml_validator import (  # noqa: E402
    YAMLValidator,  # noqa: E402
)  # noqa: E402


class TestYAMLValidator(unittest.TestCase):
    """Test YAML docstring validator behavior.

    :Purpose:
        Validates YAML docstring contract enforcement.
    """

    def test_valid_workflow_header(self) -> None:
        """Test that a valid workflow header passes validation.

        :Purpose:
            Verify complete header with all required sections passes.
        """
        content = """# Workflow: Test Workflow
#
# Purpose:
#   Test workflow purpose.
#
# Triggers:
#   - push
#
# Dependencies:
#   - actions/checkout@v4
#
# Outputs:
#   Test results
#
# Notes:
#   Test notes

---
name: Test
on: push
"""
        errors = YAMLValidator.validate(Path("test.yml"), content)
        self.assertEqual(len(errors), 0, f"Expected no errors, got: {errors}")

    def test_valid_file_header(self) -> None:
        """Test that a valid config file header passes validation.

        :Purpose:
            Verify File: header variant works.
        """
        content = """# File: Configuration
#
# Purpose:
#   Test config purpose.
#
# Usage:
#   Load this file
#
# Inputs:
#   Config values
#
# Side effects:
#   None
#
# Note:
#   Single note variant

---
key: value
"""
        errors = YAMLValidator.validate(Path("config.yml"), content)
        self.assertEqual(len(errors), 0, f"Expected no errors, got: {errors}")

    def test_missing_purpose_section(self) -> None:
        """Test that missing Purpose section is detected.

        :Purpose:
            Verify headers without Purpose are flagged.
        """
        content = """# Workflow: Test
#
# Triggers:
#   - push
#
# Dependencies:
#   - actions/checkout@v4
#
# Outputs:
#   Results
#
# Notes:
#   Notes

---
name: Test
"""
        errors = YAMLValidator.validate(Path("test.yml"), content)
        self.assertEqual(len(errors), 1)
        self.assertIn("Purpose:", errors[0].missing_sections)

    def test_missing_triggers_section(self) -> None:
        """Test that missing Triggers section is detected.

        :Purpose:
            Verify headers without Triggers/Usage are flagged.
        """
        content = """# Workflow: Test
#
# Purpose:
#   Test purpose
#
# Dependencies:
#   - actions/checkout@v4
#
# Outputs:
#   Results
#
# Notes:
#   Notes

---
name: Test
"""
        errors = YAMLValidator.validate(Path("test.yml"), content)
        self.assertEqual(len(errors), 1)
        self.assertIn("Triggers: or Usage:", errors[0].missing_sections)

    def test_missing_header(self) -> None:
        """Test that completely missing header is detected.

        :Purpose:
            Verify YAML files without headers are flagged.
        """
        content = """---
name: Test
on: push
"""
        errors = YAMLValidator.validate(Path("test.yml"), content)
        self.assertGreater(len(errors), 0)
        # Should detect missing sections
        has_missing_sections = any(len(e.missing_sections) > 0 for e in errors)
        self.assertTrue(has_missing_sections, f"Expected missing sections, got: {errors}")

    def test_header_extraction_stops_at_content(self) -> None:
        """Test that header extraction stops at first YAML content.

        :Purpose:
            Verify header block extraction logic.
        """
        content = """# Workflow: Test
#
# Purpose:
#   Test

---
name: Test
# This is not part of header
"""
        # The validator should only check the header block
        # This is more of an implementation detail test
        header = YAMLValidator._extract_header_block(content)  # pylint: disable=protected-access
        self.assertIn("# Workflow: Test", header)
        self.assertNotIn("# This is not part of header", header)


if __name__ == "__main__":
    unittest.main()
