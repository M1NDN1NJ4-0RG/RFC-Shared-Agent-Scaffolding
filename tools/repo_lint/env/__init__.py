"""Environment and PATH management utilities for repo-lint.

This module provides utilities for managing virtual environments and PATH
configuration to help users run repo-lint from their shells.

:Purpose:
    Provide environment and venv management tools for repo-lint users.
    Includes virtual environment detection, PATH configuration helpers,
    and shell integration utilities.

:Modules:
    venv_resolver: Virtual environment detection and resolution

:Environment Variables:
    None. This package does not read environment variables directly.

:Examples:
    >>> from tools.repo_lint.env.venv_resolver import resolve_venv
    >>> venv = resolve_venv()

:Exit Codes:
    This is a utility module and does not define exit codes. Exit codes are
    determined by the calling commands (which, env, activate). See those
    commands' documentation for their specific exit codes.

    - 0: Not applicable (utility module)
    - 1: Not applicable (utility module)
"""

from __future__ import annotations
