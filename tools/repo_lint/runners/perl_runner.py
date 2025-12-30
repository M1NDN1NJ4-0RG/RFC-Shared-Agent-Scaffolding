"""Perl language runner for Perl::Critic and docstring validation.

:Purpose:
    Runs all Perl linting tools as defined in the repository standards.
    Integrates with existing validate_docstrings.py script.

:Tools:
    - Perl::Critic: Perl source code analyzer
    - validate_docstrings.py: Docstring contract validation

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

import subprocess
import sys
from typing import List, Optional

from tools.repo_lint.common import LintResult, Violation
from tools.repo_lint.runners.base import Runner, command_exists


class PerlRunner(Runner):
    """Runner for Perl linting tools."""

    def has_files(self) -> bool:
        """Check if repository has Perl files.

        :returns:
            True if Perl files exist, False otherwise
        """
        result = subprocess.run(
            ["git", "ls-files", "**/*.pl"], cwd=self.repo_root, capture_output=True, text=True, check=False
        )
        return bool(result.stdout.strip())

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
        results.append(self._run_perlcritic())
        results.append(self._run_docstring_validation())

        return results

    def fix(self, policy: Optional[dict] = None) -> List[LintResult]:
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
        result = subprocess.run(
            ["git", "ls-files", "**/*.pl"], cwd=self.repo_root, capture_output=True, text=True, check=False
        )
        if not result.stdout.strip():
            return []
        
        # Exclude test fixture directories with intentional violations
        exclude_patterns = [
            "conformance/repo-lint/fixtures/violations/",
            "conformance/repo-lint/vectors/fixtures/",
            "scripts/tests/fixtures/",
        ]
        
        all_files = result.stdout.strip().split("\n")
        filtered_files = [
            f for f in all_files 
            if not any(pattern in f for pattern in exclude_patterns)
        ]
        
        return filtered_files

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
        """Run Perl docstring validation.

        :returns:
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

        perl_files = self._get_perl_files()
        if not perl_files:
            return LintResult(tool="validate_docstrings", passed=True, violations=[])

        # Run validator for perl language only (no need for --file args with --language flag)
        result = subprocess.run(
            [sys.executable, str(validator_script), "--language", "perl"],
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
