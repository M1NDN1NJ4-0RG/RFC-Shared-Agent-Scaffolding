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

from __future__ import annotations

import inspect
import logging
import re
import shutil
import subprocess
import traceback
import warnings
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List

from tools.repo_lint.common import LintResult, MissingToolError


# DEPRECATED (Phase 2.9): Use get_excluded_paths() instead
# This constant is maintained for backward compatibility only
def __getattr__(name):
    """Provide backward compatibility for deprecated module-level constants.

    This module-level __getattr__ function enables smooth migration from hardcoded
    constants to YAML-first configuration (Phase 2.9). It intercepts attribute
    access to deprecated constants and redirects to the new YAML-based functions
    while emitting deprecation warnings.

    This pattern allows existing code that imports deprecated constants to continue
    working during the transition period, giving users time to update their code
    before the constants are completely removed in a future release.

    :param name: Attribute name being accessed
    :returns: List of excluded paths from YAML config (for EXCLUDED_PATHS)

    :raises AttributeError: If the requested attribute doesn't exist or isn't deprecated
    """
    if name == "EXCLUDED_PATHS":
        warnings.warn(
            "EXCLUDED_PATHS constant is deprecated. Use get_excluded_paths() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return get_excluded_paths()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def find_repo_root() -> Path:
    """Find the repository root directory (legacy wrapper).

    DEPRECATED: Use tools.repo_lint.repo_utils.find_repo_root() directly.

    :returns: Path to repository root

    :Note:
        This is a compatibility wrapper around the shared repo_utils.find_repo_root().
        New code should import directly from tools.repo_lint.repo_utils.
    """
    # pylint: disable=import-outside-toplevel,redefined-outer-name
    from tools.repo_lint.repo_utils import find_repo_root as find_repo_root_impl

    return find_repo_root_impl()


def command_exists(command: str) -> bool:
    """Check if a command exists in PATH (cross-platform).

    :param command: Command name to check
    :returns: True if command exists, False otherwise
    """
    return shutil.which(command) is not None


def get_excluded_paths() -> List[str]:
    """Get paths to exclude from linting (YAML-first, Phase 2.9).

    :returns: List of paths to exclude from linting

    :Note:
        This function loads exclusions from conformance/repo-lint/repo-lint-file-patterns.yaml
        and replaces the hardcoded EXCLUDED_PATHS constant.
    """
    # pylint: disable=import-outside-toplevel
    from tools.repo_lint.yaml_loader import get_linting_exclusion_paths

    return get_linting_exclusion_paths()


def get_git_pathspec_excludes(include_fixtures: bool = False) -> List[str]:
    """Get git pathspec exclude patterns for linting (YAML-first, Phase 2.9).

    :param include_fixtures: Whether to include test fixture files (vector mode)
    :returns: List of exclude patterns for git ls-files

    :Note:
        Updated in Phase 2.9 to use YAML configuration instead of hardcoded EXCLUDED_PATHS.
        In vector mode (include_fixtures=True), test fixtures are included in scans.
    """
    excludes = []
    for path in get_excluded_paths():
        # Skip fixture exclusions when in vector mode
        # Check if path is any fixture pattern (ends with fixtures/** or fixtures/)
        if include_fixtures and ("fixtures/**" in path or "fixtures/" == path.rstrip("*")):
            continue
        # Git pathspec format: ':(exclude)pattern'
        excludes.append(f":(exclude){path}")
    return excludes


def get_tracked_files(patterns: List[str], repo_root: Path | None = None, include_fixtures: bool = False) -> List[str]:
    """Get tracked files matching patterns, excluding lint test fixtures.

    :param patterns: List of file patterns (e.g., ["**/*.py", "**/*.sh"])
    :param repo_root: Repository root path (auto-detected if None)
    :param include_fixtures: Whether to include test fixture files (vector mode)
    :returns: List of file paths (empty list if none found)

    :Note:
        When include_fixtures=True (vector mode), test fixture files under tests/fixtures/
        are included in the results. This is used for vector-based conformance testing.
    """
    if repo_root is None:
        repo_root = find_repo_root()

    excludes = get_git_pathspec_excludes(include_fixtures=include_fixtures)
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

    def __init__(self, repo_root: Path | None = None, ci_mode: bool = False, verbose: bool = False):
        """Initialize runner.

        :param repo_root: Path to repository root (auto-detected if None)
        :param ci_mode: Whether running in CI mode (fail if tools missing)
        :param verbose: Whether to show verbose output
        """
        self.repo_root = repo_root or find_repo_root()
        self.ci_mode = ci_mode
        self.verbose = verbose
        self._tool_filter = None  # List of specific tools to run (None = run all)
        self._changed_only = False  # Only check git-changed files
        self._include_fixtures = False  # Include test fixtures in scans (vector mode)

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
    def fix(self, policy: dict | None = None) -> List[LintResult]:
        """Apply automatic fixes where possible (formatters only).

        :param policy: Auto-fix policy dictionary (deny-by-default)
        :returns: List of linting results after fixes applied
        :raises MissingToolError: If required tools are not installed (CI mode only)
        """
        pass  # pylint: disable=unnecessary-pass  # Abstract method

    def check_parallel(self, max_workers: int = 4) -> List[LintResult]:
        """Run linting checks with tool-level parallelism (optional).

        This is a default implementation that introspects the runner for tool methods
        and executes them in parallel. Runners can override this for custom behavior
        or declare which methods are safe to parallelize explicitly.

        :param max_workers: Maximum number of parallel tool executions
        :returns: List of linting results from all tools (in deterministic order)

        :note: This method uses naming conventions to discover tool methods. For more
               explicit control, runners should override this method and declare which
               methods to parallelize. The current pattern matches methods starting with
               '_run_' that aren't fix/format/helper/util methods.
        """
        # TODO: CRITICAL - Replace introspection with explicit declaration pattern  # pylint: disable=fixme
        # FUTURE: Add @parallelizable decorator or _parallelizable_methods class attribute
        # Current implementation relies on naming conventions which is fragile and may not
        # be reliable across all runners. This should be refactored to use explicit opt-in.
        # (Copilot review comment - high priority for maintainability)

        # Get all methods that look like tool check methods
        # Pattern: _run_* methods that are likely tool-specific
        tool_methods = []
        for name, method in inspect.getmembers(self, predicate=inspect.ismethod):
            # Include methods that start with _run_ and aren't utility methods
            if (
                name.startswith("_run_")
                and not name.endswith(("_fix", "_format", "_helper", "_util"))
                and callable(method)
            ):
                # Extract tool name using regex for more robust parsing
                # Handles patterns like: _run_black_check, _run_pylint, _run_docstring_validation
                # Also supports numbers: _run_python3_check, _run_ps1_check
                tool_name_match = re.match(r"_run_([a-z0-9_]+?)(?:_check|_validation)?$", name)
                if tool_name_match:
                    tool_name = tool_name_match.group(1)
                    # Verify the method matches check() behavior by checking if tool filtering applies
                    # Only call _should_run_tool if it exists; otherwise, include all discovered methods
                    should_run_tool = getattr(self, "_should_run_tool", None)
                    if should_run_tool is None or should_run_tool(tool_name):
                        tool_methods.append((name, method))

        # If no tool methods found or only one, fall back to sequential
        if len(tool_methods) <= 1:
            return self.check()

        # Execute tools in parallel
        # Note: Tool methods (_run_*_check, _run_*_validation) return single LintResult objects,
        # not lists. The check() method aggregates these into a List[LintResult].
        # Verify type at runtime to catch implementation errors early.
        results_map = {}  # method_name -> result (single LintResult)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_method = {executor.submit(method): name for name, method in tool_methods}

            for future in as_completed(future_to_method):
                method_name = future_to_method[future]
                try:
                    result = future.result()
                    # Verify that tool methods return single LintResult, not lists
                    if isinstance(result, list):
                        logging.warning(
                            "Tool method %s returned a list instead of single LintResult. Using first result only.",
                            method_name,
                        )
                        result = result[0] if result else LintResult(tool="unknown", passed=True, violations=[])
                    results_map[method_name] = result
                except Exception as e:
                    # Log full exception for debugging
                    logging.error("Tool method %s failed with exception:\n%s", method_name, traceback.format_exc())
                    # Create error result for failed tool
                    results_map[method_name] = LintResult(
                        tool=method_name, passed=False, violations=[], error=f"Tool execution failed: {str(e)}"
                    )

        # Return results in deterministic order (same order as tool_methods)
        results = []
        for name, _ in tool_methods:
            if name in results_map:
                results.append(results_map[name])

        return results

    def set_tool_filter(self, tools: List[str]) -> None:
        """Set tool filter to run only specific tools.

        :param tools: List of tool names to run (e.g., ["black", "ruff"])

        :Purpose:
            Enables granular tool filtering so users can run specific linters/formatters
            without running the full suite. Runners should check this filter in their
            check() and fix() methods.
        """
        self._tool_filter = tools

    def set_changed_only(self, enabled: bool = True) -> None:
        """Enable/disable changed-only mode.

        :param enabled: Whether to only check git-changed files

        :Purpose:
            Restricts linting to files that have been modified according to git.
            Useful for pre-commit hooks and iterative development.
            Requires git repository (will error if not in git repo).
        """
        self._changed_only = enabled

    def set_include_fixtures(self, enabled: bool = True) -> None:
        """Enable/disable fixture inclusion (vector mode).

        :param enabled: Whether to include test fixture files in scans

        :Purpose:
            Includes test fixture files (tests/fixtures/**) in linting scans.
            Used for vector-based conformance testing to verify that repo-lint
            correctly detects violations in intentionally-bad fixture files.
            When disabled (default), fixtures are excluded from all scans.
        """
        self._include_fixtures = enabled

    def _should_run_tool(self, tool_name: str) -> bool:
        """Check if a specific tool should run based on tool filter.

        :param tool_name: Name of tool to check
        :returns: True if tool should run, False if filtered out

        :Purpose:
            Helper method for runners to check tool filter. If no filter is set,
            all tools run. If filter is set, only tools in the filter run.
        """
        if self._tool_filter is None:
            return True
        return tool_name in self._tool_filter

    def _get_changed_files(self, patterns: List[str] | None = None) -> List[str]:
        """Get list of files changed in git working tree.

        :param patterns: Optional file patterns to filter (e.g., ["*.py"])
        :returns: List of changed file paths
        :raises RuntimeError: If not in a git repository

        :Purpose:
            Retrieves files with uncommitted changes from git. Used when --changed-only
            is specified to limit linting scope.
        """
        # Get files changed in working tree (unstaged + staged)
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=self.repo_root,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            raise RuntimeError("Not in a git repository. --changed-only requires git repository.")

        files = result.stdout.strip().split("\n") if result.stdout.strip() else []

        # Apply pattern filtering if requested
        if patterns:
            import fnmatch  # pylint: disable=import-outside-toplevel

            filtered = []
            for file in files:
                for pattern in patterns:
                    if fnmatch.fnmatch(file, pattern):
                        filtered.append(file)
                        break
            return filtered

        return files

    def _ensure_tools(self, required_tools: List[str]) -> None:
        """Ensure required tools are installed.

        :param required_tools: List of required tool names
        :raises MissingToolError: If any required tools are missing and CI mode is enabled
        """
        missing = [tool for tool in required_tools if not command_exists(tool)]
        if missing and self.ci_mode:
            raise MissingToolError(missing[0], f"Install {', '.join(missing)} to continue")
