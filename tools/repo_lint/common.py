"""Common types, errors, and utilities for repo_lint.

:Purpose:
    Provides shared data structures and utilities used across all runner modules
    to ensure consistent behavior and reporting.

:Types:
    - Violation: Represents a single linting violation
    - LintResult: Result from running a linter/formatter
    - ExitCode: Standard exit codes used throughout the tool

:Errors:
    - RepoLintError: Base exception for all repo_lint errors
    - MissingToolError: Raised when required tools are not installed
    - RunnerError: Raised when a runner encounters an error

:Environment Variables:
    None

:Examples:
    Create a violation::

        from tools.repo_lint.common import Violation
        v = Violation(tool="ruff", file="test.py", line=10, message="Line too long")

:Exit Codes:
    This module defines exit codes (see ExitCode class) but doesn't exit:
    - 0: SUCCESS - All checks passed
    - 1: VIOLATIONS - Linting/formatting violations found
    - 2: MISSING_TOOLS - Required tools not installed (CI mode)
    - 3: INTERNAL_ERROR - Internal error or exception
"""

from dataclasses import dataclass
from enum import IntEnum
from typing import List, Optional


class ExitCode(IntEnum):
    """Standard exit codes for repo_lint."""

    SUCCESS = 0  # All checks passed
    VIOLATIONS = 1  # Linting/formatting violations found
    MISSING_TOOLS = 2  # Required tools not installed (CI mode)
    INTERNAL_ERROR = 3  # Internal error or exception


@dataclass
class Violation:
    """Represents a single linting violation.

    :Args:
        tool: Name of the tool that reported the violation (e.g., "black", "ruff")
        file: File path relative to repo root
        line: Line number (if applicable)
        message: Human-readable violation message
    """

    tool: str
    file: str
    line: Optional[int]
    message: str


@dataclass
class LintResult:
    """Result from running a linter or formatter.

    :Args:
        tool: Name of the tool that ran
        passed: Whether the check passed (no violations)
        violations: List of violations found
        error: Error message if the tool failed to run
    """

    tool: str
    passed: bool
    violations: List[Violation]
    error: Optional[str] = None


class RepoLintError(Exception):
    """Base exception for all repo_lint errors."""


class MissingToolError(RepoLintError):
    """Raised when required tools are not installed."""

    def __init__(self, tool: str, install_hint: Optional[str] = None):
        """Initialize MissingToolError.

        :param tool: Name of the missing tool
        :param install_hint: Optional installation hint for the user
        """
        self.tool = tool
        self.install_hint = install_hint
        msg = f"Required tool '{tool}' not found"
        if install_hint:
            msg += f"\nInstall hint: {install_hint}"
        super().__init__(msg)


class RunnerError(RepoLintError):
    """Raised when a runner encounters an error."""
