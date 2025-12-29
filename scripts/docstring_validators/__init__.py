#!/usr/bin/env python3
# noqa: EXITCODES
"""Docstring validators package for RFC-Shared-Agent-Scaffolding.

This package contains language-specific validators for enforcing docstring
contracts across the repository.

:Purpose:
    Provide modular, language-specific docstring validation for all repository code

:Environment Variables:
    SKIP_CONTENT_CHECKS
        Set by main script to control exit code content validation

:Examples:
    Import a validator::

        from docstring_validators.python_validator import PythonValidator
        errors = PythonValidator.validate(file_path, content)

:Exit Codes:
    N/A - This is a library package, not an executable script
"""

from .common import ValidationError, check_pragma_ignore, validate_exit_codes_content

__all__ = [
    "ValidationError",
    "check_pragma_ignore",
    "validate_exit_codes_content",
]
