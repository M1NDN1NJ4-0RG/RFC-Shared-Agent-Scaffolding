"""YAML language runner for yamllint.

:Purpose:
    Runs all YAML linting tools as defined in the repository standards.

:Tools:
    - yamllint: YAML linter

:Environment Variables:
    None

:Examples:
    Use this runner::

        from tools.repo_lint.runners.yaml_runner import YAMLRunner
        runner = YAMLRunner()
        results = runner.check()

:Exit Codes:
    Returns LintResult objects, not exit codes directly:
    - 0: Success (LintResult.passed = True)
    - 1: Violations found (LintResult.passed = False)
"""

import subprocess
from typing import List, Optional

from tools.repo_lint.common import LintResult, Violation
from tools.repo_lint.runners.base import Runner, command_exists, get_tracked_files


class YAMLRunner(Runner):
    """Runner for YAML linting tools."""

    def has_files(self) -> bool:
        """Check if repository has YAML files.

        :returns:
            True if YAML files exist, False otherwise
        """
        # If changed-only mode, check for changed YAML files
        if self._changed_only:
            changed_files = self._get_changed_files(patterns=["*.yml", "*.yaml", "**/*.yml", "**/*.yaml"])
            return len(changed_files) > 0
        
        # Otherwise check all tracked YAML files
        files = get_tracked_files(["**/*.yml", "**/*.yaml"], self.repo_root)
        return len(files) > 0

    def check_tools(self) -> List[str]:
        """Check which YAML tools are missing.

        :returns:
            List of missing tool names
        """
        required = ["yamllint"]
        return [tool for tool in required if not command_exists(tool)]

    def check(self) -> List[LintResult]:
        """Run all YAML linting checks.

        :returns:
            List of linting results from all YAML tools
        """
        self._ensure_tools(["yamllint"])

        results = []
        
        # Apply tool filtering
        if self._should_run_tool("yamllint"):
            results.append(self._run_yamllint())

        return results

    def fix(self, policy: Optional[dict] = None) -> List[LintResult]:
        """Apply YAML auto-fixes where possible.

        Note: yamllint does not have an auto-fix mode.


        :param policy: Auto-fix policy dictionary (unused)
        :returns:
            List of results (runs checks only)
        """
        self._ensure_tools(["yamllint"])

        # yamllint does not have auto-fix, so just run checks
        results = []
        results.append(self._run_yamllint())

        return results

    def _run_yamllint(self) -> LintResult:
        """Run yamllint.

        :returns:
            LintResult for yamllint
        """
        # Get all YAML files, excluding test fixtures
        yaml_files = get_tracked_files(["**/*.yml", "**/*.yaml"], self.repo_root)

        if not yaml_files:
            return LintResult(tool="yamllint", passed=True, violations=[])

        # Run yamllint
        result = subprocess.run(
            ["yamllint", "-f", "parsable"] + yaml_files,
            cwd=self.repo_root,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            return LintResult(tool="yamllint", passed=True, violations=[])

        violations = []
        for line in result.stdout.splitlines():
            if line.strip():
                violations.append(Violation(tool="yamllint", file=".", line=None, message=line.strip()))

        return LintResult(tool="yamllint", passed=False, violations=violations[:20])  # Limit output
