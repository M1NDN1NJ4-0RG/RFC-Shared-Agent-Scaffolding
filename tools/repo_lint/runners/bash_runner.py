"""Bash language runner for ShellCheck, shfmt, and docstring validation.

:Purpose:
    Runs all Bash linting and formatting tools as defined in the repository
    standards. Integrates with existing validate_docstrings.py script.

:Tools:
    - ShellCheck: Static analysis for shell scripts
    - shfmt: Shell script formatter
    - validate_docstrings.py: Docstring contract validation

:Environment Variables:
    None

:Examples:
    Use this runner::

        from tools.repo_lint.runners.bash_runner import BashRunner
        runner = BashRunner()
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
from tools.repo_lint.policy import is_category_allowed
from tools.repo_lint.runners.base import Runner, command_exists


class BashRunner(Runner):
    """Runner for Bash linting and formatting tools."""

    def has_files(self) -> bool:
        """Check if repository has Bash files.

        :returns:
            True if Bash files exist, False otherwise
        """
        result = subprocess.run(
            ["git", "ls-files", "**/*.sh"], cwd=self.repo_root, capture_output=True, text=True, check=False
        )
        return bool(result.stdout.strip())

    def check_tools(self) -> List[str]:
        """Check which Bash tools are missing.

        :returns:
            List of missing tool names
        """
        required = ["shellcheck", "shfmt"]
        return [tool for tool in required if not command_exists(tool)]

    def check(self) -> List[LintResult]:
        """Run all Bash linting checks.

        :returns:
            List of linting results from all Bash tools
        """
        self._ensure_tools(["shellcheck", "shfmt"])

        results = []
        results.append(self._run_shellcheck())
        results.append(self._run_shfmt_check())
        results.append(self._run_docstring_validation())

        return results

    def fix(self, policy: Optional[dict] = None) -> List[LintResult]:
        """Apply Bash formatters and safe auto-fixes.

        Per Phase 6 Item 6.5.6: Consult auto-fix policy before running fixes.

        :param policy: Auto-fix policy dictionary (deny-by-default)
        :returns: List of results after applying fixes
        """
        self._ensure_tools(["shellcheck", "shfmt"])

        results = []

        # Default policy if none provided (backwards compatibility)
        # Note: Empty policy denies all fixes. This is intentional during transition.
        if policy is None:
            policy = {"allowed_categories": []}

        # Apply shfmt formatting (if allowed by policy)
        if is_category_allowed(policy, "FORMAT.SHFMT"):
            shfmt_result = self._run_shfmt_fix()
            results.append(shfmt_result)
        else:
            if self.verbose:
                print("  ⊘ Skipping shfmt (denied by policy)")
            shfmt_result = LintResult(tool="shfmt", passed=True, violations=[])
            results.append(shfmt_result)

        # Re-run checks only if shfmt succeeded
        if shfmt_result.passed:
            results.append(self._run_shellcheck())
            results.append(self._run_docstring_validation())

        return results

    def _get_bash_files(self) -> List[str]:
        """Get list of Bash files in repository.

        :returns:
            List of Bash file paths (empty list if none found)
        """
        result = subprocess.run(
            ["git", "ls-files", "**/*.sh"], cwd=self.repo_root, capture_output=True, text=True, check=False
        )
        if not result.stdout.strip():
            return []
        return result.stdout.strip().split("\n")

    def _run_shellcheck(self) -> LintResult:
        """Run ShellCheck.

        :returns:
            LintResult for ShellCheck
        """
        bash_files = self._get_bash_files()
        if not bash_files:
            return LintResult(tool="shellcheck", passed=True, violations=[])

        # Run shellcheck
        result = subprocess.run(
            ["shellcheck", "--color=never", "--format=gcc"] + bash_files,
            cwd=self.repo_root,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            return LintResult(tool="shellcheck", passed=True, violations=[])

        violations = []
        for line in result.stdout.splitlines():
            if line.strip():
                violations.append(Violation(tool="shellcheck", file=".", line=None, message=line.strip()))

        return LintResult(tool="shellcheck", passed=False, violations=violations[:20])  # Limit output

    def _run_shfmt_check(self) -> LintResult:
        """Run shfmt in check mode.

        :returns:
            LintResult for shfmt check
        """
        bash_files = self._get_bash_files()
        if not bash_files:
            return LintResult(tool="shfmt", passed=True, violations=[])

        # Run shfmt in check mode (-d = diff, -l = list files)
        result = subprocess.run(
            ["shfmt", "-d", "-l"] + bash_files,
            cwd=self.repo_root,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            return LintResult(tool="shfmt", passed=True, violations=[])

        violations = []
        if result.stdout:
            violations.append(
                Violation(
                    tool="shfmt",
                    file=".",
                    line=None,
                    message=(
                        "Shell scripts do not match shfmt style. " "Run 'python -m tools.repo_lint fix' to auto-format."
                    ),
                )
            )

        return LintResult(tool="shfmt", passed=False, violations=violations)

    def _run_shfmt_fix(self) -> LintResult:
        """Run shfmt to fix formatting.

        :returns:
            LintResult for shfmt fix operation
        """
        bash_files = self._get_bash_files()
        if not bash_files:
            return LintResult(tool="shfmt", passed=True, violations=[])

        # Run shfmt in fix mode (-w = write)
        result = subprocess.run(
            ["shfmt", "-w"] + bash_files,
            cwd=self.repo_root,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            return LintResult(tool="shfmt", passed=True, violations=[])

        return LintResult(
            tool="shfmt", passed=False, violations=[], error=f"shfmt failed with exit code {result.returncode}"
        )

    def _run_docstring_validation(self) -> LintResult:
        """Run Bash docstring validation.

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

        bash_files = self._get_bash_files()
        if not bash_files:
            return LintResult(tool="validate_docstrings", passed=True, violations=[])

        # Run validator for each Bash file
        result = subprocess.run(
            [sys.executable, str(validator_script)] + [f"--file={f}" for f in bash_files],
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
