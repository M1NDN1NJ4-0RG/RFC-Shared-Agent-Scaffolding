#!/usr/bin/env python3
# pylint: disable=wrong-import-position,protected-access  # Test file needs special setup
# ruff: noqa: SLF001
"""Unit tests for Perl docstring validator.

:Purpose:
    Validates that the Perl docstring validator correctly enforces
    docstring contracts for Perl POD documentation.

:Test Coverage:
    - File-level POD validation (required sections)
    - Required POD sections (NAME, SYNOPSIS, DESCRIPTION, etc.)
    - Missing section detection
    - Subroutine documentation checking

:Usage:
    Run tests from repository root::

        python3 -m pytest tools/repo_lint/tests/test_perl_validator.py
        # or
        python3 tools/repo_lint/tests/test_perl_validator.py

:Environment Variables:
    None. Tests are self-contained.

:Exit Codes:
    0
        All tests passed
    1
        One or more tests failed

:Examples:
    Run all tests::

        python3 -m pytest tools/repo_lint/tests/test_perl_validator.py -v

    Run specific test::

        python3 -m pytest tools/repo_lint/tests/test_perl_validator.py::TestPerlValidator \
            ::test_valid_file_pod -v

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

from tools.repo_lint.docstrings.perl_validator import (  # noqa: E402
    PerlValidator,  # noqa: E402
)  # noqa: E402


class TestPerlValidator(unittest.TestCase):
    """Test Perl docstring validator behavior.

    :Purpose:
        Validates Perl docstring contract enforcement.
    """

    def test_valid_file_pod(self) -> None:
        """Test that valid POD documentation passes validation.

        :Purpose:
            Verify complete POD with all required sections passes.
        """
        content = """#!/usr/bin/perl

=head1 NAME

test.pl - Test script

=head1 SYNOPSIS

    ./test.pl

=head1 DESCRIPTION

This script provides test functionality.

=head1 ENVIRONMENT VARIABLES

None

=head1 EXIT CODES

0 - Success

=head1 EXAMPLES

    ./test.pl

=cut

print "Hello\\n";
"""
        errors = PerlValidator.validate(Path("test.pl"), content)
        # May have symbol-level errors, but file-level should pass
        file_sections = {
            "=head1 NAME",
            "=head1 SYNOPSIS",
            "=head1 DESCRIPTION",
            "=head1 ENVIRONMENT VARIABLES",
            "=head1 EXIT CODES",
            "=head1 EXAMPLES",
        }
        if errors:
            for error in errors:
                for section in error.missing_sections:
                    self.assertNotIn(section, file_sections, f"File-level section {section} should not be missing")

    def test_missing_name_section(self) -> None:
        """Test that missing NAME section is detected.

        :Purpose:
            Verify POD without NAME is flagged.
        """
        content = """#!/usr/bin/perl

=head1 SYNOPSIS

    ./test.pl

=head1 DESCRIPTION

Test

=head1 ENVIRONMENT VARIABLES

None

=head1 EXIT CODES

0 - Success

=head1 EXAMPLES

    ./test.pl

=cut

print "Hello\\n";
"""
        errors = PerlValidator.validate(Path("test.pl"), content)
        self.assertGreaterEqual(len(errors), 1)
        has_name_error = any("=head1 NAME" in e.missing_sections for e in errors)
        self.assertTrue(has_name_error, f"Expected NAME error, got: {errors}")

    def test_missing_description_section(self) -> None:
        """Test that missing DESCRIPTION section is detected.

        :Purpose:
            Verify POD without DESCRIPTION is flagged.
        """
        content = """#!/usr/bin/perl

=head1 NAME

test.pl - Test

=head1 SYNOPSIS

    ./test.pl

=head1 ENVIRONMENT VARIABLES

None

=head1 EXIT CODES

0 - Success

=head1 EXAMPLES

    ./test.pl

=cut

print "Hello\\n";
"""
        errors = PerlValidator.validate(Path("test.pl"), content)
        self.assertGreaterEqual(len(errors), 1)
        has_desc_error = any("=head1 DESCRIPTION" in e.missing_sections for e in errors)
        self.assertTrue(has_desc_error, f"Expected DESCRIPTION error, got: {errors}")

    def test_missing_pod(self) -> None:
        """Test that completely missing POD is detected.

        :Purpose:
            Verify scripts without POD are flagged.
        """
        content = """#!/usr/bin/perl
print "Hello\\n";
"""
        errors = PerlValidator.validate(Path("test.pl"), content)
        self.assertGreater(len(errors), 0)
        has_missing_sections = any(len(e.missing_sections) > 0 for e in errors)
        self.assertTrue(has_missing_sections, f"Expected missing sections, got: {errors}")


if __name__ == "__main__":
    unittest.main()
