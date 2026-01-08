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
    - 4: UNSAFE_VIOLATION - Unsafe mode policy violation (CI or missing confirmation)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import List


def safe_print(text: str, fallback_text: str = None) -> None:
    """Print text with emoji, falling back to plain text on encoding errors.

    This function handles Windows and CI environments that may not support
    Unicode emoji characters. It attempts to print the original text, and
    if that fails due to encoding errors, it either prints a fallback or
    automatically strips/replaces emoji with ASCII equivalents.

    :param text: Text to print (may contain emoji)
    :param fallback_text: Fallback text if emoji can't be encoded (optional)

    :raises: Never raises - always prints something

    :examples:
        >>> safe_print("✓ Success")  # Works everywhere
        >>> safe_print("🔍 Searching...", "Searching...")  # With fallback
    """
    try:
        print(text)
    except UnicodeEncodeError:
        # Windows/CI environments may not support emoji
        if fallback_text:
            print(fallback_text)
        else:
            # Strip emoji and retry (simple fallback)
            # Replace common emoji with ASCII equivalents
            safe_text = (
                text.replace("🔍", "[*]")
                .replace("🔧", "[*]")
                .replace("🧹", "[*]")
                .replace("📦", "[*]")
                .replace("📄", "[-]")
                .replace("📋", "[-]")
                .replace("⚠️", "[!]")
                .replace("✓", "[+]")
                .replace("✗", "[x]")
                .replace("❌", "[X]")
                .replace("✅", "[OK]")
            )
            print(safe_text)


class ExitCode(IntEnum):
    """Standard exit codes for repo_lint."""

    SUCCESS = 0  # All checks passed
    VIOLATIONS = 1  # Linting/formatting violations found
    MISSING_TOOLS = 2  # Required tools not installed (CI mode)
    INTERNAL_ERROR = 3  # Internal error or exception
    UNSAFE_VIOLATION = 4  # Unsafe mode policy violation (CI or missing confirmation)


@dataclass
class Violation:
    """Represents a single linting violation.

    :param tool: Name of the tool that reported the violation (e.g., "black", "ruff")
    :param file: File path relative to repo root
    :param line: Line number (if applicable)
    :param message: Human-readable violation message
    """

    tool: str
    file: str
    line: int | None
    message: str


@dataclass
class LintResult:
    """Result from running a linter or formatter.

    :param tool: Name of the tool that ran
    :param passed: Whether the check passed (no violations)
    :param violations: List of violations found
    :param error: Error message if the tool failed to run
    :param file_count: Number of files checked (optional)
    :param duration: Time taken in seconds (optional)
    :param info_message: Informational message (displayed but doesn't affect pass/fail)
    """

    tool: str
    passed: bool
    violations: List[Violation]
    error: str | None = None
    file_count: int | None = None
    duration: float | None = None
    info_message: str | None = None


class RepoLintError(Exception):
    """Base exception for all repo_lint errors."""


class MissingToolError(RepoLintError):
    """Raised when required tools are not installed."""

    def __init__(self, tool: str, install_hint: str | None = None):
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


# File filtering utilities


def filter_excluded_paths(files: List[str], exclude_patterns: List[str] | None = None) -> List[str]:
    """Filter out files matching exclusion patterns.

    :param files: List of file paths to filter
    :param exclude_patterns: List of path patterns to exclude (uses substring matching)
    :returns: Filtered list of file paths

    :Examples:
        Filter test fixtures::

            files = ["src/main.py", "fixtures/violations/bad.py"]
            filtered = filter_excluded_paths(files, ["fixtures/violations/"])
            # Result: ["src/main.py"]

    :Note:
        Uses simple substring matching. A file is excluded if any pattern
        appears anywhere in its path. This is consistent with how git pathspecs
        work for directory exclusions.
    """
    if exclude_patterns is None:
        exclude_patterns = get_default_exclude_patterns()

    return [f for f in files if not any(pattern in f for pattern in exclude_patterns)]


def get_default_exclude_patterns() -> List[str]:
    """Get the default list of exclusion patterns for test fixtures.

    :returns: List of exclusion patterns

    :Note:
        These patterns are used consistently across all language runners to
        exclude test fixtures with intentional violations from linting.
    """
    return [
        "conformance/repo-lint/fixtures/violations/",
        "conformance/repo-lint/vectors/fixtures/",
        "scripts/tests/fixtures/",
    ]


def convert_validation_errors_to_violations(errors: List, tool_name: str) -> List[Violation]:
    """Convert ValidationError objects to Violation objects for repo_lint reporting.

    :param errors: List of ValidationError objects from docstring validators
    :param tool_name: Name of the tool reporting violations (e.g., "python-docstrings")

    :returns: List of Violation objects suitable for LintResult, limited to 20 items

    :Note:
        This function provides a standardized conversion from the internal
        docstring validation ValidationError format to the repo_lint Violation
        format. It handles symbol information, missing sections, and message
        formatting consistently across all language runners.
    """
    import os

    violations = []
    for error in errors:
        file_basename = os.path.basename(error.file_path)

        if error.missing_sections:
            sections = ", ".join(error.missing_sections)
            if error.symbol_name:
                message = f"Symbol '{error.symbol_name}': Missing {sections}"
            else:
                message = f"Missing required sections: {sections}"
        else:
            message = error.message

        if error.message and error.missing_sections:
            message += f" ({error.message})"

        violations.append(
            Violation(
                tool=tool_name,
                file=file_basename,
                line=error.line_number,
                message=message,
            )
        )
    return violations[:20]  # Limit output
