"""Perl language runner for Perl::Critic and docstring validation.

:Purpose:
    Runs all Perl linting tools as defined in the repository standards.
    Integrates with existing validate_docstrings.py script.

:Tools:
    - Perl::Critic: Perl source code analyzer
    - validate_docstrings.py: Docstring contract validation
"""

import subprocess
import sys
from typing import List

from tools.repo_lint.common import LintResult, Violation
from tools.repo_lint.runners.base import Runner, command_exists


class PerlRunner(Runner):
    """Runner for Perl linting tools."""

    def has_files(self) -> bool:
        """Check if repository has Perl files.

        :Returns:
            True if Perl files exist, False otherwise
        """
        result = subprocess.run(
            ["git", "ls-files", "**/*.pl"], cwd=self.repo_root, capture_output=True, text=True, check=False
        )
        return bool(result.stdout.strip())

    def check_tools(self) -> List[str]:
        """Check which Perl tools are missing.

        :Returns:
            List of missing tool names
        """
        required = ["perlcritic"]
        return [tool for tool in required if not command_exists(tool)]

    def check(self) -> List[LintResult]:
        """Run all Perl linting checks.

        :Returns:
            List of linting results from all Perl tools
        """
        self._ensure_tools(["perlcritic"])

        results = []
        results.append(self._run_perlcritic())
        results.append(self._run_docstring_validation())

        return results

    def fix(self) -> List[LintResult]:
        """Apply Perl auto-fixes where possible.

        Note: Perl::Critic does not have an auto-fix mode.

        :Returns:
            List of results (runs checks only)
        """
        self._ensure_tools(["perlcritic"])

        # Perl::Critic does not have auto-fix, so just run checks
        results = []
        results.append(self._run_perlcritic())
        results.append(self._run_docstring_validation())

        return results

    def _run_perlcritic(self) -> LintResult:
        """Run Perl::Critic.

        :Returns:
            LintResult for Perl::Critic
        """
        # Get all Perl files
        perl_files_result = subprocess.run(
            ["git", "ls-files", "**/*.pl"], cwd=self.repo_root, capture_output=True, text=True, check=False
        )

        if not perl_files_result.stdout.strip():
            return LintResult(tool="perlcritic", passed=True, violations=[])

        perl_files = perl_files_result.stdout.strip().split("\n")

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
        """Run Perl docstring validation.

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

        # Get all Perl files to validate
        perl_files_result = subprocess.run(
            ["git", "ls-files", "**/*.pl"], cwd=self.repo_root, capture_output=True, text=True, check=False
        )

        if not perl_files_result.stdout.strip():
            return LintResult(tool="validate_docstrings", passed=True, violations=[])

        perl_files = perl_files_result.stdout.strip().split("\n")

        # Run validator for each Perl file
        result = subprocess.run(
            [sys.executable, str(validator_script)] + [f"--file={f}" for f in perl_files],
            cwd=self.repo_root,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            return LintResult(tool="validate_docstrings", passed=True, violations=[])

        violations = []
        for line in result.stdout.splitlines():
            if "❌" in line or "ERROR" in line or "violation" in line.lower():
                violations.append(Violation(tool="validate_docstrings", file=".", line=None, message=line.strip()))

        return LintResult(tool="validate_docstrings", passed=False, violations=violations[:20])  # Limit output
