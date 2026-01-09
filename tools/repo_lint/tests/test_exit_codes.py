#!/usr/bin/env python3
# pylint: disable=wrong-import-position,protected-access  # Test file needs special setup
"""Unit tests for exit code behavior.

:Purpose:
    Validates Phase 7 Item 7.1.2 - Test exit codes:
    - ExitCode.SUCCESS (0) when all checks pass
    - ExitCode.VIOLATIONS (1) when violations found
    - ExitCode.MISSING_TOOLS (2) in CI mode when tools missing
    - ExitCode.INTERNAL_ERROR (3) for internal errors
    - ExitCode.UNSAFE_VIOLATION (4) for unsafe mode policy violations

:Test Coverage:
    - cmd_check() returns SUCCESS when no violations
    - cmd_check() returns VIOLATIONS when violations found
    - cmd_check() returns MISSING_TOOLS in CI mode when tools missing
    - cmd_fix() returns SUCCESS when fixes applied successfully
    - cmd_fix() returns VIOLATIONS when violations remain after fix
    - cmd_fix() returns UNSAFE_VIOLATION when --unsafe used in CI
    - cmd_fix() returns UNSAFE_VIOLATION when --unsafe without --yes-i-know
    - cmd_fix() returns UNSAFE_VIOLATION when --unsafe with non-Python language
    - cmd_install() returns SUCCESS on successful install
    - cmd_install() returns INTERNAL_ERROR on install failure

:Usage:
    Run tests from repository root::

        python3 -m pytest tools/repo_lint/tests/test_exit_codes.py
        # or
        python3 tools/repo_lint/tests/test_exit_codes.py

:Environment Variables:
    None. Tests are self-contained with mocked components.

:Exit Codes:
    0
        All tests passed
    1
        One or more tests failed

:Examples:
    Run all tests::

        python3 -m pytest tools/repo_lint/tests/test_exit_codes.py -v

    Run specific test::

        python3 -m pytest tools/repo_lint/tests/test_exit_codes.py::TestExitCodes::test_success_when_no_violations -v

:Notes:
    - Tests use unittest.mock to avoid executing actual linters
    - Tests verify correct exit codes for all scenarios
    - Tests cover both local and CI modes
"""

from __future__ import annotations

import argparse
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

# Add repo_lint parent directory to path for imports
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))

from tools.repo_lint.cli_argparse import cmd_check, cmd_fix, cmd_install  # noqa: E402
from tools.repo_lint.common import ExitCode  # noqa: E402


