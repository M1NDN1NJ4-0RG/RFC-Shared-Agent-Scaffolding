"""Python language runner for Black, Ruff, Pylint, and docstring validation.

:Purpose:
    Runs all Python linting and formatting tools as defined in the repository
    standards. Integrates with existing validate_docstrings.py script.

:Tools:
    - Black: Code formatter (PEP 8 compliant)
    - Ruff: Fast Python linter (replaces Flake8)
    - Pylint: Comprehensive static analysis
    - validate_docstrings.py: Docstring contract validation

:Environment Variables:
    None

:Examples:
    Use this runner::

        from tools.repo_lint.runners.python_runner import PythonRunner
        runner = PythonRunner()
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
from tools.repo_lint.runners.base import Runner, command_exists, get_tracked_files


class PythonRunner(Runner):
    """Runner for Python linting and formatting tools."""

    def has_files(self) -> bool:
        """Check if repository has Python files.

        :returns:
            True if Python files exist, False otherwise
        """
        # If changed-only mode, check for changed Python files
        if self._changed_only:
            changed_files = self._get_changed_files(patterns=["*.py", "**/*.py"])
            return len(changed_files) > 0

        # Otherwise check all tracked Python files
        files = get_tracked_files(["**/*.py"], self.repo_root)
        return len(files) > 0

    def _is_ruff_context_line(self, line: str) -> bool:
        """Check if a line is a ruff context line (not an actual violation).

        :param line: Stripped line from ruff output
        :returns: True if this is a context line to skip
        """
        # Skip various ruff context/formatting lines
        if line.startswith(("|", "-->", "=", "help:")):
            return True
        # Skip line-number-only lines
        if line.replace(" ", "").replace("|", "").isdigit():
            return True
        # Skip caret/pointer lines
        if all(c in "^ " for c in line):
            return True
        return False

    def _parse_lint_output(self, line: str) -> dict:
        """Parse linter output to extract file, line, and message.

        Handles multiple formats:
        - path:line:col: code message (ruff, pylint)
        - path:line: code message
        - message only (fallback)

        :param line: Raw linter output line
        :returns: Dict with 'file' (basename), 'line' (int or None), 'message' (str)
        """
        import os

        # Try to parse path:line:col: format (ruff, pylint)
        if ":" in line:
            parts = line.split(":", 3)
            if len(parts) >= 3:
                # Check if second part is a number (line number)
                try:
                    file_path = parts[0].strip()
                    line_num = int(parts[1].strip())
                    # parts[2] could be column or part of message
                    # If parts[2] is numeric, it's column; otherwise part of message
                    try:
                        int(parts[2].strip())
                        # Has column number, message starts at parts[3]
                        message = parts[3].strip() if len(parts) > 3 else line
                    except ValueError:
                        # No column, parts[2] is start of message
                        message = ":".join(parts[2:]).strip()

                    # Extract basename from file path
                    file_basename = os.path.basename(file_path) if file_path else "."

                    return {
                        "file": file_basename,
                        "line": line_num,
                        "message": message,
                    }
                except (ValueError, IndexError):
                    pass

        # Fallback: couldn't parse, return original line as message
        return {
            "file": ".",
            "line": None,
            "message": line,
        }

    def check_tools(self) -> List[str]:
        """Check which Python tools are missing.

        :returns:
            List of missing tool names
        """
        required = ["black", "ruff", "pylint"]
        return [tool for tool in required if not command_exists(tool)]

    def check(self) -> List[LintResult]:
        """Run all Python linting checks.

        :returns:
            List of linting results from all Python tools
        """
        self._ensure_tools(["black", "ruff", "pylint"])

        results = []

        # Apply tool filtering: only run tools that pass the filter
        if self._should_run_tool("black"):
            results.append(self._run_black_check())

        if self._should_run_tool("ruff"):
            results.append(self._run_ruff_check())

        if self._should_run_tool("pylint"):
            results.append(self._run_pylint())

        if self._should_run_tool("validate_docstrings"):
            results.append(self._run_docstring_validation())

        return results

    def fix(self, policy: Optional[dict] = None) -> List[LintResult]:
        """Apply Python formatters and safe auto-fixes.

        Per Phase 0 Item 0.9.1: Apply Black formatting and Ruff safe fixes.
        Per Phase 6 Item 6.5.6: Consult auto-fix policy before running fixes.

        :param policy: Auto-fix policy dictionary (deny-by-default)
        :returns: List of results after applying fixes
        """
        self._ensure_tools(["black", "ruff", "pylint"])

        results = []

        # Default policy if none provided (backwards compatibility)
        # Note: Empty policy denies all fixes. This is intentional during transition
        # to ensure fixes are only run when policy is explicitly loaded.
        if policy is None:
            policy = {"allowed_categories": []}

        # Apply Black formatting (if allowed by policy AND tool filter)
        if self._should_run_tool("black") and is_category_allowed(policy, "FORMAT.BLACK"):
            black_result = self._run_black_fix()
            results.append(black_result)
        else:
            if self.verbose:
                if not self._should_run_tool("black"):
                    print("  ⊘ Skipping Black (filtered out)")
                else:
                    print("  ⊘ Skipping Black (denied by policy)")
            black_result = LintResult(tool="black", passed=True, violations=[])
            results.append(black_result)

        # Apply Ruff safe fixes (if allowed by policy AND tool filter)
        if self._should_run_tool("ruff") and is_category_allowed(policy, "LINT.RUFF.SAFE"):
            ruff_result = self._run_ruff_fix()
            results.append(ruff_result)
        else:
            if self.verbose:
                if not self._should_run_tool("ruff"):
                    print("  ⊘ Skipping Ruff safe fixes (filtered out)")
                else:
                    print("  ⊘ Skipping Ruff safe fixes (denied by policy)")
            ruff_result = LintResult(tool="ruff", passed=True, violations=[])
            results.append(ruff_result)

        # Re-run checks only if both Black and Ruff succeeded
        if black_result.passed and ruff_result.passed:
            results.append(self._run_pylint())
            results.append(self._run_docstring_validation())

        return results

    def _run_black_check(self) -> LintResult:
        """Run Black in check mode.

        :returns:
            LintResult for Black check
        """
        result = subprocess.run(
            ["black", "--check", "--diff", "."], cwd=self.repo_root, capture_output=True, text=True, check=False
        )

        if result.returncode == 0:
            return LintResult(tool="black", passed=True, violations=[])

        # Parse Black output to extract violations
        violations = []
        if result.stdout:
            # Black outputs diffs, we'll create a summary violation
            violations.append(
                Violation(
                    tool="black",
                    file=".",
                    line=None,
                    message=(
                        "Code formatting does not match Black style. "
                        "Run 'python3 -m tools.repo_lint fix' to auto-format."
                    ),
                )
            )

        return LintResult(tool="black", passed=False, violations=violations)

    def _run_black_fix(self) -> LintResult:
        """Run Black to fix formatting.

        :returns:
            LintResult for Black fix operation
        """
        result = subprocess.run(["black", "."], cwd=self.repo_root, capture_output=True, text=True, check=False)

        if result.returncode == 0:
            return LintResult(tool="black", passed=True, violations=[])

        return LintResult(
            tool="black", passed=False, violations=[], error=f"Black failed with exit code {result.returncode}"
        )

    def _parse_ruff_output(self, stdout: str, context: str = "check") -> List[Violation]:
        """Parse Ruff output into violations.

        :param stdout: Ruff command stdout output
        :param context: Context for unsafe fixes message ('check' or 'fix')
        :returns: List of parsed violations
        """
        violations = []
        unsafe_msg = (
            "(Review before applying with --unsafe-fixes)"
            if context == "check"
            else "(unsafe fixes not applied automatically)"
        )

        for line in stdout.splitlines():
            if line.strip():
                if "hidden fixes can be enabled with the `--unsafe-fixes` option" in line:
                    violations.append(
                        Violation(
                            tool="ruff",
                            file=".",
                            line=None,
                            message=f"⚠️  {line.strip()} {unsafe_msg}",
                        )
                    )
                elif not line.startswith("Found") and not line.startswith("[*]"):
                    # Ruff output format: path:line:col: code message
                    # Example: tools/repo_lint/ui/reporter.py:447:36: F541 [*] f-string without any placeholders
                    # Skip context lines (start with |, -->, help:, numbers only, etc.)
                    stripped = line.strip()
                    if not self._is_ruff_context_line(stripped):
                        parsed = self._parse_lint_output(stripped)
                        # Only add if we successfully parsed a file and line
                        if parsed["file"] != "." or parsed["line"] is not None:
                            violations.append(
                                Violation(
                                    tool="ruff",
                                    file=parsed["file"],
                                    line=parsed["line"],
                                    message=parsed["message"],
                                )
                            )

        return violations

    def _run_ruff_check(self) -> LintResult:
        """Run Ruff linter in check-only mode (non-mutating).

        Per Phase 0 Item 0.9.1: repo-lint check MUST be non-mutating.

        :returns:
            LintResult for Ruff check
        """
        result = subprocess.run(
            ["ruff", "check", ".", "--no-fix"], cwd=self.repo_root, capture_output=True, text=True, check=False
        )

        if result.returncode == 0:
            return LintResult(tool="ruff", passed=True, violations=[])

        violations = self._parse_ruff_output(result.stdout, context="check")
        return LintResult(tool="ruff", passed=False, violations=violations)

    def _run_ruff_fix(self) -> LintResult:
        """Run Ruff linter with safe auto-fixes.

        Per Phase 0 Item 0.9.1: repo-lint fix may apply SAFE fixes only.

        :returns:
            LintResult for Ruff fix operation
        """
        # Apply safe fixes only (no --unsafe-fixes flag)
        result = subprocess.run(
            ["ruff", "check", ".", "--fix"], cwd=self.repo_root, capture_output=True, text=True, check=False
        )

        if result.returncode == 0:
            return LintResult(tool="ruff", passed=True, violations=[])

        violations = self._parse_ruff_output(result.stdout, context="fix")
        return LintResult(tool="ruff", passed=False, violations=violations)

    def _run_pylint(self) -> LintResult:
        """Run Pylint.

        :returns:
            LintResult for Pylint check
        """
        # Get all Python files, excluding test fixtures (respecting changed-only mode)
        if self._changed_only:
            py_files = self._get_changed_files(patterns=["*.py", "**/*.py"])
        else:
            py_files = get_tracked_files(["**/*.py"], self.repo_root)

        if not py_files:
            return LintResult(tool="pylint", passed=True, violations=[])

        # Run pylint
        result = subprocess.run(
            ["pylint"] + py_files,
            cwd=self.repo_root,
            capture_output=True,
            text=True,
            check=False,
        )

        # Pylint exit codes: 0=success, 1-31=violations/errors
        if result.returncode == 0:
            return LintResult(tool="pylint", passed=True, violations=[])

        violations = []
        for line in result.stdout.splitlines():
            if line.strip() and not line.startswith("----") and not line.startswith("Your code"):
                # Parse the pylint output
                # Format: path:line:col: code: message
                # or module banner: ************* Module module.name
                if line.strip().startswith("*"):
                    # Module banner - skip or could be used for context
                    continue
                parsed = self._parse_lint_output(line.strip())
                violations.append(
                    Violation(
                        tool="pylint",
                        file=parsed["file"],
                        line=parsed["line"],
                        message=parsed["message"],
                    )
                )

        return LintResult(tool="pylint", passed=False, violations=violations[:20])  # Limit output

    def _run_docstring_validation(self) -> LintResult:
        """Run Python docstring validation.

        :returns:
            LintResult for docstring validation
        """
        validator_script = self.repo_root / "scripts" / "validate_docstrings.py"

        if not validator_script.exists():
            return LintResult(
                tool="validate_docstrings",
                passed=False,
                violations=[],
                error=f"Docstring validation SKIPPED: validator script not found at {validator_script}. "
                "This check was not executed.",
            )

        result = subprocess.run(
            [sys.executable, str(validator_script), "--language", "python"],
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
                # Parse docstring validator output
                # Format can be:
                # ❌ /path/to/file.py:123
                # ❌ /path/to/file.py
                # ❌ Validation FAILED: ...
                parsed = self._parse_lint_output(line.strip())
                violations.append(
                    Violation(
                        tool="validate_docstrings",
                        file=parsed["file"],
                        line=parsed["line"],
                        message=parsed["message"],
                    )
                )

        return LintResult(tool="validate_docstrings", passed=False, violations=violations[:20])  # Limit output
