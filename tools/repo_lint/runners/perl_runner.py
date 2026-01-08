"""Perl language runner for Perl::Critic and docstring validation.

:Purpose:
    Runs all Perl linting tools as defined in the repository standards.
    Uses internal docstring validation module.

:Tools:
    - Perl::Critic: Perl source code analyzer
    - Internal docstring validator: Docstring contract validation

:Environment Variables:
    None

:Examples:
    Use this runner::

        from tools.repo_lint.runners.perl_runner import PerlRunner
        runner = PerlRunner()
        results = runner.check()

:Exit Codes:
    Returns LintResult objects, not exit codes directly:
    - 0: Success (LintResult.passed = True)
    - 1: Violations found (LintResult.passed = False)
"""

from __future__ import annotations

import os
import subprocess
from typing import List

from tools.repo_lint.common import LintResult, Violation, filter_excluded_paths
from tools.repo_lint.docstrings import validate_files
from tools.repo_lint.runners.base import Runner, command_exists, get_tracked_files


class PerlRunner(Runner):
    """Runner for Perl linting tools."""

    def has_files(self) -> bool:
        """Check if repository has Perl files.

        :returns:
            True if Perl files exist, False otherwise
        """
        # If changed-only mode, check for changed Perl files
        if self._changed_only:
            changed_files = self._get_changed_files(patterns=["*.pl", "**/*.pl"])
            return len(changed_files) > 0

        # Otherwise check all tracked Perl files
        files = get_tracked_files(["**/*.pl"], self.repo_root, include_fixtures=self._include_fixtures)
        return len(files) > 0

    def check_tools(self) -> List[str]:
        """Check which Perl tools are missing.

        :returns:
            List of missing tool names
        """
        required = ["perlcritic"]
        return [tool for tool in required if not command_exists(tool)]

    def check(self) -> List[LintResult]:
        """Run all Perl linting checks.

        :returns:
            List of linting results from all Perl tools
        """
        self._ensure_tools(["perlcritic"])

        results = []

        # Apply tool filtering
        if self._should_run_tool("perlcritic"):
            results.append(self._run_perlcritic())

        if self._should_run_tool("validate_docstrings"):
            results.append(self._run_docstring_validation())

        return results

    def fix(self, policy: dict | None = None) -> List[LintResult]:
        """Apply Perl auto-fixes where possible.

        Note: Perl::Critic does not have an auto-fix mode.

        :param policy: Auto-fix policy dictionary (unused for Perl)
        :returns: List of results (runs checks only)
        """
        self._ensure_tools(["perlcritic"])

        # Perl::Critic does not have auto-fix, so just run checks
        results = []
        results.append(self._run_perlcritic())
        results.append(self._run_docstring_validation())

        return results

    def _get_perl_files(self) -> List[str]:
        """Get list of Perl files in repository, excluding test fixtures.

        :returns:
            List of Perl file paths (empty list if none found)
        """
        all_files = get_tracked_files(["**/*.pl"], self.repo_root, include_fixtures=self._include_fixtures)
        return filter_excluded_paths(all_files)

    def _run_perlcritic(self) -> LintResult:
        """Run Perl::Critic.

        :returns:
            LintResult for Perl::Critic
        """
        perl_files = self._get_perl_files()
        if not perl_files:
            return LintResult(tool="perlcritic", passed=True, violations=[])

        # Run perlcritic
        result = subprocess.run(
            ["perlcritic", "--verbose", "8"] + perl_files,
            cwd=self.repo_root,
            capture_output=True,
            text=True,
            check=False,
        )

        # perlcritic exit code 0 = no violations, 2 = violations found
        if result.returncode == 0:
            return LintResult(tool="perlcritic", passed=True, violations=[])

        violations = []
        for line in result.stdout.splitlines():
            if line.strip() and not line.startswith("source OK"):
                violations.append(Violation(tool="perlcritic", file=".", line=None, message=line.strip()))

        return LintResult(tool="perlcritic", passed=False, violations=violations[:20])  # Limit output

    def _run_docstring_validation(self) -> LintResult:
        """Run Perl docstring validation using internal module.

        :returns:
            LintResult for docstring validation
        """
        perl_files = self._get_perl_files()
        if not perl_files:
            return LintResult(tool="perl-docstrings", passed=True, violations=[])

        # Use internal validator module
        errors = validate_files(perl_files, language="perl")

        if not errors:
            return LintResult(tool="perl-docstrings", passed=True, violations=[])

        # Convert ValidationError objects to Violation objects
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
                    tool="perl-docstrings",
                    file=file_basename,
                    line=error.line_number,
                    message=message,
                )
            )

        return LintResult(tool="perl-docstrings", passed=False, violations=violations[:20])
