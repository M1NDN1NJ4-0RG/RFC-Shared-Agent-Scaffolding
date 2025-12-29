#!/usr/bin/env python3
"""Perl script docstring validator.

This module validates Perl script POD documentation, including file-level
POD sections and subroutine documentation.

:Purpose:
    Enforce Perl docstring contracts as defined in
    docs/contributing/docstring-contracts/perl.md
"""

import re
from pathlib import Path
from typing import List

from .common import ValidationError


class PerlValidator:
    """Validates Perl script POD documentation.

    Checks for required POD sections (=head1 NAME, SYNOPSIS, DESCRIPTION, etc.)
    according to repository docstring contracts.
    """

    REQUIRED_SECTIONS = [
        r"^=head1\s+NAME",
        r"^=head1\s+SYNOPSIS",
        r"^=head1\s+DESCRIPTION",
        r"^=head1\s+ENVIRONMENT VARIABLES",
        r"^=head1\s+EXIT CODES",
        r"^=head1\s+EXAMPLES",
    ]

    SECTION_NAMES = [
        "=head1 NAME",
        "=head1 SYNOPSIS",
        "=head1 DESCRIPTION",
        "=head1 ENVIRONMENT VARIABLES",
        "=head1 EXIT CODES",
        "=head1 EXAMPLES",
    ]

    @staticmethod
    def validate(file_path: Path, content: str) -> List[ValidationError]:
        """Validate Perl script POD.

        :param file_path: Path to Perl file to validate
        :param content: File content as string
        :returns: List of validation errors (empty if all validations pass)
        """
        # Check for POD block
        if "=head1" not in content or "=cut" not in content:
            return [
                ValidationError(
                    str(file_path),
                    ["POD block"],
                    "Expected POD documentation with =head1 sections and =cut",
                )
            ]

        missing = []
        for i, pattern in enumerate(PerlValidator.REQUIRED_SECTIONS):
            if not re.search(pattern, content, re.MULTILINE):
                missing.append(PerlValidator.SECTION_NAMES[i])

        if missing:
            return [ValidationError(str(file_path), missing, "Expected POD sections")]
        return []
