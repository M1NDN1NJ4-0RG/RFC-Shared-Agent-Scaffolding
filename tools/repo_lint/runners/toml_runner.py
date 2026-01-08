"""TOML language runner for Taplo.

:Purpose:
    Runs Taplo to enforce TOML formatting and style standards
    as defined in docs/contributing/toml-contracts.md.

:Tools:
    - taplo: TOML linter and formatter (required)

:Configuration:
    - taplo.toml: Configuration file at repository root
    - docs/contributing/toml-contracts.md: Canonical contract documentation

:Environment Variables:
    None

:Examples:
    Use this runner::

        from tools.repo_lint.runners.toml_runner import TomlRunner
        runner = TomlRunner()
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


class TomlRunner(Runner):
    """Runner for TOML linting with Taplo."""

    def has_files(self) -> bool:
        """Check if repository has TOML files.

        :returns:
            True if TOML files exist, False otherwise
        """
        # If changed-only mode, check for changed TOML files
        if self._changed_only:
            changed_files = self._get_changed_files(patterns=["*.toml", "**/*.toml"])
            return len(changed_files) > 0

        # Otherwise check all tracked TOML files
        files = get_tracked_files(["**/*.toml"], self.repo_root, include_fixtures=self._include_fixtures)
        return len(files) > 0

    def check_tools(self) -> List[str]:
        """Check which TOML tools are missing.

        :returns:
            List of missing tool names
        """
        required = ["taplo"]
        return [tool for tool in required if not command_exists(tool)]

    def check(self) -> List[LintResult]:
        """Run TOML linting checks.

        :returns:
            List of linting results from Taplo
        """
        self._ensure_tools(["taplo"])

        results = []

        # Apply tool filtering
        if self._should_run_tool("taplo"):
            results.append(self._run_taplo())

        return results

    def fix(self, policy: dict | None = None) -> List[LintResult]:
        """Apply TOML auto-formatting.

        Taplo supports automatic formatting for all rules.

        :param policy: Auto-fix policy dictionary (unused for now)
        :returns:
            List of results after applying fixes
        """
        self._ensure_tools(["taplo"])

        results = []

        # Apply fixes if tool should run
        if self._should_run_tool("taplo"):
            results.append(self._run_taplo(fix=True))

        return results

    def _run_taplo(self, fix: bool = False) -> LintResult:
        """Run Taplo formatter/linter.

        :param fix: If True, apply automatic formatting
        :returns:
            LintResult for Taplo
        """
        # Get all TOML files
        # Note: Taplo handles config exclusions via taplo.toml
        # but we still filter by tracked files to respect git
        toml_files = get_tracked_files(["**/*.toml"], self.repo_root, include_fixtures=self._include_fixtures)

        if not toml_files:
            return LintResult(tool="taplo", passed=True, violations=[])

        # Build command
        if fix:
            # Use `taplo fmt` for formatting
            cmd = ["taplo", "fmt"]
        else:
            # Use `taplo fmt --check` for linting (dry-run)
            cmd = ["taplo", "fmt", "--check"]

        # Add config file (should be at repo root)
        config_file = self.repo_root / "taplo.toml"
        if config_file.exists():
            cmd.extend(["--config", str(config_file)])

        # Add files to lint/format
        cmd.extend(toml_files)

        # Run Taplo
        result = subprocess.run(
            cmd,
            cwd=self.repo_root,
            capture_output=True,
            text=True,
            check=False,
        )

        # Taplo exits 0 on success, 1 on violations
        if result.returncode == 0:
            return LintResult(tool="taplo", passed=True, violations=[])

        # Parse violations from stderr/stdout
        violations = self._parse_taplo_output(result.stdout, result.stderr, toml_files)

        return LintResult(tool="taplo", passed=False, violations=violations)

    def _parse_taplo_output(self, stdout: str, stderr: str, toml_files: List[str]) -> List[Violation]:
        """Parse Taplo output into Violation objects.

        Taplo format --check output:
        - stderr contains: "ERROR taplo:format_files: the file is not properly formatted path=..."
        - When all files pass, no ERROR lines

        :param stdout: Standard output from Taplo
        :param stderr: Standard error from Taplo
        :param toml_files: List of TOML files that were checked
        :returns:
            List of Violation objects
        """
        violations = []

        # Combine stdout and stderr (Taplo uses stderr for errors)
        # Add newline to properly separate lines when combining
        output = stdout + "\n" + stderr

        for line in output.splitlines():
            line = line.strip()

            # Skip info/warning lines
            if (
                not line
                or line.startswith("INFO")
                or line.startswith("WARN")
                or line.startswith("ERROR operation failed")
            ):
                continue

            # Parse error line: "ERROR taplo:format_files: the file is not properly formatted path=..."
            if "ERROR" in line and "not properly formatted" in line and "path=" in line:
                try:
                    # Extract file path from 'path="..."' or 'path=...'
                    path_start = line.find("path=")
                    if path_start != -1:
                        path_part = line[path_start + 5 :].strip()  # Skip 'path='
                        # Remove quotes if present
                        if path_part.startswith('"'):
                            path_end = path_part.find('"', 1)
                            if path_end != -1:
                                file_path = path_part[1:path_end]
                            else:
                                file_path = path_part[1:]
                        else:
                            # No quotes, take until whitespace or end
                            path_end = path_part.find(" ")
                            if path_end != -1:
                                file_path = path_part[:path_end]
                            else:
                                file_path = path_part

                        # Normalize path (remove leading ./)
                        if file_path.startswith("./"):
                            file_path = file_path[2:]

                        violations.append(
                            Violation(
                                tool="taplo",
                                file=file_path,
                                line=None,  # Taplo doesn't provide line numbers in --check mode
                                message="File is not properly formatted according to taplo.toml",
                            )
                        )
                except (ValueError, IndexError):
                    # If parsing fails, skip this line
                    pass

        return violations
