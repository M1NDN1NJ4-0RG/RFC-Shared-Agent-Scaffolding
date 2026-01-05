#!/usr/bin/env python3
# pylint: disable=wrong-import-position,protected-access  # Test file needs special setup

"""Unit tests for Python runner (Ruff check/fix behavior).

from __future__ import annotations


:Purpose:
    Validates that the Python runner correctly implements Phase 0 Item 0.9.1:
    - check command is non-mutating (uses --no-fix)
    - fix command applies safe fixes only (uses --fix without --unsafe-fixes)
    - Both commands handle exit codes correctly

:Test Coverage:
    - _run_ruff_check() runs with --no-fix and is non-mutating
    - _run_ruff_fix() applies safe fixes but not unsafe fixes
    - fix() command properly sequences Black and Ruff fixes
    - Both methods handle exit codes correctly
    - Output parsing works correctly for both check and fix contexts

:Usage:
    Run tests from repository root::

        python3 -m pytest tools/repo_lint/tests/test_python_runner.py
        # or
        python3 tools/repo_lint/tests/test_python_runner.py

:Environment Variables:
    None. Tests are self-contained with mocked subprocess calls.

:Exit Codes:
    0
        All tests passed
    1
        One or more tests failed

:Examples:
    Run all tests::

        python3 -m pytest tools/repo_lint/tests/test_python_runner.py -v

    Run specific test::

        python3 -m pytest tools/repo_lint/tests/test_python_runner.py::TestRuffCheckFix::test_check_uses_no_fix -v

:Notes:
    - Tests use unittest.mock to avoid executing actual linters
    - Tests verify command-line arguments passed to subprocess
    - Tests check that file modifications only happen during fix, not check
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add repo_lint parent directory to path for imports
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))

from tools.repo_lint.runners.python_runner import PythonRunner  # noqa: E402


class TestRuffCheckFix(unittest.TestCase):
    """Test Ruff check/fix behavior per Phase 0 Item 0.9.1.

    :Purpose:
        Validates split check/fix behavior and --no-fix vs --fix usage.
    """

    def setUp(self):
        """Set up test fixtures.

        :Purpose:
            Create PythonRunner instance with mocked repo root.
        """
        self.runner = PythonRunner(repo_root=Path("/fake/repo"))

    @patch("tools.repo_lint.runners.python_runner.subprocess.run")
    def test_check_uses_no_fix(self, mock_run):
        """Test that _run_ruff_check uses --no-fix flag.

        :Purpose:
            Verify check command is non-mutating per Phase 0 Item 0.9.1.

        :param mock_run: Mocked subprocess.run
        """
        # Mock successful Ruff check
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        # Run check
        result = self.runner._run_ruff_check()

        # Verify --no-fix was used
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        self.assertIn("--no-fix", call_args, "Check should use --no-fix flag")
        self.assertNotIn("--fix", call_args, "Check should not use --fix flag")

        # Verify result
        self.assertTrue(result.passed, "Check with no violations should pass")
        self.assertEqual(result.tool, "ruff")

    @patch("tools.repo_lint.runners.python_runner.subprocess.run")
    def test_fix_uses_fix_flag(self, mock_run):
        """Test that _run_ruff_fix uses --fix flag.

        :Purpose:
            Verify fix command applies safe fixes per Phase 0 Item 0.9.1.

        :param mock_run: Mocked subprocess.run
        """
        # Mock successful Ruff fix
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        # Run fix
        result = self.runner._run_ruff_fix()

        # Verify --fix was used but --unsafe-fixes was NOT
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        self.assertIn("--fix", call_args, "Fix should use --fix flag")
        self.assertNotIn("--unsafe-fixes", call_args, "Fix should not use --unsafe-fixes flag")
        self.assertNotIn("--no-fix", call_args, "Fix should not use --no-fix flag")

        # Verify result
        self.assertTrue(result.passed, "Fix with no remaining violations should pass")
        self.assertEqual(result.tool, "ruff")

    @patch("tools.repo_lint.runners.python_runner.subprocess.run")
    def test_check_handles_violations(self, mock_run):
        """Test that _run_ruff_check correctly parses violations.

        :Purpose:
            Verify violation parsing in check mode.

        :param mock_run: Mocked subprocess.run
        """
        # Mock Ruff check with violations
        mock_output = """tools/repo_lint/cli.py:10:1: E501 Line too long (125 > 120)
tools/repo_lint/cli.py:20:5: F841 Local variable 'x' is assigned but never used
Found 2 errors."""
        mock_run.return_value = MagicMock(returncode=1, stdout=mock_output, stderr="")

        # Run check
        result = self.runner._run_ruff_check()

        # Verify result
        self.assertFalse(result.passed, "Check with violations should fail")
        self.assertEqual(result.tool, "ruff")
        self.assertEqual(len(result.violations), 2, "Should parse 2 violations (ignoring 'Found' line)")

    @patch("tools.repo_lint.runners.python_runner.subprocess.run")
    def test_check_handles_unsafe_fixes_warning(self, mock_run):
        """Test that _run_ruff_check handles unsafe fixes warning.

        :Purpose:
            Verify unsafe fixes message is parsed with check context.

        :param mock_run: Mocked subprocess.run
        """
        # Mock Ruff check with unsafe fixes warning
        mock_output = """tools/repo_lint/cli.py:10:1: E501 Line too long (125 > 120)
