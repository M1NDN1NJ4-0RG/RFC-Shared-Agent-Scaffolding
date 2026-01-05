"""Version pins for deterministic tool installations.

:Purpose:
    Centralize version pinning for all linting tools to ensure deterministic
    installations across environments.

:Version Sources (Phase 2.9 YAML-First Migration):
    - PRIMARY SOURCE: conformance/repo-lint/repo-lint-linting-rules.yaml
    - DERIVED: This module loads from YAML (single source of truth)
    - SYNC: pyproject.toml must be manually synced with YAML versions

:Migration Notes (Phase 2.9):
    - Hardcoded constants (PYTHON_TOOLS, BASH_TOOLS, etc.) are DEPRECATED
    - All code should use get_all_versions() which loads from YAML
    - Direct constant access will trigger deprecation warnings
    - Backward compatibility maintained during transition period

:Environment Variables:
    None

:Examples:
    Get all tool versions (RECOMMENDED)::

        from tools.repo_lint.install.version_pins import get_all_versions
        versions = get_all_versions()
        print(f"Black version: {versions['black']}")

:Exit Codes:
    - 0: Success (when used in scripts)
    - 1: Error (when used in scripts)
"""

from __future__ import annotations

import warnings

from tools.repo_lint.yaml_loader import get_tool_versions

# Pip version for venv creation (pinned for deterministic installs)
# NOTE: This remains hardcoded as it's not a linting tool
PIP_VERSION = "25.3"


# DEPRECATED: Direct constant access (Phase 2.9)
# These will be removed in a future version. Use get_all_versions() instead.
def __getattr__(name):
    """Provide backward compatibility with deprecation warnings.

    :param name: Attribute name being accessed
    :returns: Attribute value from YAML config

    :raises AttributeError: If attribute doesn't exist
    :raises DeprecationWarning: For deprecated constant access
    """
    deprecated_constants = ["PYTHON_TOOLS", "BASH_TOOLS", "POWERSHELL_TOOLS", "PERL_TOOLS"]

    if name in deprecated_constants:
        warnings.warn(
            f"{name} is deprecated. Use get_all_versions() or tools.repo_lint.yaml_loader.get_tool_versions() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        # Return appropriate subset for backward compatibility
        all_versions = get_tool_versions()
        if name == "PYTHON_TOOLS":
            return {k: v for k, v in all_versions.items() if k in ["black", "ruff", "pylint", "yamllint"]}
        elif name == "BASH_TOOLS":
            return {k: v for k, v in all_versions.items() if k in ["shellcheck", "shfmt"]}
        elif name == "POWERSHELL_TOOLS":
            return {k: v for k, v in all_versions.items() if k == "PSScriptAnalyzer"}
        elif name == "PERL_TOOLS":
            return {k: v for k, v in all_versions.items() if k == "Perl::Critic"}

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def get_all_versions():
    """Get all tool versions from YAML configuration (YAML-first).

    :returns: Dictionary mapping tool name to version string (or None if not pinned)

    :Note:
        This is the primary interface for accessing tool versions.
        Versions are loaded from conformance/repo-lint/repo-lint-linting-rules.yaml
    """
    return get_tool_versions()
