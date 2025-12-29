#!/usr/bin/env python3
"""Bash script docstring validator.

This module validates Bash script documentation, including file-level header
comments and individual function documentation blocks.

:Purpose:
    Enforce Bash docstring contracts as defined in
    docs/contributing/docstring-contracts/bash.md
"""

import re
from pathlib import Path
from typing import List, Optional

from .common import ValidationError, check_pragma_ignore, validate_exit_codes_content


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
    def _validate_header(file_path: Path, content: str) -> Optional[ValidationError]:
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

        Detects function definitions and checks for comment blocks preceding them.

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
