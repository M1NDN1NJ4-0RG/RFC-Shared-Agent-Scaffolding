"""Rust language runner for rustfmt, clippy, and docstring validation.

:Purpose:
    Runs all Rust linting and formatting tools as defined in the repository
    standards. Integrates with existing validate_docstrings.py script.

:Tools:
    - rustfmt: Code formatter (official Rust style)
    - clippy: Comprehensive linter for Rust
    - validate_docstrings.py: Docstring contract validation

:Status:
    STUB IMPLEMENTATION - Basic structure in place, full implementation pending.
    See docs/epic-repo-lint-status.md for tracking.
"""

import subprocess
from typing import List, Optional

from tools.repo_lint.common import LintResult, Violation
from tools.repo_lint.runners.base import Runner, command_exists


class RustRunner(Runner):
    """Runner for Rust linting and formatting tools.

    :Status:
        Stub implementation. Checks for tools and files, but linting logic
        is not yet fully implemented.
    """

    def has_files(self) -> bool:
        """Check if repository has Rust files.

        :Returns:
            True if Rust files exist, False otherwise
        """
        result = subprocess.run(
            ["git", "ls-files", "**/*.rs"], cwd=self.repo_root, capture_output=True, text=True, check=False
        )
        return bool(result.stdout.strip())

    def check_tools(self) -> List[str]:
        """Check which Rust tools are missing.

        :Returns:
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

        :Returns:
            List of linting results from all Rust tools

        :Note:
            Stub implementation. Returns placeholder results.
            Full implementation tracked in Phase 6.5 future work.
        """
        self._ensure_tools(["cargo"])

        results = []
        results.append(self._run_rustfmt_check())
        results.append(self._run_clippy())
        # TODO: Add docstring validation once Rust validator is integrated
        # results.append(self._run_docstring_validation())

        return results

    def fix(self, policy: Optional[dict] = None) -> List[LintResult]:
        """Apply Rust auto-fixes where possible.

        :Returns:
            List of linting results after fixes applied

        :Note:
            Stub implementation. Runs rustfmt in fix mode, then re-checks.
            Full implementation tracked in Phase 6.5 future work.
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

        :Returns:
            LintResult for rustfmt

        :Note:
            Stub implementation. Basic check only.
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
        """Run clippy linter.

        :Returns:
            LintResult for clippy

        :Note:
            Stub implementation. Basic check only.
        """
        rust_dir = self.repo_root / "rust"
        if not rust_dir.exists():
            # No rust directory - skip silently
            if self.verbose:
                print("  No rust/ directory found, skipping clippy check")
            return LintResult(tool="clippy", passed=True, violations=[])

        result = subprocess.run(
            ["cargo", "clippy", "--all-targets", "--all-features", "--", "-D", "warnings"],
            cwd=rust_dir,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            return LintResult(tool="clippy", passed=True, violations=[])

        violations = []
        # Parse clippy output for violations
        for line in result.stderr.splitlines():
            if "warning:" in line or "error:" in line:
                violations.append(Violation(tool="clippy", file=".", line=None, message=line.strip()))

        return LintResult(tool="clippy", passed=False, violations=violations[:20])  # Limit output

    def _run_docstring_validation(self) -> LintResult:
        """Run Rust docstring validation.

        :Returns:
            LintResult for docstring validation

        :Note:
            TODO: Not yet implemented. Requires integration with
            scripts/validate_docstrings.py for Rust files.
        """
        # Placeholder - docstring validation not yet implemented for Rust
        if self.verbose:
            print("  Rust docstring validation not yet implemented (TODO)")
        return LintResult(tool="rust-docstrings", passed=True, violations=[])
