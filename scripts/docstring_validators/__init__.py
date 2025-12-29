"""Docstring validators package for RFC-Shared-Agent-Scaffolding.

This package contains language-specific validators for enforcing docstring
contracts across the repository.

Modules:
    - common: Shared utilities and ValidationError class
    - bash_validator: Bash script validation
    - powershell_validator: PowerShell script validation
    - python_validator: Python module validation
    - perl_validator: Perl script validation
    - rust_validator: Rust module validation
    - yaml_validator: YAML file validation
"""

from .common import ValidationError, check_pragma_ignore, validate_exit_codes_content

__all__ = [
    "ValidationError",
    "check_pragma_ignore",
    "validate_exit_codes_content",
]
