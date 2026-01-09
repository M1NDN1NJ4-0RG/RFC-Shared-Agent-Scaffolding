"""JSON/JSONC language runner for Prettier.

:Purpose:
    Runs Prettier to enforce JSON/JSONC formatting and style standards
    as defined in docs/contributing/json-jsonc-contracts.md.
    Also validates that .json files have required metadata fields.

:Tools:
    - prettier: JSON/JSONC linter and formatter (required)

:Configuration:
    - .prettierrc.json: Configuration file at repository root
    - docs/contributing/json-jsonc-contracts.md: Canonical contract documentation
    - docs/contributing/docstring-contracts/json-jsonc.md: Documentation requirements

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

import json
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
        :rtype: bool
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
        :rtype: List[str]
        """
        required = ["prettier"]
        return [tool for tool in required if not command_exists(tool)]

    def check(self) -> List[LintResult]:
        """Run JSON/JSONC linting checks.

        :returns:
            List of linting results from Prettier and metadata validator
        :rtype: List[LintResult]
        """
        self._ensure_tools(["prettier"])

        results = []

        # Apply tool filtering
        if self._should_run_tool("prettier"):
            results.append(self._run_prettier())

        # Validate JSON metadata (always run, not tool-filtered)
        results.append(self._validate_json_metadata())

        return results

    def fix(self, policy: dict | None = None) -> List[LintResult]:
        """Apply JSON/JSONC auto-formatting.

        Prettier supports automatic formatting for all rules.

        :param policy: Auto-fix policy dictionary (unused for now)
        :returns:
            List of results after applying fixes
        :rtype: List[LintResult]
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
        :rtype: LintResult
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
        :rtype: List[Violation]
        """
        violations = []

        # Combine stdout and stderr
        output = stdout + "\n" + stderr

        for line in output.splitlines():
            line = line.strip()

            # Skip empty lines and status messages
            skip_prefixes = ("Checking formatting", "[warn]", "[error]")
            skip_phrases = ("Code style issues", "files checked")

            if not line or line.startswith(skip_prefixes) or any(phrase in line for phrase in skip_phrases):
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

    def _validate_json_metadata(self) -> LintResult:
        """Validate that .json files have required metadata fields.

        Per docs/contributing/docstring-contracts/json-jsonc.md:
        All .json files MUST have either "$schema" OR "description" at root level.

        :returns:
            LintResult for JSON metadata validation
        :rtype: LintResult
        """
        # Get only .json files (not .jsonc)
        json_files = get_tracked_files(
            ["**/*.json"],
            self.repo_root,
            include_fixtures=self._include_fixtures,
        )

        if not json_files:
            return LintResult(tool="json-metadata", passed=True, violations=[])

        violations = []

        for json_file in json_files:
            file_path = self.repo_root / json_file

            # Skip if file doesn't exist (edge case)
            if not file_path.exists():
                continue

            try:
                # Read and parse JSON
                with open(file_path, encoding="utf-8") as f:
                    data = json.load(f)

                # Must be a dict/object at root level
                if not isinstance(data, dict):
                    violations.append(
                        Violation(
                            tool="json-metadata",
                            file=json_file,
                            line=1,
                            message="JSON file must be an object at root level to contain metadata fields",
                        )
                    )
                    continue

                # Check for required metadata fields
                has_schema = "$schema" in data
                has_description = "description" in data
                has_title = "title" in data  # Some schemas use "title" instead

                if not (has_schema or has_description or has_title):
                    violations.append(
                        Violation(
                            tool="json-metadata",
                            file=json_file,
                            line=1,
                            message=(
                                'Missing required metadata: JSON files must have "$schema", '
                                '"description", or "title" field. '
                                "See docs/contributing/docstring-contracts/json-jsonc.md"
                            ),
                        )
                    )

            except json.JSONDecodeError as e:
                # Invalid JSON - report parsing error
                violations.append(
                    Violation(
                        tool="json-metadata",
                        file=json_file,
                        line=e.lineno if hasattr(e, "lineno") else 1,
                        message=f"Invalid JSON syntax: {e.msg}",
                    )
                )
            except Exception as e:  # pylint: disable=broad-except
                # Other errors (file read errors, etc.)
                violations.append(
                    Violation(
                        tool="json-metadata",
                        file=json_file,
                        line=1,
                        message=f"Error reading file: {str(e)}",
                    )
                )

        passed = len(violations) == 0
        return LintResult(tool="json-metadata", passed=passed, violations=violations)
