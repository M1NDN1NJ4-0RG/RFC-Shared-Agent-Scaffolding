"""Docstring validation for repo_lint.

:Purpose:
    Provides internal docstring validation for all supported languages.
    This module consolidates validation logic that was previously in
    scripts/validate_docstrings.py into a first-class repo_lint feature.

:Architecture:
    - Language-specific validators (python_validator, bash_validator, etc.)
    - Common utilities (ValidationError, pragma checking)
    - Helper scripts for parsing (PowerShell AST, Perl PPI, Bash tree-sitter)
    - Main validator interface for unified access

:Supported Languages:
    - Python (AST-based)
    - Bash (regex + tree-sitter)
    - PowerShell (AST via helper script)
    - Perl (PPI via helper script)
    - Rust (regex-based)
    - YAML (comment parsing)

:Environment Variables:
    None

:Examples:
    Validate Python files::

        from tools.repo_lint.docstrings.python_validator import PythonValidator
        errors = PythonValidator.validate(file_path, content)

    Use the main validator interface::

        from tools.repo_lint.docstrings.validator import validate_files
        errors = validate_files(files, language="python")

:Exit Codes:
    N/A - This is a library module, not an executable script
"""

from __future__ import annotations

__all__ = ["ValidationError", "validate_files"]

from tools.repo_lint.docstrings.common import ValidationError
from tools.repo_lint.docstrings.validator import validate_files
