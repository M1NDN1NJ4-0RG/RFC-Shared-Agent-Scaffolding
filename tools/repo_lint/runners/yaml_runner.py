"""YAML language runner for yamllint, actionlint, and docstring validation.

:Purpose:
    Runs all YAML linting tools as defined in the repository standards.

:Tools:
    - yamllint: YAML linter (required)
    - actionlint: GitHub Actions workflow linter (optional)
    - yaml-docstrings: YAML docstring contract validator (required)

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

from __future__ import annotations

import subprocess
import sys
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
        files = get_tracked_files(["**/*.yml", "**/*.yaml"], self.repo_root, include_fixtures=self._include_fixtures)
        return len(files) > 0

    def check_tools(self) -> List[str]:
        """Check which YAML tools are missing.

        :returns:
            List of missing tool names
        """
        required = ["yamllint"]
        # actionlint is optional - only report as missing if it would be used
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

        # Run actionlint if available and requested
        if self._should_run_tool("actionlint") and command_exists("actionlint"):
            results.append(self._run_actionlint())

        # Run YAML docstring validation
        if self._should_run_tool("yaml-docstrings"):
            results.append(self._run_docstring_validation())

        return results

    def fix(self, policy: Optional[dict] = None) -> List[LintResult]:
        """Apply YAML auto-fixes where possible.

        Note: yamllint and actionlint do not have auto-fix modes.
        yaml-docstrings is included for consistency with other language runners.

        :param policy: Auto-fix policy dictionary (unused)
        :returns:
            List of results (runs checks only)
        """
        self._ensure_tools(["yamllint"])

        # yamllint and actionlint do not have auto-fix, so just run checks
        results = []
        if self._should_run_tool("yamllint"):
            results.append(self._run_yamllint())

        if self._should_run_tool("actionlint") and command_exists("actionlint"):
            results.append(self._run_actionlint())

        if self._should_run_tool("yaml-docstrings"):
            results.append(self._run_docstring_validation())

        return results

    def _run_yamllint(self) -> LintResult:
        """Run yamllint.

        :returns:
            LintResult for yamllint
        """
        # Get all YAML files, excluding test fixtures
        yaml_files = get_tracked_files(
            ["**/*.yml", "**/*.yaml"], self.repo_root, include_fixtures=self._include_fixtures
        )

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

    def _run_actionlint(self) -> LintResult:
        """Run actionlint on GitHub Actions workflow files.

        actionlint validates GitHub Actions workflow syntax, expressions, and references.
        It only runs on files matching .github/workflows/*.yml pattern.

        Reference: https://github.com/rhysd/actionlint

        :returns:
            LintResult for actionlint
        """
        # Get GitHub Actions workflow files only
        workflow_files = get_tracked_files(
            [".github/workflows/*.yml", ".github/workflows/*.yaml"],
            self.repo_root,
            include_fixtures=self._include_fixtures,
        )

        if not workflow_files:
            return LintResult(tool="actionlint", passed=True, violations=[])

        # Run actionlint
        result = subprocess.run(
            ["actionlint"] + workflow_files,
            cwd=self.repo_root,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            return LintResult(tool="actionlint", passed=True, violations=[])

        violations = []
        for line in result.stdout.splitlines():
            if line.strip():
                # actionlint output format: file:line:col: message
                violations.append(Violation(tool="actionlint", file=".", line=None, message=line.strip()))

        return LintResult(tool="actionlint", passed=False, violations=violations[:20])  # Limit output

    def _run_docstring_validation(self) -> LintResult:
        """Run YAML docstring contract validation.

        Validates that YAML configuration files follow the repository's
        docstring contract requirements.

        :returns:
            LintResult for yaml-docstrings
        """
        validator_script = self.repo_root / "scripts" / "validate_docstrings.py"

        if not validator_script.exists():
            return LintResult(
                tool="yaml-docstrings",
                passed=False,
                violations=[],
                error=(
                    f"Docstring validation SKIPPED: validator script not found at "
                    f"{validator_script}. This check was not executed."
                ),
            )

        # Get YAML files to validate
        yaml_files = get_tracked_files(
            ["**/*.yml", "**/*.yaml"], self.repo_root, include_fixtures=self._include_fixtures
        )

        if not yaml_files:
            return LintResult(tool="yaml-docstrings", passed=True, violations=[])

        # Run validator with --language yaml flag
        result = subprocess.run(
            [sys.executable, str(validator_script), "--language", "yaml"]
            + (["--include-fixtures"] if self._include_fixtures else []),
            cwd=self.repo_root,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            return LintResult(tool="yaml-docstrings", passed=True, violations=[])

        violations = []
        error_indicators = ("❌", "ERROR", "violation")
        for line in result.stdout.splitlines():
            stripped = line.strip()
            if (
                stripped
                and not stripped.startswith("Checking")
                and any(indicator in stripped for indicator in error_indicators)
            ):
                violations.append(Violation(tool="yaml-docstrings", file=".", line=None, message=stripped))

        return LintResult(tool="yaml-docstrings", passed=False, violations=violations[:20])  # Limit output
