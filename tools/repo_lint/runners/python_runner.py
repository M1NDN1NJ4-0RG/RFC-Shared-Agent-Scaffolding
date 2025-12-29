"""Python language runner for Black, Ruff, Pylint, and docstring validation.

:Purpose:
    Runs all Python linting and formatting tools as defined in the repository
    standards. Integrates with existing validate_docstrings.py script.

:Tools:
    - Black: Code formatter (PEP 8 compliant)
    - Ruff: Fast Python linter (replaces Flake8)
    - Pylint: Comprehensive static analysis
    - validate_docstrings.py: Docstring contract validation
"""

import subprocess
import sys
from typing import List

from tools.repo_lint.common import LintResult, Violation
from tools.repo_lint.runners.base import Runner, command_exists


class PythonRunner(Runner):
    """Runner for Python linting and formatting tools."""

    def has_files(self) -> bool:
        """Check if repository has Python files.

        :Returns:
            True if Python files exist, False otherwise
        """
        result = subprocess.run(
            ["git", "ls-files", "**/*.py"], cwd=self.repo_root, capture_output=True, text=True, check=False
        )
        return bool(result.stdout.strip())

    def check_tools(self) -> List[str]:
        """Check which Python tools are missing.

        :Returns:
            List of missing tool names
        """
        required = ["black", "ruff", "pylint"]
        return [tool for tool in required if not command_exists(tool)]

    def check(self) -> List[LintResult]:
        """Run all Python linting checks.

        :Returns:
            List of linting results from all Python tools
        """
        self._ensure_tools(["black", "ruff", "pylint"])

        results = []
        results.append(self._run_black_check())
        results.append(self._run_ruff_check())
        results.append(self._run_pylint())
        results.append(self._run_docstring_validation())

        return results

    def fix(self) -> List[LintResult]:
        """Apply Python formatters (Black only).

        :Returns:
            List of results after applying fixes
        """
        self._ensure_tools(["black", "ruff", "pylint"])

        results = []

        # Apply Black formatting
        black_result = self._run_black_fix()
        results.append(black_result)

        # Re-run checks after formatting
        if black_result.passed or not black_result.violations:
            results.append(self._run_ruff_check())
            results.append(self._run_pylint())
            results.append(self._run_docstring_validation())

        return results

    def _run_black_check(self) -> LintResult:
        """Run Black in check mode.

        :Returns:
            LintResult for Black check
        """
        result = subprocess.run(
            ["black", "--check", "--diff", "."], cwd=self.repo_root, capture_output=True, text=True, check=False
        )

        if result.returncode == 0:
            return LintResult(tool="black", passed=True, violations=[])

        # Parse Black output to extract violations
        violations = []
        if result.stdout:
            # Black outputs diffs, we'll create a summary violation
            violations.append(
                Violation(
                    tool="black",
                    file=".",
                    line=None,
                    message="Code formatting does not match Black style. Run 'repo-lint fix' to auto-format.",
                )
            )

        return LintResult(tool="black", passed=False, violations=violations)

    def _run_black_fix(self) -> LintResult:
        """Run Black to fix formatting.

        :Returns:
            LintResult for Black fix operation
        """
        result = subprocess.run(["black", "."], cwd=self.repo_root, capture_output=True, text=True, check=False)

        if result.returncode == 0:
            return LintResult(tool="black", passed=True, violations=[])

        return LintResult(
            tool="black", passed=False, violations=[], error=f"Black failed with exit code {result.returncode}"
        )

    def _run_ruff_check(self) -> LintResult:
        """Run Ruff linter with auto-fix for safe fixes.

        :Returns:
            LintResult for Ruff check
        """
        # First, auto-fix safe fixes
        subprocess.run(
            ["ruff", "check", ".", "--fix"],
            cwd=self.repo_root,
            capture_output=True,
            text=True,
            check=False,
        )

        # Then check for remaining issues (including unsafe fixes)
        result = subprocess.run(["ruff", "check", "."], cwd=self.repo_root, capture_output=True, text=True, check=False)

        if result.returncode == 0:
            return LintResult(tool="ruff", passed=True, violations=[])

        # Parse Ruff output
        violations = []

        for line in result.stdout.splitlines():
            if line.strip():
                if "hidden fixes can be enabled with the `--unsafe-fixes` option" in line:
                    violations.append(
                        Violation(
                            tool="ruff",
                            file=".",
                            line=None,
                            message=f"⚠️  {line.strip()} (Review before applying with --unsafe-fixes)",
                        )
                    )
                elif not line.startswith("Found"):
                    # Ruff output format: path:line:col: code message
                    violations.append(Violation(tool="ruff", file=".", line=None, message=line.strip()))

        return LintResult(tool="ruff", passed=False, violations=violations)

    def _run_pylint(self) -> LintResult:
        """Run Pylint.

        :Returns:
            LintResult for Pylint check
        """
        # Get all Python files
        py_files_result = subprocess.run(
            ["git", "ls-files", "-z", "**/*.py"], cwd=self.repo_root, capture_output=True, text=True, check=False
        )

        if not py_files_result.stdout.strip():
            return LintResult(tool="pylint", passed=True, violations=[])

        # Run pylint
        result = subprocess.run(
            ["xargs", "-0", "-r", "pylint"],
            cwd=self.repo_root,
            input=py_files_result.stdout,
            capture_output=True,
            text=True,
            check=False,
        )

        # Pylint exit codes: 0=success, 1-31=violations/errors
        if result.returncode == 0:
            return LintResult(tool="pylint", passed=True, violations=[])

        violations = []
        for line in result.stdout.splitlines():
            if line.strip() and not line.startswith("----") and not line.startswith("Your code"):
                violations.append(Violation(tool="pylint", file=".", line=None, message=line.strip()))

        return LintResult(tool="pylint", passed=False, violations=violations[:20])  # Limit output

    def _run_docstring_validation(self) -> LintResult:
        """Run Python docstring validation.

        :Returns:
            LintResult for docstring validation
        """
        validator_script = self.repo_root / "scripts" / "validate_docstrings.py"

        if not validator_script.exists():
            return LintResult(
                tool="validate_docstrings",
                passed=False,
                violations=[],
                error=f"Docstring validator script not found: {validator_script}",
            )

        result = subprocess.run(
            [sys.executable, str(validator_script)], cwd=self.repo_root, capture_output=True, text=True, check=False
        )

        if result.returncode == 0:
            return LintResult(tool="validate_docstrings", passed=True, violations=[])

        violations = []
        for line in result.stdout.splitlines():
            if "❌" in line or "ERROR" in line or "violation" in line.lower():
                violations.append(Violation(tool="validate_docstrings", file=".", line=None, message=line.strip()))

        return LintResult(tool="validate_docstrings", passed=False, violations=violations[:20])  # Limit output
