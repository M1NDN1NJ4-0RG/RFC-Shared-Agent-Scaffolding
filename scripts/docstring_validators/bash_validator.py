#!/usr/bin/env python3
# noqa: EXITCODES
"""Bash script docstring validator.

This module validates Bash script documentation, including file-level header
comments and individual function documentation blocks.

Uses tree-sitter with pinned Bash grammar for structure-aware parsing
(per Phase 0 Item 0.9.4).

:Purpose:
    Enforce Bash docstring contracts as defined in
    docs/contributing/docstring-contracts/bash.md

:Environment Variables:
    None

:Examples:
    Validate a Bash script::

        from docstring_validators.bash_validator import BashValidator
        errors = BashValidator.validate(file_path, content)

:Exit Codes:
    N/A - This is a library module, not an executable script
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import List

from .common import ValidationError, check_pragma_ignore, check_symbol_pragma_exemption, validate_exit_codes_content

# Import tree-sitter helper if available
try:
    # Add helpers directory to path
    helpers_dir = Path(__file__).parent / "helpers"
    if str(helpers_dir) not in sys.path:
        sys.path.insert(0, str(helpers_dir))

    from bash_treesitter import parse_bash_functions

    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False


class BashValidator:
    """Validates Bash script docstrings and function documentation.

    Checks both file-level header documentation and individual function
    comment blocks according to repository docstring contracts.
    """

    REQUIRED_SECTIONS = [
        r"#\s*DESCRIPTION:",
        r"#\s*USAGE:",
        r"#\s*INPUTS:",
        r"#\s*OUTPUTS:",
        r"#\s*EXAMPLES:",
    ]

    SECTION_NAMES = ["DESCRIPTION:", "USAGE:", "INPUTS:", "OUTPUTS:", "EXAMPLES:"]

    @staticmethod
    def validate(file_path: Path, content: str) -> List[ValidationError]:
        """Validate Bash script header and function docstrings.

        :param file_path: Path to Bash file to validate
        :param content: File content as string

        :returns: List of validation errors (empty if all validations pass)
        """
        errors = []

        # File-level validation
        file_error = BashValidator._validate_header(file_path, content)
        if file_error:
            errors.append(file_error)

        # Symbol-level validation
        symbol_errors = BashValidator._validate_functions(file_path, content)
        errors.extend(symbol_errors)

        return errors

    @staticmethod
    def _validate_header(file_path: Path, content: str) -> ValidationError | None:
        """Validate Bash script header documentation.

        :param file_path: Path to Bash file
        :param content: File content as string

        :returns: ValidationError if header is missing required sections, None otherwise
        """
        # Check for top-of-file comment block (first 100 lines)
        lines = content.split("\n")[:100]
        header = "\n".join(lines)

        # Check shebang
        if not content.startswith("#!/usr/bin/env bash") and not content.startswith("#!/bin/bash"):
            return ValidationError(
                str(file_path),
                ["shebang"],
                "Expected '#!/usr/bin/env bash' shebang",
            )

        missing = []
        for i, pattern in enumerate(BashValidator.REQUIRED_SECTIONS):
            section_name = BashValidator.SECTION_NAMES[i]

            # Check if section is ignored via pragma
            if check_pragma_ignore(content, section_name):
                continue

            if not re.search(pattern, header, re.IGNORECASE):
                missing.append(section_name)

        # Basic content validation for exit codes (if OUTPUTS present)
        if "OUTPUTS:" not in missing:
            # Extract OUTPUTS section content
            outputs_match = re.search(r"#\s*OUTPUTS:\s*\n((?:#.*\n)+)", header, re.IGNORECASE)
            if outputs_match:
                # Remove leading # from each line for easier pattern matching
                outputs_lines = outputs_match.group(1).split("\n")
                outputs_content = "\n".join(line.lstrip("#").strip() for line in outputs_lines if line.strip())
                exit_codes_error = validate_exit_codes_content(outputs_content, "Bash")
                if exit_codes_error and not check_pragma_ignore(content, "EXITCODES"):
                    return ValidationError(
                        str(file_path),
                        ["OUTPUTS content"],
                        f"Exit codes incomplete: {exit_codes_error}",
                    )

        if missing:
            return ValidationError(
                str(file_path),
                missing,
                "Expected top-of-file comment block with # prefix",
            )
        return None

    @staticmethod
    def _validate_functions(file_path: Path, content: str) -> List[ValidationError]:
        """Validate Bash function documentation.

        Uses tree-sitter parser if available (per Phase 0 Item 0.9.4).
        Falls back to regex-based detection if tree-sitter is not installed.

        :param file_path: Path to Bash file
        :param content: File content

        :returns: List of validation errors for functions
        """
        errors = []

        # Try tree-sitter first (preferred)
        if TREE_SITTER_AVAILABLE:
            parse_result = parse_bash_functions(file_path)

            # Check for parse errors
            if parse_result.get("errors"):
                # If tree-sitter fails, fall back to regex
                return BashValidator._validate_functions_regex(file_path, content)

            # Split content into lines once for all pragma checks
            lines = content.split("\n")

            # Validate each function
            for func in parse_result.get("functions", []):
                func_name = func.get("name")
                func_line = func.get("line")
                has_doc = func.get("has_doc_comment", False)

                # Check for pragma exemption using shared helper
                if check_symbol_pragma_exemption(lines, func_line):
                    continue

                # Per Phase 5.5 policy: Do NOT skip private/internal functions
                # All functions must have documentation unless explicitly exempted via pragma

                if not has_doc:
                    errors.append(
                        ValidationError(
                            str(file_path),
                            ["function documentation"],
                            "Function must have comment block with description, args, returns",
                            symbol_name=f"{func_name}()",
                            line_number=func_line,
                        )
                    )

            return errors

        # Fallback to regex-based parsing
        return BashValidator._validate_functions_regex(file_path, content)

    @staticmethod
    def _validate_functions_regex(file_path: Path, content: str) -> List[ValidationError]:
        """Fallback regex-based function validation.

        Used when tree-sitter is not available.
        This is the original implementation - kept for compatibility.

        :param file_path: Path to Bash file
        :param content: File content

        :returns: List of validation errors for functions
        """
        errors = []
        lines = content.split("\n")

        # Pattern to match bash function definitions:
        # - function name() {
        # - name() {
        # - function name {
        func_pattern = re.compile(
            r"^\s*(?:function\s+)?([a-zA-Z_][a-zA-Z0-9_]*)\s*\(\s*\)\s*\{?|^\s*function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\{"
        )

        for i, line in enumerate(lines):
            match = func_pattern.match(line)
            if match:
                func_name = match.group(1) or match.group(2)
                lineno = i + 1

                # Check for pragma ignore on the function line
                if re.search(r"#\s*noqa:\s*FUNCTION", line):
                    continue

                # Per Phase 5.5 policy: Do NOT skip private/internal functions
                # All functions must have documentation unless explicitly exempted via pragma

                # Look for comment block immediately preceding the function
                # A proper doc block should have at least one comment line with description
                comment_block = []
                j = i - 1
                while j >= 0 and (lines[j].strip().startswith("#") or lines[j].strip() == ""):
                    if lines[j].strip().startswith("#"):
                        comment_block.insert(0, lines[j])
                    elif lines[j].strip() == "" and comment_block:
                        # Empty line after comments - stop here
                        break
                    j -= 1

                if not comment_block:
                    errors.append(
                        ValidationError(
                            str(file_path),
                            ["function documentation"],
                            "Function must have comment block with description, args, returns",
                            symbol_name=f"{func_name}()",
                            line_number=lineno,
                        )
                    )
                else:
                    # Check if comment block has minimum required info
                    # Very lenient check - just ensure there's some description text
                    # (more than just "# Arguments:" or similar headers)
                    has_description = any(
                        len(line.lstrip("#").strip()) > 3 and not line.lstrip("#").strip().endswith(":")
                        for line in comment_block
                    )

                    if not has_description:
                        errors.append(
                            ValidationError(
                                str(file_path),
                                ["function description"],
                                "Function comment block must include description text",
                                symbol_name=f"{func_name}()",
                                line_number=lineno,
                            )
                        )

        return errors
