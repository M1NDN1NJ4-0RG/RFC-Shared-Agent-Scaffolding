"""Version pins for deterministic tool installations.

:Purpose:
    Centralize version pinning for all linting tools to ensure deterministic
    installations across environments. Versions are kept in sync with
    pyproject.toml where applicable.

:Version Sources:
    - Python tools: Synced with [project.optional-dependencies.lint] in pyproject.toml
    - Non-Python tools: Manually maintained based on stable releases

:Usage:
    Import version constants when implementing tool installation logic.
"""

# Python-based tools (must match pyproject.toml [project.optional-dependencies.lint])
PYTHON_TOOLS = {
    "black": "24.10.0",
    "ruff": "0.8.4",
    "pylint": "3.3.2",
    "yamllint": "1.35.1",
}

# Bash tools
# Note: shellcheck typically installed via system package manager (apt/brew)
# shfmt installed via go install (version pinned in install command)
BASH_TOOLS = {
    "shellcheck": None,  # System package manager (version varies)
    "shfmt": "v3.12.0",  # Go install version
}

# PowerShell tools
# Note: PSScriptAnalyzer installed via PowerShell Gallery
POWERSHELL_TOOLS = {
    "PSScriptAnalyzer": "1.23.0",
}

# Perl tools
# Note: Perl::Critic installed via CPAN
PERL_TOOLS = {
    "Perl::Critic": None,  # CPAN (version varies)
}


def get_all_versions():
    """Get all tool versions as a flat dictionary.

    :Returns:
        Dictionary mapping tool name to version string (or None if not pinned)
    """
    all_versions = {}
    all_versions.update(PYTHON_TOOLS)
    all_versions.update(BASH_TOOLS)
    all_versions.update(POWERSHELL_TOOLS)
    all_versions.update(PERL_TOOLS)
    return all_versions
