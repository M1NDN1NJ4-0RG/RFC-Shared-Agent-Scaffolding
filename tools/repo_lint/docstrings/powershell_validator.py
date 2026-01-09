#!/usr/bin/env python3
# noqa: EXITCODES
"""PowerShell script docstring validator.

This module validates PowerShell script comment-based help documentation,
including file-level comment blocks and function documentation.

Uses PowerShell's native AST parser via Parser::ParseFile to extract symbols
without executing the script (per Phase 0 Item 0.9.3).

:Purpose:
    Enforce PowerShell docstring contracts as defined in
    docs/contributing/docstring-contracts/powershell.md

:Environment Variables:
    None

:Examples:
    Validate a PowerShell script::

        from docstring_validators.powershell_validator import PowerShellValidator
        errors = PowerShellValidator.validate(file_path, content)

:Exit Codes:
    N/A - This is a library module, not an executable script
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import List

from .common import ValidationError, check_symbol_pragma_exemption


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
        :rtype: List[ValidationError]
        """
        errors = []

        # File-level validation
        file_error = PowerShellValidator._validate_file_help(file_path, content)
        if file_error:
            errors.append(file_error)

        # Symbol-level validation using AST parser
        symbol_errors = PowerShellValidator._validate_functions(file_path, content)
        errors.extend(symbol_errors)

        return errors

    @staticmethod
    def _validate_file_help(file_path: Path, content: str) -> ValidationError | None:
        """Validate file-level comment-based help block.

        :param file_path: Path to PowerShell file
        :param content: File content as string

        :returns: ValidationError if file help is missing required sections, None otherwise
        :rtype: ValidationError | None
        """
        # Check for comment-based help block
        if "<#" not in content or "#>" not in content:
            return ValidationError(
                str(file_path),
                ["comment-based help block"],
                "Expected <# ... #> comment-based help block",
            )

        # Extract help block
        match = re.search(r"<#(.+?)#>", content, re.DOTALL)
        if not match:
            return ValidationError(
                str(file_path),
                ["comment-based help block"],
                "Could not parse <# ... #> block",
            )

        help_block = match.group(1)

        missing = []
        for i, pattern in enumerate(PowerShellValidator.REQUIRED_SECTIONS):
            if not re.search(pattern, help_block, re.IGNORECASE):
                missing.append(PowerShellValidator.SECTION_NAMES[i])

        if missing:
            return ValidationError(str(file_path), missing, "Expected PowerShell comment-based help")
        return None

    @staticmethod
    def _validate_functions(file_path: Path, content: str) -> List[ValidationError]:
        """Validate PowerShell function documentation using native AST parser.

        Uses Parser::ParseFile via helper script (per Phase 0 Item 0.9.3).
        Detects function definitions and checks for comment-based help blocks.

        :param file_path: Path to PowerShell file
        :param content: File content as string (for pragma checking)

        :returns: List of validation errors for functions
        :rtype: List[ValidationError]
        """
        errors = []

        # Find the helper script (renamed to PascalCase)
        helper_script = Path(__file__).parent / "helpers" / "ParsePowershellAst.ps1"
        if not helper_script.exists():
            # Fallback: skip symbol-level validation if helper not available
            # (This allows incremental migration)
            return []

        try:
            # Run PowerShell parser helper
            result = subprocess.run(
                ["pwsh", "-NoProfile", "-NonInteractive", "-File", str(helper_script), "-FilePath", str(file_path)],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                # Parser failed - report as error
                return [
                    ValidationError(
                        str(file_path),
                        ["PowerShell AST parse"],
                        f"Failed to parse PowerShell script: {result.stderr}",
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
                            ["PowerShell syntax"],
                            error_msg,
                        )
                    )

            # Split content into lines once for all pragma checks
            lines = content.split("\n")

            # Validate each function
            for func in parse_result.get("functions", []):
                func_name = func.get("name")
                func_line = func.get("line")
                has_help = func.get("has_help", False)
                help_sections = func.get("help_sections", [])

                # Check for pragma exemption using shared helper
                if check_symbol_pragma_exemption(lines, func_line):
                    continue

                if not has_help:
                    errors.append(
                        ValidationError(
                            str(file_path),
                            ["function help block"],
                            "Function must have comment-based help with .SYNOPSIS, .DESCRIPTION, etc.",
                            symbol_name=func_name,
                            line_number=func_line,
                        )
                    )
                else:
                    # Check for minimum required sections in function help
                    required_func_sections = [".SYNOPSIS", ".DESCRIPTION"]
                    missing_sections = [s for s in required_func_sections if s not in help_sections]

                    if missing_sections:
                        errors.append(
                            ValidationError(
                                str(file_path),
                                missing_sections,
                                "Function help missing required sections",
                                symbol_name=func_name,
                                line_number=func_line,
                            )
                        )

        except subprocess.TimeoutExpired:
            errors.append(
                ValidationError(
                    str(file_path),
                    ["PowerShell parser timeout"],
                    "PowerShell AST parser timed out (file too large or complex)",
                )
            )
        except (json.JSONDecodeError, subprocess.SubprocessError) as e:
            errors.append(
                ValidationError(
                    str(file_path),
                    ["PowerShell parser error"],
                    f"Failed to parse PowerShell AST output: {e}",
                )
            )

        return errors
