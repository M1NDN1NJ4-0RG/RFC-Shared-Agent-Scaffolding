"""Base runner interface and utilities for language-specific linters.

:Purpose:
    Defines the standard Runner protocol that all language-specific runners
    must implement, ensuring consistent behavior across all languages.

:Protocol:
    - check(): Run linting/formatting checks without modifying files
    - fix(): Apply automatic fixes where possible (formatters only)
    - has_files(): Check if language has relevant files in repository
    - check_tools(): Verify required tools are installed

:Environment Variables:
    None

:Examples:
    Implement a custom runner::

        from tools.repo_lint.runners.base import Runner

        class MyRunner(Runner):
            def check(self):
                # Implementation
                pass

:Exit Codes:
    Runners don't exit directly but return LintResult objects:
    - 0: Implied success (when LintResult.passed = True)
    - 1: Implied violations (when LintResult.passed = False)
"""

import shutil
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from tools.repo_lint.common import LintResult, MissingToolError

# Paths to exclude from linting/docstring validation
# These are test fixtures that are intentionally non-conformant
EXCLUDED_PATHS = [
    "conformance/repo-lint/unsafe-fix-fixtures/",
]


def find_repo_root() -> Path:
    """Find the repository root directory.

    Falls back to current working directory if .git is not found,
    allowing repo_lint to work in non-Git directories.

    :returns: Path to repository root (or cwd if .git not found)

    :Note:
        This is a compatibility wrapper around the shared repo_utils.find_repo_root().
        New code should import directly from tools.repo_lint.repo_utils.
    """
    from tools.repo_lint.repo_utils import find_repo_root as _find_repo_root

    return _find_repo_root()


def command_exists(command: str) -> bool:
    """Check if a command exists in PATH (cross-platform).

    :param command: Command name to check
    :returns: True if command exists, False otherwise
    """
    return shutil.which(command) is not None


def get_git_pathspec_excludes() -> List[str]:
    """Get git pathspec exclude patterns for linting.

    :returns: List of exclude patterns for git ls-files
    """
    excludes = []
    for path in EXCLUDED_PATHS:
        # Git pathspec format: ':(exclude)pattern'
        excludes.append(f":(exclude){path}")
    return excludes


def get_tracked_files(patterns: List[str], repo_root: Optional[Path] = None) -> List[str]:
    """Get tracked files matching patterns, excluding lint test fixtures.

    :param patterns: List of file patterns (e.g., ["**/*.py", "**/*.sh"])
    :param repo_root: Repository root path (auto-detected if None)
    :returns: List of file paths (empty list if none found)
    """
    if repo_root is None:
        repo_root = find_repo_root()

    excludes = get_git_pathspec_excludes()
    result = subprocess.run(
        ["git", "ls-files"] + patterns + excludes,
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )

    if not result.stdout.strip():
        return []

    return result.stdout.strip().split("\n")


class Runner(ABC):
    """Base class for language-specific linting runners.

    :Purpose:
        Provides common functionality and defines the interface that all
        language runners must implement.
    """

    def __init__(self, repo_root: Optional[Path] = None, ci_mode: bool = False, verbose: bool = False):
        """Initialize runner.

        :param repo_root: Path to repository root (auto-detected if None)
        :param ci_mode: Whether running in CI mode (fail if tools missing)
        :param verbose: Whether to show verbose output
        """
        self.repo_root = repo_root or find_repo_root()
        self.ci_mode = ci_mode
        self.verbose = verbose

    @abstractmethod
    def has_files(self) -> bool:
        """Check if language has relevant files in repository.

        :Returns:
            True if language has files to lint, False otherwise
        """
        pass  # pylint: disable=unnecessary-pass  # Abstract method

    @abstractmethod
    def check_tools(self) -> List[str]:
        """Check which required tools are missing.

        :Returns:
            List of missing tool names (empty if all tools present)
        """
        pass  # pylint: disable=unnecessary-pass  # Abstract method

    @abstractmethod
    def check(self) -> List[LintResult]:
        """Run linting checks without modifying files.

        :Returns:
            List of linting results from all tools

        :Raises:
            MissingToolError: If required tools are not installed (CI mode only)
        """
        pass  # pylint: disable=unnecessary-pass  # Abstract method

    @abstractmethod
    def fix(self, policy: Optional[dict] = None) -> List[LintResult]:
        """Apply automatic fixes where possible (formatters only).

        :param policy: Auto-fix policy dictionary (deny-by-default)
        :returns: List of linting results after fixes applied
        :raises MissingToolError: If required tools are not installed (CI mode only)
        """
        pass  # pylint: disable=unnecessary-pass  # Abstract method

    def _ensure_tools(self, required_tools: List[str]) -> None:
        """Ensure required tools are installed.

        :param required_tools: List of required tool names
        :raises MissingToolError: If any required tools are missing and CI mode is enabled
        """
        missing = [tool for tool in required_tools if not command_exists(tool)]
        if missing and self.ci_mode:
            raise MissingToolError(missing[0], f"Install {', '.join(missing)} to continue")
