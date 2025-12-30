"""PowerShell language runner for PSScriptAnalyzer and docstring validation.

:Purpose:
    Runs all PowerShell linting tools as defined in the repository standards.
    Integrates with existing validate_docstrings.py script.

:Tools:
    - PSScriptAnalyzer: PowerShell script analyzer (via pwsh)
    - validate_docstrings.py: Docstring contract validation
"""

import subprocess
import sys
from typing import List, Optional

from tools.repo_lint.common import LintResult, Violation
from tools.repo_lint.runners.base import Runner, command_exists


class PowerShellRunner(Runner):
    """Runner for PowerShell linting tools."""

    def has_files(self) -> bool:
        """Check if repository has PowerShell files.

        :Returns:
            True if PowerShell files exist, False otherwise
        """
        result = subprocess.run(
            ["git", "ls-files", "**/*.ps1"], cwd=self.repo_root, capture_output=True, text=True, check=False
        )
        return bool(result.stdout.strip())

    def check_tools(self) -> List[str]:
        """Check which PowerShell tools are missing.

        :Returns:
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

        :Returns:
            List of linting results from all PowerShell tools
        """
        self._ensure_tools(["pwsh"])

        results = []
        results.append(self._run_psscriptanalyzer())
        results.append(self._run_docstring_validation())

        return results

    def fix(self, policy: Optional[dict] = None) -> List[LintResult]:
        """Apply PowerShell auto-fixes where possible.

        Note: PSScriptAnalyzer does not have a general auto-fix mode.

        :Returns:
            List of results (runs checks only)
        """
        self._ensure_tools(["pwsh"])

        # PSScriptAnalyzer does not have a general auto-fix mode, so just run checks
        results = []
        results.append(self._run_psscriptanalyzer())
        results.append(self._run_docstring_validation())

        return results

    def _get_powershell_files(self) -> List[str]:
        """Get list of PowerShell files in repository.

        :Returns:
            List of PowerShell file paths (empty list if none found)
        """
        result = subprocess.run(
            ["git", "ls-files", "**/*.ps1"], cwd=self.repo_root, capture_output=True, text=True, check=False
        )
        if not result.stdout.strip():
            return []
        return result.stdout.strip().split("\n")

    def _run_psscriptanalyzer(self) -> LintResult:
        """Run PSScriptAnalyzer.

        :Returns:
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
        """Run PowerShell docstring validation.

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

        ps_files = self._get_powershell_files()
        if not ps_files:
            return LintResult(tool="validate_docstrings", passed=True, violations=[])

        # Run validator for each PowerShell file
        result = subprocess.run(
            [sys.executable, str(validator_script)] + [f"--file={f}" for f in ps_files],
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
