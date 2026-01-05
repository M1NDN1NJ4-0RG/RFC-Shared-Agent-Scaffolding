"""Shared repository utility functions for repo_lint.

:Purpose:
    Provides common utility functions used across repo_lint modules to avoid
    code duplication and ensure consistent behavior.

:Functions:
    - find_repo_root: Find repository root directory (or cwd as fallback)

:Environment Variables:
    None

:Exit Codes:
    This module does not define or use exit codes (utility functions only):
    - 0: Not applicable (see tools.repo_lint.common.ExitCode)
    - 1: Not applicable (see tools.repo_lint.common.ExitCode)

:Examples:
    Find repository root::

        from tools.repo_lint.repo_utils import find_repo_root
        repo_root = find_repo_root()
"""

from __future__ import annotations

from pathlib import Path


def find_repo_root() -> Path:
    """Find the repository root directory.

    Walks up the directory tree from the current working directory looking for
    a .git directory. Falls back to current working directory if .git is not found,
    allowing repo_lint to work in non-Git directories.

    :returns: Path to repository root (or cwd if .git not found)
    """
    current = Path.cwd().resolve()
    start_dir = current

    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent

    # Fallback: return starting directory if .git not found
    return start_dir
