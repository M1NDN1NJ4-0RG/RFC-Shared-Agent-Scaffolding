"""Configuration handling for PEP 526 type annotation checking.

:Purpose:
    Provides configuration loading and validation for the PEP 526 checker.
    Reads configuration from pyproject.toml and provides defaults.

:Configuration Schema:
    [tool.repo_lint.python.type_annotations]
    module_level = true          # MANDATORY baseline
    class_attributes = true      # MANDATORY baseline
    local_variables = false      # OPTIONAL (future: --strict-typing)
    instance_attributes = false  # OPTIONAL (future)

    require_empty_literal_annotations = true
    require_none_annotations = true

    per_file_ignores = [
        "tests/*.py:PEP526",
        "scripts/legacy/*.py:PEP526"
    ]

:Examples:
    Load default configuration::

        config = get_default_config()

    Load from pyproject.toml::

        config = load_config_from_toml('pyproject.toml')
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # type: ignore[import-not-found]
    except ImportError:
        tomllib = None  # type: ignore[assignment]  # typing: Any (TODO: tighten)


def get_default_config() -> Dict[str, Any]:
    """Get default PEP 526 checker configuration.

    :returns: Default configuration dictionary
    :rtype: dict

    :Default Values:
        - module_level: True (MANDATORY baseline)
        - class_attributes: True (MANDATORY baseline)
        - local_variables: False (OPTIONAL, future)
        - instance_attributes: False (OPTIONAL, future)
        - require_empty_literal_annotations: True
        - require_none_annotations: True
    """
    return {
        "module_level": True,
        "class_attributes": True,
        "local_variables": False,
        "instance_attributes": False,
        "require_empty_literal_annotations": True,
        "require_none_annotations": True,
        "per_file_ignores": [],
    }


def load_config_from_toml(toml_path: str | Path) -> Dict[str, Any]:
    """Load PEP 526 configuration from pyproject.toml.

    :param toml_path: Path to pyproject.toml file
    :returns: Configuration dictionary with defaults applied
    :rtype: dict

    :raises:
        FileNotFoundError: If toml_path does not exist
        ValueError: If TOML parsing fails

    :Note:
        If the configuration section is missing, returns default config.
        If tomllib is not available, returns default config with warning.
    """
    if tomllib is None:
        # TOML library not available, return defaults
        return get_default_config()

    toml_path = Path(toml_path)
    if not toml_path.exists():
        raise FileNotFoundError(f"TOML file not found: {toml_path}")

    try:
        with open(toml_path, "rb") as f:
            data = tomllib.load(f)
    except Exception as e:
        raise ValueError(f"Failed to parse TOML file {toml_path}: {e}") from e

    # Extract configuration from [tool.repo_lint.python.type_annotations]
    config = get_default_config()
    tool_config = data.get("tool", {})
    repo_lint_config = tool_config.get("repo_lint", {})
    python_config = repo_lint_config.get("python", {})
    type_annotations_config = python_config.get("type_annotations", {})

    # Merge with defaults
    config.update(type_annotations_config)

    # Validate merged configuration to ensure only valid keys and values are present
    validation_errors = validate_config(config)
    if validation_errors:
        joined_errors = "; ".join(validation_errors)
        raise ValueError(
            f"Invalid PEP 526 configuration in {toml_path}: {joined_errors}"
        )
    return config


def should_ignore_file(filepath: str, rule: str, config: Dict[str, Any]) -> bool:
    """Check if a file should be ignored for a specific rule.

    :param filepath: Path to file being checked
    :param rule: Rule ID (e.g., 'PEP526', 'PEP526-module')
    :param config: Configuration dictionary
    :returns: True if file should be ignored for this rule
    :rtype: bool

    :Per-File Ignore Format:
        "path/pattern:RULE" - Ignore RULE for files matching pattern
        Supports glob patterns via pathlib.Path.match()

    :Examples:
        per_file_ignores = [
            "tests/*.py:PEP526",           # Ignore all PEP526 rules in tests
            "scripts/legacy.py:PEP526-module"  # Ignore module-level only
        ]
    """
    ignores = config.get("per_file_ignores", [])
    filepath_obj = Path(filepath)

    for ignore_pattern in ignores:
        if ":" not in ignore_pattern:
            continue  # Invalid pattern, skip

        pattern, ignore_rule = ignore_pattern.rsplit(":", 1)

        # Check if file matches pattern
        if filepath_obj.match(pattern):
            # Check if rule matches (exact match or prefix match)
            if ignore_rule == rule or rule.startswith(ignore_rule):
                return True

    return False


def validate_config(config: Dict[str, Any]) -> List[str]:
    """Validate PEP 526 configuration.

    :param config: Configuration dictionary to validate
    :returns: List of validation error messages (empty if valid)
    :rtype: list[str]

    :Validation Rules:
        - Scope flags must be boolean
        - per_file_ignores must be list of strings
        - per_file_ignore patterns must have ':' separator
    """
    errors: List[str] = []

    # Validate boolean flags
    bool_keys = [
        "module_level",
        "class_attributes",
        "local_variables",
        "instance_attributes",
        "require_empty_literal_annotations",
        "require_none_annotations",
    ]
    for key in bool_keys:
        if key in config and not isinstance(config[key], bool):
            errors.append(f"Config key '{key}' must be boolean, got {type(config[key]).__name__}")

    # Validate per_file_ignores
    if "per_file_ignores" in config:
        ignores = config["per_file_ignores"]
        if not isinstance(ignores, list):
            errors.append(f"Config key 'per_file_ignores' must be list, got {type(ignores).__name__}")
        else:
            for i, pattern in enumerate(ignores):
                if not isinstance(pattern, str):
                    errors.append(f"per_file_ignores[{i}] must be string, got {type(pattern).__name__}")
                elif ":" not in pattern:
                    errors.append(f"per_file_ignores[{i}] missing ':' separator: {pattern}")

    return errors