class TestExitCodes(unittest.TestCase):
    """Test exit code behavior per Phase 7 Item 7.1.2.

    :Purpose:
        Validates correct exit codes for all scenarios.
    """

    def setUp(self) -> None:
        """Set up test fixtures.

        :Purpose:
            Create mock args for exit code testing.
        """
        # Create mock args
        self.args_local = argparse.Namespace(ci=False, verbose=False, only=None)
        self.args_ci = argparse.Namespace(ci=True, verbose=False, only=None)
        self.args_install = argparse.Namespace(verbose=False, cleanup=False)

    @patch("tools.repo_lint.cli_argparse._run_all_runners")
    def test_success_when_no_violations(self, mock_run_all) -> None:
        """Test that cmd_check returns SUCCESS when no violations.

        :Purpose:
            Verify EXIT_CODE.SUCCESS (0) when all checks pass.

        :param mock_run_all: Mocked _run_all_runners
        """
        # Mock successful check
        mock_run_all.return_value = ExitCode.SUCCESS

        # Run check
        result = cmd_check(self.args_local)

        # Verify success exit code
        self.assertEqual(result, ExitCode.SUCCESS)

    @patch("tools.repo_lint.cli_argparse._run_all_runners")
    def test_violations_when_issues_found(self, mock_run_all) -> None:
        """Test that cmd_check returns VIOLATIONS when issues found.

        :Purpose:
            Verify EXIT_CODE.VIOLATIONS (1) when violations exist.

        :param mock_run_all: Mocked _run_all_runners
        """
        # Mock check with violations
        mock_run_all.return_value = ExitCode.VIOLATIONS

        # Run check
        result = cmd_check(self.args_local)

        # Verify violations exit code
        self.assertEqual(result, ExitCode.VIOLATIONS)

    @patch("tools.repo_lint.cli_argparse._run_all_runners")
    def test_missing_tools_in_ci_mode(self, mock_run_all) -> None:
        """Test that cmd_check returns MISSING_TOOLS in CI mode.

        :Purpose:
            Verify EXIT_CODE.MISSING_TOOLS (2) in CI mode when tools missing.

        :param mock_run_all: Mocked _run_all_runners
        """
        # Mock missing tools
        mock_run_all.return_value = ExitCode.MISSING_TOOLS

        # Run check in CI mode
        result = cmd_check(self.args_ci)

        # Verify missing tools exit code
        self.assertEqual(result, ExitCode.MISSING_TOOLS)

    @patch("tools.repo_lint.cli_argparse._run_all_runners")
    @patch("tools.repo_lint.cli_argparse.load_policy")
    @patch("tools.repo_lint.cli_argparse.validate_policy")
    def test_fix_success_when_all_fixed(self, mock_validate, mock_load, mock_run_all) -> None:
        """Test that cmd_fix returns SUCCESS when all fixes applied.

        :Purpose:
            Verify EXIT_CODE.SUCCESS (0) when fix completes successfully.

        :param mock_validate: Mocked validate_policy
        :param mock_load: Mocked load_policy
        :param mock_run_all: Mocked _run_all_runners
        """
        # Mock policy load and validation
        mock_load.return_value = {"allowed_categories": ["formatting"]}
        mock_validate.return_value = []

        # Mock successful fix
        mock_run_all.return_value = ExitCode.SUCCESS

        # Run fix
        result = cmd_fix(self.args_local)

        # Verify success exit code
        self.assertEqual(result, ExitCode.SUCCESS)

    @patch("tools.repo_lint.cli_argparse._run_all_runners")
    @patch("tools.repo_lint.cli_argparse.load_policy")
    @patch("tools.repo_lint.cli_argparse.validate_policy")
    def test_fix_violations_when_issues_remain(self, mock_validate, mock_load, mock_run_all) -> None:
        """Test that cmd_fix returns VIOLATIONS when issues remain.

        :Purpose:
            Verify EXIT_CODE.VIOLATIONS (1) when violations remain after fix.

        :param mock_validate: Mocked validate_policy
        :param mock_load: Mocked load_policy
        :param mock_run_all: Mocked _run_all_runners
        """
        # Mock policy load and validation
        mock_load.return_value = {"allowed_categories": ["formatting"]}
        mock_validate.return_value = []

        # Mock fix with remaining violations
        mock_run_all.return_value = ExitCode.VIOLATIONS

        # Run fix
        result = cmd_fix(self.args_local)

        # Verify violations exit code
        self.assertEqual(result, ExitCode.VIOLATIONS)

    @patch("tools.repo_lint.cli_argparse.load_policy")
    @patch("tools.repo_lint.cli_argparse.validate_policy")
    def test_fix_internal_error_on_policy_failure(self, mock_validate, mock_load) -> None:
        """Test that cmd_fix returns INTERNAL_ERROR on policy failure.

        :Purpose:
            Verify EXIT_CODE.INTERNAL_ERROR (3) when policy validation fails.

        :param mock_validate: Mocked validate_policy
        :param mock_load: Mocked load_policy
        """
        # Mock policy load with validation errors
        mock_load.return_value = {"allowed_categories": ["invalid"]}
        mock_validate.return_value = ["Invalid category: invalid"]

        # Run fix
        result = cmd_fix(self.args_local)

        # Verify internal error exit code
        self.assertEqual(result, ExitCode.INTERNAL_ERROR)

    @patch("tools.repo_lint.cli_argparse.load_policy")
    def test_fix_internal_error_on_policy_not_found(self, mock_load) -> None:
        """Test that cmd_fix returns INTERNAL_ERROR when policy not found.

        :Purpose:
            Verify EXIT_CODE.INTERNAL_ERROR (3) when policy file missing.

        :param mock_load: Mocked load_policy
        """
        # Mock policy file not found
        mock_load.side_effect = FileNotFoundError()

        # Run fix
        result = cmd_fix(self.args_local)

        # Verify internal error exit code
        self.assertEqual(result, ExitCode.INTERNAL_ERROR)

    @patch("tools.repo_lint.cli_argparse.install_python_tools")
    @patch("tools.repo_lint.cli_argparse.print_bash_tool_instructions")
    @patch("tools.repo_lint.cli_argparse.print_powershell_tool_instructions")
    @patch("tools.repo_lint.cli_argparse.print_perl_tool_instructions")
    def test_install_success(
        self,
        mock_perl_inst,
        mock_ps_inst,
        mock_bash_inst,
        mock_python_inst,
    ) -> None:
        """Test that cmd_install returns SUCCESS on successful install.

        :Purpose:
            Verify EXIT_CODE.SUCCESS (0) when install completes successfully.

        :param mock_perl_inst: Mocked print_perl_tool_instructions
        :param mock_ps_inst: Mocked print_powershell_tool_instructions
        :param mock_bash_inst: Mocked print_bash_tool_instructions
        :param mock_python_inst: Mocked install_python_tools
        """
        # Mock successful install (returns tuple of success, errors)
        mock_python_inst.return_value = (True, [])

        # Run install
        result = cmd_install(self.args_install)

        # Verify success exit code
        self.assertEqual(result, ExitCode.SUCCESS)

    @patch("tools.repo_lint.cli_argparse.install_python_tools")
    @patch("tools.repo_lint.cli_argparse.print_bash_tool_instructions")
    @patch("tools.repo_lint.cli_argparse.print_powershell_tool_instructions")
    @patch("tools.repo_lint.cli_argparse.print_perl_tool_instructions")
    def test_install_internal_error_on_failure(
        self,
        mock_perl_inst,
        mock_ps_inst,
        mock_bash_inst,
        mock_python_inst,
    ) -> None:
        """Test that cmd_install returns INTERNAL_ERROR on install failure.

        :Purpose:
            Verify EXIT_CODE.INTERNAL_ERROR (3) when install fails.

        :param mock_perl_inst: Mocked print_perl_tool_instructions
        :param mock_ps_inst: Mocked print_powershell_tool_instructions
        :param mock_bash_inst: Mocked print_bash_tool_instructions
        :param mock_python_inst: Mocked install_python_tools
        """
        # Mock failed install (returns tuple of success, errors)
        mock_python_inst.return_value = (False, ["Installation failed"])

        # Run install
        result = cmd_install(self.args_install)

        # Verify internal error exit code
        self.assertEqual(result, ExitCode.INTERNAL_ERROR)

    @patch("tools.repo_lint.cli_argparse.cleanup_repo_local")
    def test_cleanup_success(self, mock_cleanup) -> None:
        """Test that cmd_install --cleanup returns SUCCESS on success.

        :Purpose:
            Verify EXIT_CODE.SUCCESS (0) when cleanup completes successfully.

        :param mock_cleanup: Mocked cleanup_repo_local
        """
        # Mock successful cleanup
        mock_cleanup.return_value = (True, ["Cleanup message"])

        # Run cleanup
        args_cleanup = argparse.Namespace(verbose=False, cleanup=True)
        result = cmd_install(args_cleanup)

        # Verify success exit code
        self.assertEqual(result, ExitCode.SUCCESS)

    @patch("tools.repo_lint.cli_argparse.cleanup_repo_local")
    def test_cleanup_internal_error_on_failure(self, mock_cleanup) -> None:
        """Test that cmd_install --cleanup returns INTERNAL_ERROR on failure.

        :Purpose:
            Verify EXIT_CODE.INTERNAL_ERROR (3) when cleanup fails.

        :param mock_cleanup: Mocked cleanup_repo_local
        """
        # Mock failed cleanup
        mock_cleanup.return_value = (False, ["Cleanup error"])

        # Run cleanup
        args_cleanup = argparse.Namespace(verbose=False, cleanup=True)
        result = cmd_install(args_cleanup)

        # Verify internal error exit code
        self.assertEqual(result, ExitCode.INTERNAL_ERROR)

    @patch("tools.repo_lint.cli_argparse.load_policy")
    @patch("tools.repo_lint.cli_argparse.validate_policy")
    def test_fix_unsafe_violation_in_ci(self, mock_validate, mock_load) -> None:
        """Test that cmd_fix returns UNSAFE_VIOLATION when --unsafe used in CI.

        :Purpose:
            Verify EXIT_CODE.UNSAFE_VIOLATION (4) when unsafe mode is used in CI.

        :param mock_validate: Mocked validate_policy
        :param mock_load: Mocked load_policy
        """
        # Create args with unsafe mode in CI
        args_unsafe_ci = argparse.Namespace(
            ci=True,
            verbose=False,
            only=None,
            unsafe=True,
            yes_i_know=True,
        )

        # Run fix with unsafe in CI
        result = cmd_fix(args_unsafe_ci)

        # Verify unsafe violation exit code
        self.assertEqual(result, ExitCode.UNSAFE_VIOLATION)

    @patch("tools.repo_lint.cli_argparse.load_policy")
    @patch("tools.repo_lint.cli_argparse.validate_policy")
    def test_fix_unsafe_violation_without_confirmation(self, mock_validate, mock_load) -> None:
        """Test that cmd_fix returns UNSAFE_VIOLATION when --unsafe without --yes-i-know.

        :Purpose:
            Verify EXIT_CODE.UNSAFE_VIOLATION (4) when unsafe mode lacks confirmation.

        :param mock_validate: Mocked validate_policy
        :param mock_load: Mocked load_policy
        """
        # Create args with unsafe mode but no confirmation
        args_unsafe_no_confirm = argparse.Namespace(
            ci=False,
            verbose=False,
            only=None,
            unsafe=True,
            yes_i_know=False,
        )

        # Run fix with unsafe but no confirmation
        result = cmd_fix(args_unsafe_no_confirm)

        # Verify unsafe violation exit code
        self.assertEqual(result, ExitCode.UNSAFE_VIOLATION)

    @patch("tools.repo_lint.cli_argparse.load_policy")
    @patch("tools.repo_lint.cli_argparse.validate_policy")
    @patch.dict(os.environ, {}, clear=True)  # Clear environment to ensure CI is not set
    def test_fix_unsafe_violation_non_python_language(self, mock_validate, mock_load) -> None:
        """Test that cmd_fix returns UNSAFE_VIOLATION when --unsafe with non-Python language.

        :Purpose:
            Verify EXIT_CODE.UNSAFE_VIOLATION (4) when unsafe mode used with unsupported language.

        :param mock_validate: Mocked validate_policy
        :param mock_load: Mocked load_policy
        """
        # Mock policy loading to succeed
        mock_load.return_value = {}
        mock_validate.return_value = []

        # Create args with unsafe mode and non-Python language
        args_unsafe_perl = argparse.Namespace(
            ci=False,
            verbose=False,
            only="perl",
            unsafe=True,
            yes_i_know=True,
            json=False,
        )

        # Run fix with unsafe and --only=perl
        result = cmd_fix(args_unsafe_perl)

        # Verify unsafe violation exit code
        self.assertEqual(result, ExitCode.UNSAFE_VIOLATION)


if __name__ == "__main__":
    unittest.main()
