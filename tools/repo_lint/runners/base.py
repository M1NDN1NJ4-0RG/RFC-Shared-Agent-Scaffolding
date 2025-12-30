"""Base runner interface and utilities for language-specific linters.

:Purpose:
    Defines the standard Runner protocol that all language-specific runners
    must implement, ensuring consistent behavior across all languages.

:Protocol:
    - check(): Run linting/formatting checks without modifying files
    - fix(): Apply automatic fixes where possible (formatters only)
    - has_files(): Check if language has relevant files in repository
    - check_tools(): Verify required tools are installed
"""

import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from tools.repo_lint.common import LintResult, MissingToolError


def find_repo_root() -> Path:
    """Find the repository root directory.

    :Returns:
        Path to repository root

    :Raises:
        RuntimeError: If repository root cannot be found
    """
    current = Path.cwd().resolve()
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    raise RuntimeError("Could not find repository root (no .git directory)")


def command_exists(command: str) -> bool:
    """Check if a command exists in PATH (cross-platform).

    :Args:
        command: Command name to check

    :Returns:
        True if command exists, False otherwise
    """
    return shutil.which(command) is not None


class Runner(ABC):
    """Base class for language-specific linting runners.

    :Purpose:
        Provides common functionality and defines the interface that all
        language runners must implement.
    """

    def __init__(self, repo_root: Optional[Path] = None, ci_mode: bool = False, verbose: bool = False):
        """Initialize runner.

        :Args:
            repo_root: Path to repository root (auto-detected if None)
            ci_mode: Whether running in CI mode (fail if tools missing)
            verbose: Whether to show verbose output
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

        :Args:
            policy: Auto-fix policy dictionary (deny-by-default)

        :Returns:
            List of linting results after fixes applied

        :Raises:
            MissingToolError: If required tools are not installed (CI mode only)
        """
        pass  # pylint: disable=unnecessary-pass  # Abstract method

    def _ensure_tools(self, required_tools: List[str]) -> None:
        """Ensure required tools are installed.

        :Args:
            required_tools: List of required tool names

        :Raises:
            MissingToolError: If any required tools are missing and CI mode is enabled
        """
        missing = [tool for tool in required_tools if not command_exists(tool)]
        if missing and self.ci_mode:
            raise MissingToolError(missing[0], f"Install {', '.join(missing)} to continue")