No fixes available (1 hidden fixes can be enabled with the `--unsafe-fixes` option).
Found 1 error."""
        mock_run.return_value = MagicMock(returncode=1, stdout=mock_output, stderr="")

        # Run check
        result = self.runner._run_ruff_check()

        # Verify we have 1 actual violation (E501) plus info message
        self.assertFalse(result.passed)  # Should fail - has E501 violation
        self.assertEqual(len(result.violations), 1)  # One E501 violation
        self.assertIsNotNone(result.info_message)  # Info message present
        self.assertIn("Review before applying", result.info_message, "Should use check context message")

    @patch("tools.repo_lint.runners.python_runner.subprocess.run")
    def test_fix_handles_unsafe_fixes_warning(self, mock_run):
        """Test that _run_ruff_fix handles unsafe fixes warning.

        :Purpose:
            Verify unsafe fixes message is parsed with fix context.

        :param mock_run: Mocked subprocess.run
        """
        # Mock Ruff fix with unsafe fixes warning
        mock_output = """tools/repo_lint/cli.py:10:1: E501 Line too long (125 > 120)
No fixes available (1 hidden fixes can be enabled with the `--unsafe-fixes` option).
Found 1 error."""
        mock_run.return_value = MagicMock(returncode=1, stdout=mock_output, stderr="")

        # Run fix
        result = self.runner._run_ruff_fix()

        # Verify unsafe fixes warning is in info_message, not violations
        # One actual violation remains (E501), so should fail
        self.assertFalse(result.passed)
        self.assertEqual(len(result.violations), 1)  # One E501 violation
        self.assertIsNotNone(result.info_message)  # Info message present
        self.assertIn("not applied automatically", result.info_message, "Should use fix context message")

    @patch("tools.repo_lint.runners.python_runner.subprocess.run")
    def test_fix_command_sequences_black_and_ruff(self, mock_run):
        """Test that fix() command calls both Black and Ruff.

        :Purpose:
            Verify fix command properly sequences formatters.

        :param mock_run: Mocked subprocess.run
        """
        # Mock successful Black and Ruff runs
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        # Create policy that allows both Black and Ruff fixes
        policy = {"allowed_categories": [{"category": "FORMAT.BLACK"}, {"category": "LINT.RUFF.SAFE"}]}

        # Mock tool checks and has_files
        with patch("tools.repo_lint.runners.python_runner.command_exists", return_value=True):
            with patch.object(self.runner, "has_files", return_value=True):
                # Run fix with policy
                self.runner.fix(policy=policy)

        # Verify Black was called
        black_calls = [call for call in mock_run.call_args_list if "black" in str(call)]
        self.assertGreater(len(black_calls), 0, "Black should be called during fix")

        # Verify Ruff was called with --fix
        ruff_calls = [call for call in mock_run.call_args_list if "ruff" in str(call)]
        self.assertGreater(len(ruff_calls), 0, "Ruff should be called during fix")

        # Verify at least one Ruff call used --fix
        ruff_fix_calls = [call for call in ruff_calls if "--fix" in str(call)]
        self.assertGreater(len(ruff_fix_calls), 0, "Ruff should be called with --fix during fix command")


class TestParseRuffOutput(unittest.TestCase):
    """Test _parse_ruff_output helper method.

    :Purpose:
        Validates output parsing logic for both check and fix contexts.
    """

    def setUp(self):
        """Set up test fixtures.

        :Purpose:
            Create PythonRunner instance.
        """
        self.runner = PythonRunner(repo_root=Path("/fake/repo"))

    def test_parse_empty_output(self):
        """Test parsing empty output.

        :Purpose:
            Verify empty output returns no violations.
        """
        violations, _ = self.runner._parse_ruff_output("", context="check")
        self.assertEqual(len(violations), 0, "Empty output should have no violations")

    def test_parse_check_context_unsafe_message(self):
        """Test parsing unsafe fixes message in check context.

        :Purpose:
            Verify check context uses correct message in info_message.
        """
        output = "No fixes available (1 hidden fixes can be enabled with the `--unsafe-fixes` option)."
        violations, info_message = self.runner._parse_ruff_output(output, context="check")

        self.assertEqual(len(violations), 0)  # No actual violations
        self.assertIsNotNone(info_message)
        self.assertIn("Review before applying", info_message)
        self.assertNotIn("not applied automatically", info_message)

    def test_parse_fix_context_unsafe_message(self):
        """Test parsing unsafe fixes message in fix context.

        :Purpose:
            Verify fix context uses correct message in info_message.
        """
        output = "No fixes available (1 hidden fixes can be enabled with the `--unsafe-fixes` option)."
        violations, info_message = self.runner._parse_ruff_output(output, context="fix")

        self.assertEqual(len(violations), 0)  # No actual violations
        self.assertIsNotNone(info_message)
        self.assertIn("not applied automatically", info_message)
        self.assertNotIn("Review before applying", info_message)

    def test_parse_filters_found_lines(self):
        """Test that 'Found N errors' lines are filtered out.

        :Purpose:
            Verify summary lines are not included as violations.
        """
        output = """tools/cli.py:10:1: E501 Line too long
Found 1 error."""
        violations, _ = self.runner._parse_ruff_output(output, context="check")

        # Should only parse the actual violation, not the "Found" line
        self.assertEqual(len(violations), 1)
        self.assertNotIn("Found", violations[0].message)


if __name__ == "__main__":
    unittest.main()
