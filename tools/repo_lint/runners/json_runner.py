"""JSON/JSONC language runner for Prettier.

:Purpose:
    Runs Prettier to enforce JSON/JSONC formatting and style standards
    as defined in docs/contributing/json-jsonc-contracts.md.

:Tools:
    - prettier: JSON/JSONC linter and formatter (required)

:Configuration:
    - .prettierrc.json: Configuration file at repository root
    - docs/contributing/json-jsonc-contracts.md: Canonical contract documentation

:Environment Variables:
    None

:Examples:
    Use this runner::

        from tools.repo_lint.runners.json_runner import JsonRunner
        runner = JsonRunner()
        results = runner.check()

:Exit Codes:
    Returns LintResult objects, not exit codes directly:
    - 0: Success (LintResult.passed = True)
    - 1: Violations found (LintResult.passed = False)
"""

from __future__ import annotations

import subprocess
from typing import List

from tools.repo_lint.common import LintResult, Violation
from tools.repo_lint.runners.base import Runner, command_exists, get_tracked_files


class JsonRunner(Runner):
    """Runner for JSON/JSONC linting with Prettier."""

    def has_files(self) -> bool:
        """Check if repository has JSON/JSONC files.

        :returns:
            True if JSON/JSONC files exist, False otherwise
        """
        # If changed-only mode, check for changed JSON/JSONC files
        if self._changed_only:
            changed_files = self._get_changed_files(patterns=["*.json", "*.jsonc", "**/*.json", "**/*.jsonc"])
            return len(changed_files) > 0

        # Otherwise check all tracked JSON/JSONC files
        files = get_tracked_files(
            ["**/*.json", "**/*.jsonc"],
            self.repo_root,
            include_fixtures=self._include_fixtures,
        )
        return len(files) > 0

    def check_tools(self) -> List[str]:
        """Check which JSON/JSONC tools are missing.

        :returns:
            List of missing tool names
        """
        required = ["prettier"]
        return [tool for tool in required if not command_exists(tool)]

    def check(self) -> List[LintResult]:
        """Run JSON/JSONC linting checks.

        :returns:
            List of linting results from Prettier
        """
        self._ensure_tools(["prettier"])

        results = []

        # Apply tool filtering
        if self._should_run_tool("prettier"):
            results.append(self._run_prettier())

        return results

    def fix(self, policy: dict | None = None) -> List[LintResult]:
        """Apply JSON/JSONC auto-formatting.

        Prettier supports automatic formatting for all rules.

        :param policy: Auto-fix policy dictionary (unused for now)
        :returns:
            List of results after applying fixes
        """
        self._ensure_tools(["prettier"])

        results = []

        # Apply fixes if tool should run
        if self._should_run_tool("prettier"):
            results.append(self._run_prettier(fix=True))

        return results

    def _run_prettier(self, fix: bool = False) -> LintResult:
        """Run Prettier formatter/linter.

        :param fix: If True, apply automatic formatting
        :returns:
            LintResult for Prettier
        """
        # Get all JSON/JSONC files
        json_files = get_tracked_files(
            ["**/*.json", "**/*.jsonc"],
            self.repo_root,
            include_fixtures=self._include_fixtures,
        )

        if not json_files:
            return LintResult(tool="prettier", passed=True, violations=[])

        # Build command
        if fix:
            # Use `prettier --write` for formatting
            cmd = ["prettier", "--write"]
        else:
            # Use `prettier --check` for linting (dry-run)
            cmd = ["prettier", "--check"]

        # Add config file reference (prettier auto-discovers .prettierrc.json)
        config_file = self.repo_root / ".prettierrc.json"
        if config_file.exists():
            cmd.extend(["--config", str(config_file)])

        # Prettier accepts multiple files
        cmd.extend(json_files)

        # Run Prettier
        result = subprocess.run(
            cmd,
            cwd=self.repo_root,
            capture_output=True,
            text=True,
            check=False,
        )

        # Prettier exits 0 on success, 1 on violations
        if result.returncode == 0:
            return LintResult(tool="prettier", passed=True, violations=[])

        # Parse violations from stdout
        violations = self._parse_prettier_output(result.stdout, result.stderr)

        return LintResult(tool="prettier", passed=False, violations=violations)

    def _parse_prettier_output(self, stdout: str, stderr: str) -> List[Violation]:
        """Parse Prettier output into Violation objects.

        Prettier --check output:
        - Lists files that need formatting, one per line
        - Example: "Checking formatting...
                    path/to/file.json
                    path/to/other.jsonc
                    [warn] Code style issues found in 2 files."

        :param stdout: Standard output from Prettier
        :param stderr: Standard error from Prettier
        :returns:
            List of Violation objects
        """
        violations = []

        # Combine stdout and stderr
        output = stdout + "\n" + stderr

        for line in output.splitlines():
            line = line.strip()

            # Skip empty lines, status messages, and summary lines
            if (
                not line
                or line.startswith("Checking formatting")
                or line.startswith("[warn]")
                or line.startswith("[error]")
                or "Code style issues" in line
                or "files checked" in line
            ):
                continue

            # Lines containing file paths (look for .json or .jsonc extension)
            if line.endswith(".json") or line.endswith(".jsonc"):
                violations.append(
                    Violation(
                        tool="prettier",
                        file=line,
                        line=None,  # Prettier doesn't provide line numbers in --check mode
                        message="File is not properly formatted according to .prettierrc.json",
                    )
                )

        return violations
