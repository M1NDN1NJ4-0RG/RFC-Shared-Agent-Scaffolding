"""Strict YAML configuration validator for repo_lint rules.

:Purpose:
    Validates repo_lint configuration YAML files with strict schema enforcement.
    Ensures YAML document markers, required fields, and structure compliance.

:Functions:
    - validate_config_file: Validate a YAML config file against its schema
    - load_validated_config: Load and validate a config file
    - ConfigValidationError: Exception raised on validation failures

:Environment Variables:
    None

:Examples:
    Validate a naming rules file::

        from tools.repo_lint.config_validator import load_validated_config
        config = load_validated_config('conformance/repo-lint/repo-lint-naming-rules.yaml')

:Exit Codes:
    Functions raise ConfigValidationError on validation failure:
    - Caller should exit with ExitCode.INTERNAL_ERROR (3)
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class ConfigValidationError(Exception):
    """Exception raised when config validation fails.

    :Purpose:
        Provides detailed error information for config validation failures
        with file path, line context, and actionable error messages.
    """

    def __init__(self, file_path: str, message: str, line: Optional[int] = None):
        """Initialize config validation error.

        :param file_path: Path to the config file that failed validation
        :param message: Detailed error message
        :param line: Optional line number where error occurred
        """
        self.file_path = file_path
        self.message = message
        self.line = line
        location = f" (line {line})" if line else ""
        super().__init__(f"{file_path}{location}: {message}")


def _validate_yaml_structure(file_path: Path, content: str) -> None:
    """Validate YAML document structure (markers, single-document).

    :Purpose:
        Ensures YAML file has required document markers (---/...) and is
        a single-document file (not multi-document).

    :param file_path: Path to config file
    :param content: Raw YAML file content
    :raises ConfigValidationError: If structure validation fails
    """
    lines = content.splitlines()

    # Check for document start marker (---)
    if not lines or not lines[0].strip() == "---":
        raise ConfigValidationError(
            str(file_path),
            "Missing required YAML document start marker '---' at beginning of file. "
            "All repo-lint config files must start with '---'.",
            line=1,
        )

    # Check for document end marker (...)
    if not lines or not lines[-1].strip() == "...":
        raise ConfigValidationError(
            str(file_path),
            "Missing required YAML document end marker '...' at end of file. "
            "All repo-lint config files must end with '...'.",
            line=len(lines),
        )

    # Check for multiple documents (multiple --- markers)
    doc_start_count = sum(1 for line in lines if line.strip() == "---")
    if doc_start_count > 1:
        raise ConfigValidationError(
            str(file_path),
            f"Multiple YAML documents detected ({doc_start_count} '---' markers found). "
            "Config files must be single-document only.",
        )


def _validate_required_fields(file_path: Path, data: Dict[str, Any], config_type: str) -> None:
    """Validate required top-level fields in config.

    :Purpose:
        Ensures config_type and version fields are present and valid.

    :param file_path: Path to config file
    :param data: Parsed YAML data
    :param config_type: Expected config_type value
    :raises ConfigValidationError: If required fields are missing or invalid
    """
    # Check config_type field
    if "config_type" not in data:
        raise ConfigValidationError(
            str(file_path), "Missing required field 'config_type'. This field identifies the configuration type."
        )

    actual_type = data["config_type"]
    if actual_type != config_type:
        raise ConfigValidationError(
            str(file_path),
            f"Invalid config_type: expected '{config_type}', got '{actual_type}'. "
            f"This file should be type '{config_type}'.",
        )

    # Check version field
    if "version" not in data:
        raise ConfigValidationError(
            str(file_path), "Missing required field 'version'. Version must be specified (e.g., '1.0.0')."
        )

    version = data["version"]
    if not isinstance(version, str):
        raise ConfigValidationError(
            str(file_path), f"Invalid version type: expected string, got {type(version).__name__}. Use '1.0.0' format."
        )

    # Validate semantic version format
    if not re.match(r"^\d+\.\d+\.\d+$", version):
        raise ConfigValidationError(
            str(file_path),
            f"Invalid version format: '{version}'. Version must follow semantic versioning (e.g., '1.0.0').",
        )


def _validate_languages_section(file_path: Path, data: Dict[str, Any]) -> None:
    """Validate languages section structure.

    :Purpose:
        Ensures languages field is present and is a valid mapping.

    :param file_path: Path to config file
    :param data: Parsed YAML data
    :raises ConfigValidationError: If languages section is invalid
    """
    if "languages" not in data:
        raise ConfigValidationError(
            str(file_path),
            "Missing required field 'languages'. Config must include a 'languages:' mapping with per-language rules.",
        )

    languages = data["languages"]
    if not isinstance(languages, dict):
        raise ConfigValidationError(
            str(file_path),
            f"Invalid 'languages' type: expected mapping/dict, got {type(languages).__name__}. "
            "Use 'languages:' with language keys (python, bash, etc.).",
        )

    if not languages:
        raise ConfigValidationError(
            str(file_path),
            "Empty 'languages' section. At least one language must be configured.",
        )


def _check_unknown_keys(file_path: Path, data: Dict[str, Any], allowed_keys: List[str]) -> None:
    """Check for unknown top-level keys.

    :Purpose:
        Rejects unknown keys to catch typos and ensure strict schema compliance.

    :param file_path: Path to config file
    :param data: Parsed YAML data
    :param allowed_keys: List of allowed top-level keys
    :raises ConfigValidationError: If unknown keys are found
    """
    unknown_keys = set(data.keys()) - set(allowed_keys)
    if unknown_keys:
        unknown_list = ", ".join(f"'{k}'" for k in sorted(unknown_keys))
        allowed_list = ", ".join(f"'{k}'" for k in allowed_keys)
        raise ConfigValidationError(
            str(file_path),
            f"Unknown top-level keys: {unknown_list}. "
            f"Allowed keys are: {allowed_list}. "
            "Check for typos or extra fields.",
        )


def validate_config_file(file_path: Path, config_type: str, allowed_keys: Optional[List[str]] = None) -> Dict[str, Any]:
    """Validate a repo_lint YAML configuration file.

    :Purpose:
        Performs strict validation of YAML config files:
        - Checks YAML document markers (--- and ...)
        - Validates single-document structure
        - Validates required fields (config_type, version)
        - Rejects unknown top-level keys
        - Validates languages section structure

    :param file_path: Path to config file
    :param config_type: Expected config_type value (e.g., 'repo-lint-naming-rules')
    :param allowed_keys: Optional list of allowed top-level keys
                        Default: ['config_type', 'version', 'languages', 'exclusions']
    :returns: Parsed and validated config data
    :raises ConfigValidationError: If validation fails (with detailed error message)
    :raises FileNotFoundError: If config file does not exist
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Config file not found: {file_path}")

    # Read raw content for structure validation
    content = file_path.read_text()

    # Validate YAML structure (document markers, single-document)
    _validate_yaml_structure(file_path, content)

    # Parse YAML
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as e:
        raise ConfigValidationError(str(file_path), f"YAML parsing error: {e}") from e

    if not isinstance(data, dict):
        raise ConfigValidationError(str(file_path), f"Config must be a YAML mapping/dict, got {type(data).__name__}")

    # Validate required fields
    _validate_required_fields(file_path, data, config_type)

    # Validate languages section
    _validate_languages_section(file_path, data)

    # Check for unknown keys
    if allowed_keys is None:
        allowed_keys = ["config_type", "version", "languages", "exclusions", "validation", "settings", "description"]

    _check_unknown_keys(file_path, data, allowed_keys)

    return data


def load_validated_config(file_path: str, config_type: str) -> Dict[str, Any]:
    """Load and validate a config file.

    :Purpose:
        Convenience function to load and validate a config file in one step.

    :param file_path: Path to config file (string or Path)
    :param config_type: Expected config_type value
    :returns: Parsed and validated config data
    :raises ConfigValidationError: If validation fails
    :raises FileNotFoundError: If config file does not exist
    """
    path = Path(file_path)
    return validate_config_file(path, config_type)
