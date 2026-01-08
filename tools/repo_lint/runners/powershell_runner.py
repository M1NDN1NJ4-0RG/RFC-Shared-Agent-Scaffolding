"""PowerShell language runner for PSScriptAnalyzer and docstring validation.

:Purpose:
    Runs all PowerShell linting tools as defined in the repository standards.
    Uses internal docstring validation module.

:Tools:
    - PSScriptAnalyzer: PowerShell script analyzer (via pwsh)
    - Internal docstring validator: Docstring contract validation

:Environment Variables:
    None

:Examples:
    Use this runner::

        from tools.repo_lint.runners.powershell_runner import PowerShellRunner
        runner = PowerShellRunner()
        results = runner.check()

:Exit Codes:
    Returns LintResult objects, not exit codes directly:
    - 0: Success (LintResult.passed = True)
    - 1: Violations found (LintResult.passed = False)
"""

from __future__ import annotations

import subprocess
from typing import List

from tools.repo_lint.common import LintResult, Violation, convert_validation_errors_to_violations, filter_excluded_paths
from tools.repo_lint.docstrings import validate_files
from tools.repo_lint.runners.base import Runner, command_exists, get_tracked_files


class PowerShellRunner(Runner):
    """Runner for PowerShell linting tools."""

    def has_files(self) -> bool:
        """Check if repository has PowerShell files.

        :returns:
            True if PowerShell files exist, False otherwise
        """
        # If changed-only mode, check for changed PowerShell files
        if self._changed_only:
            changed_files = self._get_changed_files(patterns=["*.ps1", "**/*.ps1"])
            return len(changed_files) > 0

        # Otherwise check all tracked PowerShell files
        files = get_tracked_files(["**/*.ps1"], self.repo_root, include_fixtures=self._include_fixtures)
        return len(files) > 0

    def check_tools(self) -> List[str]:
        """Check which PowerShell tools are missing.

        :returns:
            List of missing tool names
        """
        missing = []

        if not command_exists("pwsh"):
            missing.append("pwsh")
        else:
            # Check if PSScriptAnalyzer module is available
            result = subprocess.run(
                [
                    "pwsh",
                    "-NoProfile",
                    "-NonInteractive",
                    "-Command",
                    "Get-Module -ListAvailable PSScriptAnalyzer | Select-Object -First 1",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            if not result.stdout.strip():
                missing.append("PSScriptAnalyzer")

        return missing

    def check(self) -> List[LintResult]:
        """Run all PowerShell linting checks.

        :returns:
            List of linting results from all PowerShell tools
        """
        self._ensure_tools(["pwsh"])

        results = []

        # Apply tool filtering
        if self._should_run_tool("PSScriptAnalyzer"):
            results.append(self._run_psscriptanalyzer())

        if self._should_run_tool("validate_docstrings"):
            results.append(self._run_docstring_validation())

        return results

    def fix(self, policy: dict | None = None) -> List[LintResult]:
        """Apply PowerShell auto-fixes where possible.

        Note: PSScriptAnalyzer does not have a general auto-fix mode.


        :param policy: Auto-fix policy dictionary (unused)
        :returns:
            List of results (runs checks only)
        """
        self._ensure_tools(["pwsh"])

        # PSScriptAnalyzer does not have a general auto-fix mode, so just run checks
        results = []
        results.append(self._run_psscriptanalyzer())
        results.append(self._run_docstring_validation())

        return results

    def _get_powershell_files(self) -> List[str]:
        """Get list of PowerShell files in repository, excluding test fixtures.

        :returns:
            List of PowerShell file paths (empty list if none found)
        """
        all_files = get_tracked_files(["**/*.ps1"], self.repo_root, include_fixtures=self._include_fixtures)
        return filter_excluded_paths(all_files)

    def _run_psscriptanalyzer(self) -> LintResult:
        """Run PSScriptAnalyzer.

        :returns:
            LintResult for PSScriptAnalyzer
        """
        ps_files = self._get_powershell_files()
        if not ps_files:
            return LintResult(tool="PSScriptAnalyzer", passed=True, violations=[])

        # Run PSScriptAnalyzer on each file
        violations = []
        for ps_file in ps_files:
            # Use -File parameter to safely pass the script path
            result = subprocess.run(
                [
                    "pwsh",
                    "-NoProfile",
                    "-NonInteractive",
                    "-Command",
                    "Invoke-ScriptAnalyzer -Path $args[0] -Severity Warning,Error",
                    ps_file,
                ],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=False,
            )

            # Parse output for violations
            if result.stdout.strip():
                for line in result.stdout.splitlines():
                    if line.strip():
                        violations.append(
                            Violation(tool="PSScriptAnalyzer", file=ps_file, line=None, message=line.strip())
                        )

        if not violations:
            return LintResult(tool="PSScriptAnalyzer", passed=True, violations=[])

        return LintResult(tool="PSScriptAnalyzer", passed=False, violations=violations[:20])  # Limit output

    def _run_docstring_validation(self) -> LintResult:
        """Run PowerShell docstring validation using internal module.

        :returns:
            LintResult for docstring validation
        """
        ps_files = self._get_powershell_files()
        if not ps_files:
            return LintResult(tool="powershell-docstrings", passed=True, violations=[])

        # Use internal validator module
        errors = validate_files(ps_files, language="powershell")

        if not errors:
            return LintResult(tool="powershell-docstrings", passed=True, violations=[])

        # Convert ValidationError objects to Violation objects using shared helper
        violations = convert_validation_errors_to_violations(errors, "powershell-docstrings")

        return LintResult(tool="powershell-docstrings", passed=False, violations=violations)
