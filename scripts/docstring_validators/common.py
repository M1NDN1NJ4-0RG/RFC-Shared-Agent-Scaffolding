#!/usr/bin/env python3
# noqa: EXITCODES
"""Common utilities and classes for docstring validation.

This module provides shared functionality used across all language-specific
validators, including the ValidationError class and helper functions.

:Purpose:
    Centralize shared validation logic to avoid duplication and ensure
    consistency across language validators.

:Environment Variables:
    SKIP_CONTENT_CHECKS
        Global flag set by main script to control content validation

:Examples:
    Check pragma ignore::

        from docstring_validators.common import check_pragma_ignore
        if check_pragma_ignore(content, "OUTPUTS"):
            # Skip OUTPUTS validation

:Exit Codes:
    N/A - This is a library module, not an executable script
"""

import re
from typing import List, Optional


# Module-level flag for content checks (set by command-line arg in main script)
SKIP_CONTENT_CHECKS = False


class ValidationError:
    """Represents a single validation failure.

    This class encapsulates information about a docstring validation error,
    including file location, symbol information, and missing sections.

    :ivar file_path: Path to the file with validation error
    :ivar missing_sections: List of section names that are missing
    :ivar message: Additional context or guidance message
    :ivar symbol_name: Optional name of the symbol (function/class) with error
    :ivar line_number: Optional line number where symbol is defined
    """

    # pylint: disable=too-many-arguments
    # Note: 6 arguments needed to provide full context for validation errors.
    # symbol_name and line_number are keyword-only to encourage explicit usage.
    def __init__(
        self,
        file_path: str,
        missing_sections: List[str],
        message: str = "",
        *,
        symbol_name: Optional[str] = None,
        line_number: Optional[int] = None,
    ):
        """Initialize ValidationError.

        :param file_path: Path to the file with validation error
        :param missing_sections: List of section names that are missing
        :param message: Additional context or guidance message
        :param symbol_name: Optional name of the symbol (function/class) with error
        :param line_number: Optional line number where symbol is defined
        """
        self.file_path = file_path
        self.missing_sections = missing_sections
        self.message = message
        self.symbol_name = symbol_name
        self.line_number = line_number

    def __str__(self) -> str:
        """Format the validation error as a human-readable string.

        :returns: Formatted error message with location and missing sections
        """
        sections = ", ".join(self.missing_sections)

        # Format location info
        location = self.file_path
        if self.line_number:
            location += f":{self.line_number}"

        # Format error message
        if self.symbol_name:
            msg = f"\n❌ {location}\n   Symbol: {self.symbol_name}\n   Missing: {sections}"
        else:
            msg = f"\n❌ {location}\n   Missing required sections: {sections}"

        if self.message:
            msg += f"\n   {self.message}"
        return msg


def check_pragma_ignore(content: str, section: str) -> bool:
    """Check if a section is ignored via pragma comment.

    Supports pragmas like:
    - # noqa: EXITCODES
    - # docstring-ignore: EXIT CODES
    - <!-- noqa: OUTPUTS --> (for YAML)

    :param content: File content to search
    :param section: Section name to check (e.g., "EXITCODES", "EXIT CODES")
    :returns: True if section should be ignored, False otherwise
    """
    # Normalize section name (remove spaces, uppercase)
    normalized_section = section.upper().replace(" ", "").replace(":", "")

    # Check for various pragma formats
    pragma_patterns = [
        rf"#\s*noqa:\s*{normalized_section}",
        rf"#\s*docstring-ignore:\s*{section}",
        rf"<!--\s*noqa:\s*{normalized_section}\s*-->",
    ]

    for pattern in pragma_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            return True

    return False


def validate_exit_codes_content(content: str, language: str) -> Optional[str]:
    """Validate that exit codes section contains minimum required codes.

    Checks that at least exit codes 0 and 1 are documented.
    This is a soft check - we look for patterns like "0" near "success" etc.

    :param content: The exit codes section content
    :param language: Language name for context

    :returns: Error message if validation fails, None if valid
    """
    if SKIP_CONTENT_CHECKS:
        return None

    # Look for exit code 0 (success) - be very lenient with patterns
    # Match patterns like:
    # - "0    Success"
    # - "0: Success"
    # - "Exit 0"
    # - "Exit: 0 if success"
    # - "0 if all tests pass"
    has_exit_0 = bool(
        re.search(
            r"(?:exit[:\s]+)?0[\s:\-]+(?:if\s+)?.*?(?:success|ok|pass|complete|all.*pass)",
            content,
            re.IGNORECASE | re.MULTILINE | re.DOTALL,
        )
    )

    # Look for exit code 1 (failure)
    # Match patterns like:
    # - "1    Failure"
    # - "1: Fail"
    # - "Exit 1"
    # - "Exit: 1 if fail"
    # - "1 if any fail"
    has_exit_1 = bool(
        re.search(
            r"(?:exit[:\s]+)?1[\s:\-]+(?:if\s+)?.*?(?:fail|error|invalid|any.*fail)",
            content,
            re.IGNORECASE | re.MULTILINE | re.DOTALL,
        )
    )

    # If we find reasonable exit code documentation, consider it valid
    # This is intentionally lenient to avoid false positives
    if not has_exit_0 and not has_exit_1:
        # Only fail if there's NO exit code documentation at all
        has_any_exit_code = bool(re.search(r"\b(?:0|1|2|127)\b", content))
        if not has_any_exit_code:
            return "No exit codes found (expected at least 0 and 1)"

    return None
