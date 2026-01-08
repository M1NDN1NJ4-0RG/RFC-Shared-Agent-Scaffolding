"""Main validator interface for docstring validation.

:Purpose:
    Provides unified interface for validating docstrings across all supported
    languages. This module serves as the main entry point for internal
    docstring validation within repo_lint.

:Environment Variables:
    None

:Examples:
    Validate all Python files::

        from tools.repo_lint.docstrings.validator import validate_files
        from pathlib import Path

        files = [Path("tools/example.py")]
        errors = validate_files(files, language="python")

    Validate specific file::

        from tools.repo_lint.docstrings.validator import validate_file
        errors = validate_file(Path("script.sh"))

:Exit Codes:
    N/A - This is a library module, not an executable script
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Union

from tools.repo_lint.docstrings.bash_validator import BashValidator
from tools.repo_lint.docstrings.common import ValidationError
from tools.repo_lint.docstrings.perl_validator import PerlValidator
from tools.repo_lint.docstrings.powershell_validator import PowerShellValidator
from tools.repo_lint.docstrings.python_validator import PythonValidator
from tools.repo_lint.docstrings.rust_validator import RustValidator
from tools.repo_lint.docstrings.yaml_validator import YAMLValidator


def validate_file(file_path: Path) -> List[ValidationError]:
    """Validate a single file based on its extension.

    :param file_path: Path to file to validate

    :returns: List of validation errors (empty if file passes)
    """
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        return [ValidationError(str(file_path), ["read error"], str(e))]

    # Dispatch to appropriate validator
    suffix = file_path.suffix.lower()

    if suffix in [".sh", ".bash", ".zsh"]:
        return BashValidator.validate(file_path, content)
    elif suffix == ".ps1":
        return PowerShellValidator.validate(file_path, content)
    elif suffix == ".py":
        return PythonValidator.validate(file_path, content)
    elif suffix in [".pl", ".pm"]:
        return PerlValidator.validate(file_path, content)
    elif suffix == ".rs":
        return RustValidator.validate(file_path, content)
    elif suffix in [".yml", ".yaml"]:
        return YAMLValidator.validate(file_path, content)
    else:
        # Unknown extension, skip
        return []


def validate_files(files: List[Path | str], language: str = "all") -> List[ValidationError]:
    """Validate multiple files, optionally filtering by language.

    :param files: List of file paths to validate (Path objects or strings)
    :param language: Language to filter by (python, bash, perl, powershell, yaml, rust, all)

    :returns: List of all validation errors across all files
    """
    errors: List[ValidationError] = []

    for file_path in files:
        # Convert to Path if it's a string
        if isinstance(file_path, str):
            file_path = Path(file_path)

        # Apply language filter if specified
        if language != "all":
            file_lang = _get_language_from_extension(file_path)
            if file_lang != language:
                continue

        file_errors = validate_file(file_path)
        errors.extend(file_errors)

    return errors


def _get_language_from_extension(file_path: Path) -> str:
    """Determine language from file extension.

    :param file_path: Path to file

    :returns: Language name (python, bash, perl, powershell, yaml, rust) or empty string if unknown
    """
    suffix = file_path.suffix.lower()

    if suffix in [".sh", ".bash", ".zsh"]:
        return "bash"
    elif suffix == ".ps1":
        return "powershell"
    elif suffix == ".py":
        return "python"
    elif suffix in [".pl", ".pm"]:
        return "perl"
    elif suffix == ".rs":
        return "rust"
    elif suffix in [".yml", ".yaml"]:
        return "yaml"
    else:
        return ""
