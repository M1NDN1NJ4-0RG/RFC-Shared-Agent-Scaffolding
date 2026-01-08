#!/usr/bin/env python3
# noqa: EXITCODES
"""YAML file docstring validator.

This module validates YAML file documentation headers, including workflow
files and configuration files.

:Purpose:
    Enforce YAML docstring contracts as defined in
    docs/contributing/docstring-contracts/yaml.md

:Environment Variables:
    None

:Examples:
    Validate a YAML file::

        from docstring_validators.yaml_validator import YAMLValidator
        errors = YAMLValidator.validate(file_path, content)

:Exit Codes:
    N/A - This is a library module, not an executable script
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List

from .common import ValidationError


class YAMLValidator:
    """Validates YAML file documentation headers.

    Checks for required comment header sections in YAML workflow and config files
    according to repository docstring contracts.
    """

    REQUIRED_SECTIONS = [
        r"^#\s*(Workflow|File):",
        r"^#\s*Purpose:",
        r"^#\s*(Triggers|Usage):",
        r"^#\s*(Dependencies|Inputs):",
        r"^#\s*(Outputs|Side effects):",
        r"^#\s*Notes?:",
    ]

    SECTION_NAMES = [
        "Workflow: or File:",
        "Purpose:",
        "Triggers: or Usage:",
        "Dependencies: or Inputs:",
        "Outputs: or Side effects:",
        "Notes: or Note:",
    ]

    @staticmethod
    def _extract_header_block(content: str) -> str:
        """Extract the complete comment header block from the start of the file.

        The header block consists of all consecutive comment lines (starting with #)
        from the beginning of the file, stopping at the first non-comment, non-blank line.
        YAML document separators (---) at the start are included, but subsequent ones
        stop extraction (indicating multiple documents).

        :param content: File content as string
        :returns: The complete header block as a string
        """
        lines = content.split("\n")
        header_lines = []
        seen_content = False  # Track if we've seen actual YAML content yet

        for line in lines:
            stripped = line.strip()

            # Always include comments and blank lines in header
            if stripped.startswith("#") or stripped == "":
                header_lines.append(line)
                continue

            # Handle YAML document separator (---)
            if stripped == "---":
                # If we haven't seen content yet, include this separator (document start)
                # If we have seen content, stop here (multiple documents)
                if not seen_content:
                    header_lines.append(line)
                    continue

                # Multiple documents - stop extraction
                break

            # First actual YAML content - set flag and stop extraction
            seen_content = True
            break

        return "\n".join(header_lines)

    @staticmethod
    def validate(file_path: Path, content: str) -> List[ValidationError]:
        """Validate YAML file documentation header.

        :param file_path: Path to YAML file to validate
        :param content: File content as string
        :returns: List of validation errors (empty if all validations pass)
        """
        # Extract the complete header block dynamically instead of using a fixed line limit
        header = YAMLValidator._extract_header_block(content)

        missing = []
        for i, pattern in enumerate(YAMLValidator.REQUIRED_SECTIONS):
            if not re.search(pattern, header, re.MULTILINE | re.IGNORECASE):
                missing.append(YAMLValidator.SECTION_NAMES[i])

        if missing:
            return [
                ValidationError(
                    str(file_path),
                    missing,
                    "Expected top-of-file comment header with # prefix",
                )
            ]
        return []
