"""Rust language runner for rustfmt, clippy, and docstring validation.

:Purpose:
    Runs all Rust linting and formatting tools as defined in the repository
    standards. Integrates with existing validate_docstrings.py script.

:Tools:
    - rustfmt: Code formatter (official Rust style)
    - clippy: Comprehensive linter for Rust (with JSON output parsing)
    - validate_docstrings.py: Docstring contract validation

:Status:
    COMPLETE - Full implementation with enhanced clippy parsing and docstring validation.

:Environment Variables:
    None

:Examples:
    Use this runner::

        from tools.repo_lint.runners.rust_runner import RustRunner
        runner = RustRunner()
        results = runner.check()

:Exit Codes:
    Returns LintResult objects, not exit codes directly:
    - 0: Success (LintResult.passed = True)
    - 1: Violations found (LintResult.passed = False)
"""

import json
import subprocess
from typing import List, Optional

from tools.repo_lint.common import LintResult, Violation
from tools.repo_lint.runners.base import Runner, command_exists


class RustRunner(Runner):
    """Runner for Rust linting and formatting tools.

    :Status:
        Complete implementation with enhanced clippy JSON parsing
        and integrated docstring validation.
    """

    def has_files(self) -> bool:
        """Check if repository has Rust files.

        :returns:
            True if Rust files exist, False otherwise
        """
        result = subprocess.run(
            ["git", "ls-files", "**/*.rs"], cwd=self.repo_root, capture_output=True, text=True, check=False
        )
        return bool(result.stdout.strip())

    def check_tools(self) -> List[str]:
        """Check which Rust tools are missing.

        :returns:
            List of missing tool names
        """
        required = ["cargo", "rustfmt", "clippy-driver"]
        missing = []
        for tool in required:
            # Check for cargo and rustfmt directly
            if tool in ["cargo", "rustfmt"]:
                if not command_exists(tool):
                    missing.append(tool)
            # For clippy, check if cargo clippy works
            elif tool == "clippy-driver":
                result = subprocess.run(
                    ["cargo", "clippy", "--version"],
                    cwd=self.repo_root,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if result.returncode != 0:
                    missing.append("clippy")
        return missing

    def check(self) -> List[LintResult]:
        """Run all Rust linting checks.

        :returns:
            List of linting results from all Rust tools
        """
        self._ensure_tools(["cargo"])

        results = []
        results.append(self._run_rustfmt_check())
        results.append(self._run_clippy())
        results.append(self._run_docstring_validation())

        return results

    def fix(self, policy: Optional[dict] = None) -> List[LintResult]:
        """Apply Rust auto-fixes where possible.

        :param policy: Auto-fix policy dictionary (unused for Rust)
        :returns:
            List of linting results after fixes applied
        """
        self._ensure_tools(["cargo"])

        results = []

        rust_dir = self.repo_root / "rust"
        if not rust_dir.exists():
            # No rust directory - skip silently
            if self.verbose:
                print("  No rust/ directory found, skipping rustfmt fix")
            return [LintResult(tool="rustfmt", passed=True, violations=[])]

        # Run rustfmt to format code
        rustfmt_result = subprocess.run(["cargo", "fmt"], cwd=rust_dir, capture_output=True, text=True, check=False)

        if rustfmt_result.returncode != 0:
            results.append(
                LintResult(
                    tool="rustfmt",
                    passed=False,
                    violations=[
                        Violation(
                            tool="rustfmt",
                            file=".",
                            line=None,
                            message=f"rustfmt failed: {rustfmt_result.stderr}",
                        )
                    ],
                )
            )
        else:
            results.append(LintResult(tool="rustfmt", passed=True, violations=[]))

        # Re-run checks after formatting
        results.append(self._run_clippy())

        return results

    def _run_rustfmt_check(self) -> LintResult:
        """Run rustfmt in check mode.

        :returns:
            LintResult for rustfmt
        """
        rust_dir = self.repo_root / "rust"
        if not rust_dir.exists():
            # No rust directory - skip silently
            if self.verbose:
                print("  No rust/ directory found, skipping rustfmt check")
            return LintResult(tool="rustfmt", passed=True, violations=[])

        result = subprocess.run(
            ["cargo", "fmt", "--", "--check"], cwd=rust_dir, capture_output=True, text=True, check=False
        )

        if result.returncode == 0:
            return LintResult(tool="rustfmt", passed=True, violations=[])

        violations = []
        # rustfmt --check outputs files that need formatting
        for line in result.stdout.splitlines():
            if line.strip():
                violations.append(Violation(tool="rustfmt", file=".", line=None, message=line.strip()))

        return LintResult(tool="rustfmt", passed=False, violations=violations[:20])  # Limit output

    def _run_clippy(self) -> LintResult:
        """Run clippy linter with JSON output for structured parsing.

        :returns:
            LintResult for clippy with detailed file, line, and message information
        """
        rust_dir = self.repo_root / "rust"
        if not rust_dir.exists():
            # No rust directory - skip silently
            if self.verbose:
                print("  No rust/ directory found, skipping clippy check")
            return LintResult(tool="clippy", passed=True, violations=[])

        # Run clippy with JSON output for structured parsing
        result = subprocess.run(
            [
                "cargo",
                "clippy",
                "--all-targets",
                "--all-features",
                "--message-format=json",
                "--",
                "-D",
                "warnings",
            ],
            cwd=rust_dir,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            return LintResult(tool="clippy", passed=True, violations=[])

        violations = []
        # Parse JSON output for structured violations
        for line in result.stdout.splitlines():
            if not line.strip():
                continue
            
            violation = self._parse_clippy_json_line(line, rust_dir)
            if violation:
                violations.append(violation)

        return LintResult(tool="clippy", passed=False, violations=violations[:50])  # Limit output

    def _parse_clippy_json_line(self, line: str, rust_dir) -> Optional[Violation]:
        """Parse a single line of clippy JSON output.

        :param line: JSON line from clippy output
        :param rust_dir: Path to rust directory for path relativization
        :returns: Violation object if line contains a warning/error, None otherwise
        """
        try:
            msg = json.loads(line)
            # Only process compiler messages (not build artifacts)
            if msg.get("reason") != "compiler-message":
                return None

            message_obj = msg.get("message", {})
            # Skip non-warning/non-error messages
            level = message_obj.get("level", "")
            if level not in ["warning", "error"]:
                return None

            # Extract location information
            spans = message_obj.get("spans", [])
            primary_span = next((s for s in spans if s.get("is_primary")), None)

            # Make file path relative to rust/ directory if it's absolute
            # Note: Clippy may return absolute paths; we normalize them to be relative to rust/
            if primary_span:
                file_path = primary_span.get("file_name", "unknown")
                line_num = primary_span.get("line_start")
                
                if file_path.startswith(str(rust_dir)):
                    # Path is absolute and within rust_dir - make it relative
                    try:
                        file_path = file_path[len(str(rust_dir)) + 1 :]
                    except (ValueError, IndexError):
                        pass  # Keep original path if relativization fails
                elif file_path.startswith("/"):
                    # Path is absolute but not within rust_dir
                    # This shouldn't normally happen, but keep the path as-is for debugging
                    # The absolute path will help developers locate the issue
                    pass
            else:
                file_path = "unknown"
                line_num = None

            # Extract message text
            msg_text = message_obj.get("message", "clippy warning")

            # Add lint name if available
            code = message_obj.get("code", {})
            if code and "code" in code:
                lint_name = code["code"]
                msg_text = f"{lint_name}: {msg_text}"

            return Violation(tool="clippy", file=file_path, line=line_num, message=msg_text)

        except (json.JSONDecodeError, KeyError, TypeError):
            # Fallback to plain text parsing if JSON fails
            if "warning:" in line or "error:" in line:
                # Try to extract file information from text format
                # Format typically: "warning: message\n  --> file.rs:line:col"
                file_info = "unknown"
                if "-->" in line:
                    parts = line.split("-->")
                    if len(parts) > 1:
                        file_info = parts[1].strip().split(":")[0]
                return Violation(tool="clippy", file=file_info, line=None, message=line.strip())
            return None

    def _run_docstring_validation(self) -> LintResult:
        """Run Rust docstring validation using validate_docstrings.py.

        :returns:
            LintResult for docstring validation
        """
        # Check if rust directory exists
        rust_dir = self.repo_root / "rust"
        if not rust_dir.exists():
            if self.verbose:
                print("  No rust/ directory found, skipping Rust docstring validation")
            return LintResult(tool="rust-docstrings", passed=True, violations=[])

        # Call validate_docstrings.py with --language rust
        validator_script = self.repo_root / "scripts" / "validate_docstrings.py"
        if not validator_script.exists():
            if self.verbose:
                print("  Docstring validator script not found, skipping")
            return LintResult(tool="rust-docstrings", passed=True, violations=[])

        result = subprocess.run(
            ["python3", str(validator_script), "--language", "rust"],
            cwd=self.repo_root,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            return LintResult(tool="rust-docstrings", passed=True, violations=[])

        violations = []
        # Parse validator output (format: "FILE: Missing docstring for SYMBOL")
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line or line.startswith("===") or line.startswith("Checking"):
                continue

            # Parse violation format
            # Example: "rust/src/main.rs: Missing docstring for function 'helper'"
            if ":" in line:
                parts = line.split(":", 1)
                file_path = parts[0].strip()
                message = parts[1].strip() if len(parts) > 1 else line

                violations.append(
                    Violation(
                        tool="rust-docstrings",
                        file=file_path,
                        line=None,
                        message=message,
                    )
                )
            else:
                violations.append(
                    Violation(
                        tool="rust-docstrings",
                        file="unknown",
                        line=None,
                        message=line,
                    )
                )

        return LintResult(tool="rust-docstrings", passed=False, violations=violations)
