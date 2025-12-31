"""YAML configuration loader for repo_lint.

:Purpose:
    Centralized YAML configuration loading with caching and validation.
    Implements YAML-first contracts per Phase 2.9 requirements.

:Architecture:
    - Single source of truth: conformance/repo-lint/*.yaml files
    - Cached loading for performance
    - Validation via config_validator
    - Backward compatibility support

:Environment Variables:
    None

:Examples:
    Load linting rules::

        from tools.repo_lint.yaml_loader import load_linting_rules
        rules = load_linting_rules()
        black_version = rules['languages']['python']['tools']['black']['version']

    Load file patterns::

        from tools.repo_lint.yaml_loader import load_file_patterns
        patterns = load_file_patterns()
        in_scope = patterns['in_scope']['patterns']

:Exit Codes:
    - 0: Success
    - 1: YAML file not found or invalid

:Notes:
    - Configurations are cached per process (singleton pattern)
    - File paths are relative to repository root
    - All YAML files must pass config_validator checks
"""

import warnings
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

import yaml

from tools.repo_lint.config_validator import validate_config_file
from tools.repo_lint.repo_utils import find_repo_root


@lru_cache(maxsize=None)
def _get_conformance_dir() -> Path:
    """Get the conformance/repo-lint directory.

    :returns: Path to conformance/repo-lint directory

    :raises FileNotFoundError: If conformance directory doesn't exist
    """
    repo_root = find_repo_root()
    conformance_dir = repo_root / "conformance" / "repo-lint"
    if not conformance_dir.exists():
        raise FileNotFoundError(f"Conformance directory not found: {conformance_dir}")
    return conformance_dir


def load_yaml_config(config_filename: str, allowed_keys: List[str] = None) -> Dict[str, Any]:
    """Load and validate a YAML configuration file.

    :param config_filename: Filename of the YAML config (e.g., 'repo-lint-linting-rules.yaml')
    :param allowed_keys: Optional list of allowed top-level keys for validation
    :returns: Parsed YAML configuration as dictionary

    :raises FileNotFoundError: If config file doesn't exist
    :raises yaml.YAMLError: If YAML is invalid
    :raises ConfigValidationError: If config doesn't pass validation

    :Examples:
        Load linting rules::

            config = load_yaml_config('repo-lint-linting-rules.yaml')
            python_tools = config['languages']['python']['tools']

    :Note:
        This function is not cached to support custom allowed_keys.
        Use the specific load_*_rules() functions for caching.
    """
    conformance_dir = _get_conformance_dir()
    config_path = conformance_dir / config_filename

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    # Load YAML first to get config_type
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Validate config file structure
    config_type = config.get("config_type", "unknown")
    validate_config_file(config_path, config_type, allowed_keys=allowed_keys)

    return config


@lru_cache(maxsize=None)
def load_linting_rules() -> Dict[str, Any]:
    """Load linting rules configuration.

    :returns: Linting rules configuration dictionary

    :Examples:
        Get Python tool versions::

            rules = load_linting_rules()
            black_version = rules['languages']['python']['tools']['black']['version']
    """
    return load_yaml_config("repo-lint-linting-rules.yaml")


@lru_cache(maxsize=None)
def load_naming_rules() -> Dict[str, Any]:
    """Load naming rules configuration.

    :returns: Naming rules configuration dictionary

    :Examples:
        Get Python naming patterns::

            rules = load_naming_rules()
            patterns = rules['languages']['python']['file_patterns']
    """
    return load_yaml_config("repo-lint-naming-rules.yaml")


@lru_cache(maxsize=None)
def load_docstring_rules() -> Dict[str, Any]:
    """Load docstring rules configuration.

    :returns: Docstring rules configuration dictionary

    :Examples:
        Get Python docstring requirements::

            rules = load_docstring_rules()
            validation = rules['languages']['python']['validation']
    """
    return load_yaml_config("repo-lint-docstring-rules.yaml")


@lru_cache(maxsize=None)
def load_file_patterns() -> Dict[str, Any]:
    """Load file patterns configuration.

    :returns: File patterns configuration dictionary

    :Examples:
        Get in-scope patterns::

            patterns = load_file_patterns()
            in_scope = patterns['in_scope']['patterns']
            exclusions = []
            for category in patterns['exclusions'].values():
                exclusions.extend(category['patterns'])
    """
    # File patterns config has custom allowed keys
    allowed_keys = [
        "config_type",
        "version",
        "description",
        "languages",  # Required by validator
        "in_scope",
        "exclusions",
        "linting_exclusions",
        "metadata",
    ]
    return load_yaml_config("repo-lint-file-patterns.yaml", allowed_keys=allowed_keys)


def get_tool_versions() -> Dict[str, str]:
    """Get all tool versions from linting rules YAML.

    This is the YAML-first replacement for version_pins.py constants.

    :returns: Dictionary mapping tool name to version string

    :Examples:
        Get all versions::

            versions = get_tool_versions()
            print(f"Black version: {versions['black']}")

    :Note:
        This function replaces the old PYTHON_TOOLS, BASH_TOOLS, etc.
        constants from version_pins.py (Phase 2.9 migration).
    """
    rules = load_linting_rules()
    versions = {}

    for lang_config in rules.get("languages", {}).values():
        if not lang_config.get("enabled", True):
            continue

        tools = lang_config.get("tools", {})
        for tool_name, tool_config in tools.items():
            version = tool_config.get("version")
            if version:  # Skip tools with null/None version
                versions[tool_name] = version

    return versions


def get_in_scope_patterns() -> List[str]:
    """Get file patterns that are in scope for validation.

    :returns: List of file patterns (e.g., ["**/*.py", "**/*.sh"])

    :Note:
        This function replaces IN_SCOPE_PATTERNS from validate_docstrings.py
        (Phase 2.9 migration).
    """
    patterns_config = load_file_patterns()
    return patterns_config.get("in_scope", {}).get("patterns", [])


def get_exclusion_patterns() -> List[str]:
    """Get all exclusion patterns from file patterns config.

    :returns: Flattened list of all exclusion patterns

    :Note:
        This function replaces EXCLUDE_PATTERNS from validate_docstrings.py
        (Phase 2.9 migration).
    """
    patterns_config = load_file_patterns()
    exclusions_config = patterns_config.get("exclusions", {})

    all_patterns = []
    for category in exclusions_config.values():
        if isinstance(category, dict) and "patterns" in category:
            all_patterns.extend(category["patterns"])

    return all_patterns


def get_linting_exclusion_paths() -> List[str]:
    """Get paths excluded from linting checks (for base.py EXCLUDED_PATHS).

    :returns: List of paths to exclude from linting

    :Note:
        This function replaces EXCLUDED_PATHS from base.py (Phase 2.9 migration).
    """
    patterns_config = load_file_patterns()
    return patterns_config.get("linting_exclusions", {}).get("patterns", [])


# Backward compatibility layer with deprecation warnings
def _get_legacy_python_tools() -> Dict[str, str]:
    """Deprecated: Get Python tool versions (backward compatibility).

    :returns: Dictionary of Python tool versions

    :raises DeprecationWarning: This function is deprecated
    """
    warnings.warn(
        "Direct import of PYTHON_TOOLS is deprecated. Use tools.repo_lint.yaml_loader.get_tool_versions() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return get_tool_versions()


# Export for backward compatibility (with deprecation)
PYTHON_TOOLS = property(lambda self: _get_legacy_python_tools())
