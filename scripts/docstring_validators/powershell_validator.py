#!/usr/bin/env python3
"""PowerShell script docstring validator.

This module validates PowerShell script comment-based help documentation,
including file-level comment blocks and function documentation.

:Purpose:
    Enforce PowerShell docstring contracts as defined in
    docs/contributing/docstring-contracts/powershell.md
"""

import re
from pathlib import Path
from typing import List

from .common import ValidationError


class PowerShellValidator:
    """Validates PowerShell script comment-based help documentation.

    Checks for presence of required .SYNOPSIS, .DESCRIPTION, and other
    comment-based help sections in PowerShell scripts.
    """

    REQUIRED_SECTIONS = [
        r"\.SYNOPSIS",
        r"\.DESCRIPTION",
        r"\.ENVIRONMENT",
        r"\.EXAMPLE",
        r"\.NOTES",
    ]

    SECTION_NAMES = [
        ".SYNOPSIS",
        ".DESCRIPTION",
        ".ENVIRONMENT",
        ".EXAMPLE",
        ".NOTES",
    ]

    @staticmethod
    def validate(file_path: Path, content: str) -> List[ValidationError]:
        """Validate PowerShell script docstring.

        :param file_path: Path to PowerShell file to validate
        :param content: File content as string

        :returns: List of validation errors (empty if all validations pass)
        """
        # Check for comment-based help block
        if "<#" not in content or "#>" not in content:
            return [
                ValidationError(
                    str(file_path),
                    ["comment-based help block"],
                    "Expected <# ... #> comment-based help block",
                )
            ]

        # Extract help block
        match = re.search(r"<#(.+?)#>", content, re.DOTALL)
        if not match:
            return [
                ValidationError(
                    str(file_path),
                    ["comment-based help block"],
                    "Could not parse <# ... #> block",
                )
            ]

        help_block = match.group(1)

        missing = []
        for i, pattern in enumerate(PowerShellValidator.REQUIRED_SECTIONS):
            if not re.search(pattern, help_block, re.IGNORECASE):
                missing.append(PowerShellValidator.SECTION_NAMES[i])

        if missing:
            return [ValidationError(str(file_path), missing, "Expected PowerShell comment-based help")]
        return []
