#!/usr/bin/env python3
# pylint: disable=wrong-import-position  # Test file needs special setup

"""Tests for Integration Tests.

:Purpose:
    Unit tests for Integration Tests functionality.

:Environment Variables:
    None directly used. Tests may set environment variables temporarily via patching.

:Examples:
    Run all tests::

        python3 -m pytest test_integration.py -v

:Exit Codes:
    Uses pytest exit codes:
    - 0: All tests passed
    - 1: Tests failed
    - 2: Test execution error
"""
from __future__ import annotations

from __future__ import annotations


import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

# Add repo_lint parent directory to path for imports
# Note: .parent chain matches pattern used consistently across all test files in this codebase
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))

from tools.repo_lint.common import ExitCode  # noqa: E402


class TestIntegration(unittest.TestCase):
    """Integration tests for full CLI invocation.

    :Purpose:
        Validates end-to-end behavior from CLI parsing to command execution.
    """

    @patch("tools.repo_lint.cli_argparse._run_all_runners")
    @patch("sys.argv", ["repo-lint", "check", "--ci"])
    def test_check_missing_tools_ci(self, mock_run_all):
        """Test full CLI invocation: check --ci with missing tools.

        :Purpose:
            Verify integration from CLI parsing to exit code 2 for missing tools.

        :param mock_run_all: Mocked _run_all_runners
        """
        from tools.repo_lint.cli_argparse import main

        # Mock missing tools
        mock_run_all.return_value = ExitCode.MISSING_TOOLS

        # Run full CLI
        with self.assertRaises(SystemExit) as cm:
            main()

        # Verify exit code 2 (missing tools)
        self.assertEqual(cm.exception.code, ExitCode.MISSING_TOOLS)

    @patch("tools.repo_lint.cli_argparse.load_policy")
    @patch("sys.argv", ["repo-lint", "fix"])
    def test_fix_policy_not_found(self, mock_load):
        """Test full CLI invocation: fix with missing policy file.

        :Purpose:
            Verify integration from CLI parsing to exit code 3 for policy errors.

        :param mock_load: Mocked load_policy
        """
        from tools.repo_lint.cli_argparse import main

        # Mock policy file not found
        mock_load.side_effect = FileNotFoundError()

        # Run full CLI
        with self.assertRaises(SystemExit) as cm:
            main()

        # Verify exit code 3 (internal error)
        self.assertEqual(cm.exception.code, ExitCode.INTERNAL_ERROR)

    @patch.dict(os.environ, {}, clear=True)  # Clear CI environment
    @patch("sys.argv", ["repo-lint", "fix", "--unsafe", "--yes-i-know", "--only=perl"])
    def test_fix_unsafe_unsupported_language(self):
        """Test full CLI invocation: fix --unsafe with unsupported language.

        :Purpose:
            Verify integration from CLI parsing to exit code 4 for unsafe violations.
        """
        from tools.repo_lint.cli_argparse import main

        # Run full CLI
        with self.assertRaises(SystemExit) as cm:
            main()

        # Verify exit code 4 (unsafe violation)
        self.assertEqual(cm.exception.code, ExitCode.UNSAFE_VIOLATION)

    @patch("sys.argv", ["repo-lint", "fix", "--unsafe", "--ci"])
    def test_fix_unsafe_forbidden_in_ci(self):
        """Test full CLI invocation: fix --unsafe in CI environment.

        :Purpose:
            Verify integration from CLI parsing to exit code 4 for CI unsafe violation.
        """
        from tools.repo_lint.cli_argparse import main

        # Run full CLI
        with self.assertRaises(SystemExit) as cm:
            main()

        # Verify exit code 4 (unsafe violation)
        self.assertEqual(cm.exception.code, ExitCode.UNSAFE_VIOLATION)

    @patch("sys.argv", ["repo-lint"])
    def test_no_command_shows_help(self):
        """Test full CLI invocation: no command shows help.

        :Purpose:
            Verify CLI shows help and exits successfully when no command given.
        """
        from tools.repo_lint.cli_argparse import main

        # Run full CLI with no command
        with self.assertRaises(SystemExit) as cm:
            main()

        # Verify exit code 0 (success)
        self.assertEqual(cm.exception.code, ExitCode.SUCCESS)

    @patch("tools.repo_lint.cli_argparse.install_python_tools")
    @patch("tools.repo_lint.cli_argparse.print_bash_tool_instructions")
    @patch("tools.repo_lint.cli_argparse.print_powershell_tool_instructions")
    @patch("tools.repo_lint.cli_argparse.print_perl_tool_instructions")
    @patch("sys.argv", ["repo-lint", "install"])
    def test_install_failure_integration(self, mock_perl, mock_ps, mock_bash, mock_python):
        """Test full CLI invocation: install with Python tools failure.

        :Purpose:
            Verify integration from CLI parsing to exit code 3 for install failures.

        :param mock_perl: Mocked print_perl_tool_instructions
        :param mock_ps: Mocked print_powershell_tool_instructions
        :param mock_bash: Mocked print_bash_tool_instructions
        :param mock_python: Mocked install_python_tools
        """
        from tools.repo_lint.cli_argparse import main

        # Mock Python tools install failure
        mock_python.return_value = (False, ["Installation failed"])

        # Run full CLI
        with self.assertRaises(SystemExit) as cm:
            main()

        # Verify exit code 3 (internal error)
        self.assertEqual(cm.exception.code, ExitCode.INTERNAL_ERROR)

        # Verify manual instructions were NOT printed (per Phase 1 Item 3)
        mock_bash.assert_not_called()
        mock_ps.assert_not_called()
        mock_perl.assert_not_called()


if __name__ == "__main__":
    unittest.main()
