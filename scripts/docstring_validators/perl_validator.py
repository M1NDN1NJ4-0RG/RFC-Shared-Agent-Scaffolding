#!/usr/bin/env python3
# noqa: EXITCODES
"""Perl script docstring validator.

This module validates Perl script POD documentation, including file-level
POD sections and subroutine documentation.

Uses PPI (Perl Parsing Interface) via subprocess to extract symbols
without executing the script (per Phase 0 Item 0.9.5).

:Purpose:
    Enforce Perl docstring contracts as defined in
    docs/contributing/docstring-contracts/perl.md

:Environment Variables:
    None

:Examples:
    Validate a Perl script::

        from docstring_validators.perl_validator import PerlValidator
        errors = PerlValidator.validate(file_path, content)

:Exit Codes:
    N/A - This is a library module, not an executable script
"""

import json
import re
import subprocess
from pathlib import Path
from typing import List, Optional

from .common import ValidationError, check_symbol_pragma_exemption


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
        errors = []

        # File-level validation
        file_error = PerlValidator._validate_file_pod(file_path, content)
        if file_error:
            errors.append(file_error)

        # Symbol-level validation using PPI parser
        symbol_errors = PerlValidator._validate_subroutines(file_path, content)
        errors.extend(symbol_errors)

        return errors

    @staticmethod
    def _validate_file_pod(file_path: Path, content: str) -> Optional[ValidationError]:
        """Validate file-level POD documentation.

        :param file_path: Path to Perl file
        :param content: File content as string

        :returns: ValidationError if file POD is missing required sections, None otherwise
        """
        # Check for POD block
        if "=head1" not in content or "=cut" not in content:
            return ValidationError(
                str(file_path),
                ["POD block"],
                "Expected POD documentation with =head1 sections and =cut",
            )

        missing = []
        for i, pattern in enumerate(PerlValidator.REQUIRED_SECTIONS):
            if not re.search(pattern, content, re.MULTILINE):
                missing.append(PerlValidator.SECTION_NAMES[i])

        if missing:
            return ValidationError(str(file_path), missing, "Expected POD sections")
        return None

    @staticmethod
    def _validate_subroutines(file_path: Path, content: str) -> List[ValidationError]:
        """Validate Perl subroutine documentation using PPI parser.

        Uses PPI via helper script (per Phase 0 Item 0.9.5).
        Detects subroutine definitions and checks for POD documentation.

        :param file_path: Path to Perl file
        :param content: File content as string (for pragma checking)

        :returns: List of validation errors for subroutines
        """
        errors = []

        # Find the helper script
        helper_script = Path(__file__).parent / "helpers" / "parse_perl_ppi.pl"
        if not helper_script.exists():
            # Fallback: skip symbol-level validation if helper not available
            # (This allows incremental migration)
            return []

        try:
            # Run Perl PPI parser helper
            result = subprocess.run(
                ["perl", str(helper_script), str(file_path)],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                # Parser failed - check if it's a PPI module error
                if "Can't locate PPI.pm" in result.stderr:
                    # PPI not installed - skip symbol validation for now
                    return []
                # Other error - report it
                return [
                    ValidationError(
                        str(file_path),
                        ["Perl PPI parse"],
                        f"Failed to parse Perl script: {result.stderr}",
                    )
                ]

            # Parse JSON output
            parse_result = json.loads(result.stdout)

            # Check for parse errors
            if parse_result.get("errors"):
                for error_msg in parse_result["errors"]:
                    errors.append(
                        ValidationError(
                            str(file_path),
                            ["Perl syntax"],
                            error_msg,
                        )
                    )

            # Split content into lines once for all pragma checks
            lines = content.split("\n")

            # Validate each subroutine
            for sub in parse_result.get("subs", []):
                sub_name = sub.get("name")
                sub_line = sub.get("line")
                has_pod = sub.get("has_pod", False)

                # Per Phase 5.5 policy: Do NOT skip private/internal subs
                # All subs must have documentation unless explicitly exempted via pragma

                # Check for pragma exemption using shared helper
                if check_symbol_pragma_exemption(lines, sub_line):
                    continue

                if not has_pod:
                    errors.append(
                        ValidationError(
                            str(file_path),
                            ["subroutine POD"],
                            "Subroutine must have POD documentation (=head2, =item, etc.)",
                            symbol_name=f"sub {sub_name}",
                            line_number=sub_line,
                        )
                    )
                else:
                    # Lenient check: if POD exists, consider it valid
                    # (More strict validation could check for specific sections)
                    pass

        except subprocess.TimeoutExpired:
            errors.append(
                ValidationError(
                    str(file_path),
                    ["Perl parser timeout"],
                    "Perl PPI parser timed out (file too large or complex)",
                )
            )
        except (json.JSONDecodeError, subprocess.SubprocessError) as e:
            errors.append(
                ValidationError(
                    str(file_path),
                    ["Perl parser error"],
                    f"Failed to parse Perl PPI output: {e}",
                )
            )

        return errors
