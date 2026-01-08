"""Markdown language runner for markdownlint-cli2.

:Purpose:
    Runs markdownlint-cli2 to enforce Markdown formatting and style standards
    as defined in docs/contributing/markdown-contracts.md.

:Tools:
    - markdownlint-cli2: Markdown linter with auto-fix support (required)

:Configuration:
    - .markdownlint-cli2.jsonc: Configuration file at repository root
    - docs/contributing/markdown-contracts.md: Canonical contract documentation

:Environment Variables:
    None

:Examples:
    Use this runner::

        from tools.repo_lint.runners.markdown_runner import MarkdownRunner
        runner = MarkdownRunner()
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


class MarkdownRunner(Runner):
    """Runner for Markdown linting with markdownlint-cli2."""

    def has_files(self) -> bool:
        """Check if repository has Markdown files.

        :returns:
            True if Markdown files exist, False otherwise
        """
        # If changed-only mode, check for changed Markdown files
        if self._changed_only:
            changed_files = self._get_changed_files(patterns=["*.md", "**/*.md"])
            return len(changed_files) > 0

        # Otherwise check all tracked Markdown files
        files = get_tracked_files(["**/*.md"], self.repo_root, include_fixtures=self._include_fixtures)
        return len(files) > 0

    def check_tools(self) -> List[str]:
        """Check which Markdown tools are missing.

        :returns:
            List of missing tool names
        """
        required = ["markdownlint-cli2"]
        return [tool for tool in required if not command_exists(tool)]

    def check(self) -> List[LintResult]:
        """Run Markdown linting checks.

        :returns:
            List of linting results from markdownlint-cli2
        """
        self._ensure_tools(["markdownlint-cli2"])

        results = []

        # Apply tool filtering
        if self._should_run_tool("markdownlint-cli2"):
            results.append(self._run_markdownlint())

        return results

    def fix(self, policy: dict | None = None) -> List[LintResult]:
        """Apply Markdown auto-fixes where possible.

        markdownlint-cli2 supports automatic fixing for many rules
        (trailing spaces, heading spacing, list formatting, etc.).

        :param policy: Auto-fix policy dictionary (unused for now)
        :returns:
            List of results after applying fixes
        """
        self._ensure_tools(["markdownlint-cli2"])

        results = []

        # Apply fixes if tool should run
        if self._should_run_tool("markdownlint-cli2"):
            results.append(self._run_markdownlint(fix=True))

        return results

    def _run_markdownlint(self, fix: bool = False) -> LintResult:
        """Run markdownlint-cli2.

        :param fix: If True, apply automatic fixes
        :returns:
            LintResult for markdownlint-cli2
        """
        # Get all Markdown files
        # Note: markdownlint-cli2 handles exclusions via .markdownlint-cli2.jsonc
        # but we still filter by tracked files to respect git
        md_files = get_tracked_files(["**/*.md"], self.repo_root, include_fixtures=self._include_fixtures)

        if not md_files:
            return LintResult(tool="markdownlint-cli2", passed=True, violations=[])

        # Build command
        cmd = ["markdownlint-cli2"]
        if fix:
            cmd.append("--fix")

        # Add config file (should be at repo root)
        config_file = self.repo_root / ".markdownlint-cli2.jsonc"
        if config_file.exists():
            cmd.extend(["--config", str(config_file)])

        # Add files to lint
        cmd.extend(md_files)

        # Run markdownlint-cli2
        result = subprocess.run(
            cmd,
            cwd=self.repo_root,
            capture_output=True,
            text=True,
            check=False,
        )

        # markdownlint-cli2 exits 0 on success, 1 on violations
        if result.returncode == 0:
            return LintResult(tool="markdownlint-cli2", passed=True, violations=[])

        # Parse violations from stdout
        violations = self._parse_markdownlint_output(result.stdout, result.stderr)

        return LintResult(tool="markdownlint-cli2", passed=False, violations=violations)

    def _parse_markdownlint_output(self, stdout: str, stderr: str) -> List[Violation]:
        """Parse markdownlint-cli2 output into Violation objects.

        markdownlint-cli2 output format:
        file:line:column MD### Rule message

        Example:
        README.md:7:81 MD013/line-length Line length [Expected: 120; Actual: 185]

        :param stdout: Standard output from markdownlint-cli2
        :param stderr: Standard error from markdownlint-cli2
        :returns:
            List of Violation objects
        """
        violations = []

        # Combine stdout and stderr (markdownlint-cli2 may use either)
        output = stdout + stderr

        for line in output.splitlines():
            line = line.strip()

            # Skip summary lines and empty lines
            if (
                not line
                or line.startswith("markdownlint-cli2")
                or line.startswith("Finding:")
                or line.startswith("Linting:")
                or line.startswith("Summary:")
            ):
                continue

            # Try to parse violation line: file:line:column error MD### message
            # Example: README.md:7:81 error MD013/line-length Line length [Expected: 120; Actual: 185]
            if ":" in line and ("error" in line or "warning" in line):
                try:
                    # Split on first colon to get file
                    parts = line.split(":", 3)
                    if len(parts) >= 4:
                        file_path = parts[0]
                        line_number = parts[1]
                        # Rest is the message (skip column number)
                        message = parts[3].strip()

                        violations.append(
                            Violation(
                                tool="markdownlint-cli2",
                                file=file_path,
                                line=int(line_number) if line_number.isdigit() else None,
                                message=message,
                            )
                        )
                except (ValueError, IndexError):
                    # If parsing fails, include the raw line as a generic violation
                    violations.append(Violation(tool="markdownlint-cli2", file=".", line=None, message=line))

        return violations
