#!/usr/bin/env python3
# noqa: EXITCODES
"""Rust module docstring validator.

This module validates Rust module documentation using rustdoc comments,
including module-level documentation and public item documentation.

:Purpose:
    Enforce Rust docstring contracts as defined in
    docs/contributing/docstring-contracts/rust.md

:Environment Variables:
    None

:Examples:
    Validate a Rust module::

        from docstring_validators.rust_validator import RustValidator
        errors = RustValidator.validate(file_path, content)

:Exit Codes:
    N/A - This is a library module, not an executable script
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List

from .common import ValidationError


class RustValidator:
    """Validates Rust module documentation using rustdoc comments.

    Checks for required module-level documentation (//!) with Purpose
    and Examples sections according to repository docstring contracts.
    """

    REQUIRED_SECTIONS = [
        r"^//!\s*#\s*Purpose",
        r"^//!\s*#\s*Examples",
    ]

    # For main.rs, also require Exit Behavior/Exit Codes
    EXIT_SECTIONS = [r"^//!\s*#\s*Exit\s+(Behavior|Codes)"]

    SECTION_NAMES = ["# Purpose", "# Examples"]

    @staticmethod
    def validate(file_path: Path, content: str) -> List[ValidationError]:
        """Validate Rust module documentation.

        :param file_path: Path to Rust file to validate
        :param content: File content as string
        :returns: List of validation errors (empty if all validations pass)
        :rtype: List[ValidationError]
        """
        # Check for module-level docs (//!)
        if "//!" not in content:
            return [
                ValidationError(
                    str(file_path),
                    ["module documentation (//!)"],
                    "Expected module-level documentation with //!",
                )
            ]

        # Extract module docs (first 100 lines)
        lines = content.split("\n")[:100]
        module_docs = "\n".join([line for line in lines if line.strip().startswith("//!")])

        missing = []
        for i, pattern in enumerate(RustValidator.REQUIRED_SECTIONS):
            if not re.search(pattern, module_docs, re.MULTILINE | re.IGNORECASE):
                missing.append(RustValidator.SECTION_NAMES[i])

        # For main.rs, check for Exit Behavior/Exit Codes
        if file_path.name == "main.rs":
            has_exit = any(
                re.search(pattern, module_docs, re.MULTILINE | re.IGNORECASE) for pattern in RustValidator.EXIT_SECTIONS
            )
            if not has_exit:
                missing.append("# Exit Behavior or # Exit Codes")

        if missing:
            return [ValidationError(str(file_path), missing, "Expected Rustdoc sections in module docs")]
        return []
