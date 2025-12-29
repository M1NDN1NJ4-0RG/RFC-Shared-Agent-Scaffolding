#!/usr/bin/env python3
"""YAML file docstring validator.

This module validates YAML file documentation headers, including workflow
files and configuration files.

:Purpose:
    Enforce YAML docstring contracts as defined in
    docs/contributing/docstring-contracts/yaml.md
"""

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
    def validate(file_path: Path, content: str) -> List[ValidationError]:
        """Validate YAML file documentation header.

        :param file_path: Path to YAML file to validate
        :param content: File content as string
        :returns: List of validation errors (empty if all validations pass)
        """
        # Check first 50 lines for comment header (workflows can have long headers)
        lines = content.split("\n")[:50]
        header = "\n".join(lines)

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
