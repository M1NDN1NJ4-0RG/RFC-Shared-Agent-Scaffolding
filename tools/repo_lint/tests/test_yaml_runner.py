#!/usr/bin/env python3

"""Unit tests for YAML runner (yamllint).

from __future__ import annotations


:Purpose:
    Validates that the YAML runner correctly integrates with yamllint.

:Test Coverage:
    - has_files() detects YAML files (both .yml and .yaml)
    - _run_yamllint() runs with correct arguments
    - yamllint uses -f parsable flag
    - Empty file lists are handled correctly
    - Both .yml and .yaml extensions are detected

:Usage:
    Run tests from repository root::

        python3 -m pytest tools/repo_lint/tests/test_yaml_runner.py
        # or
        python3 tools/repo_lint/tests/test_yaml_runner.py

:Environment Variables:
    None. Tests are self-contained with mocked subprocess calls.

:Exit Codes:
    0
        All tests passed
    1
        One or more tests failed

:Examples:
    Run all tests::

        python3 -m pytest tools/repo_lint/tests/test_yaml_runner.py -v

    Run specific test::

        python3 -m pytest tools/repo_lint/tests/test_yaml_runner.py::TestYAMLRunner \
            ::test_yamllint_uses_parsable_format -v

:Notes:
    - Tests use unittest.mock to avoid executing actual linters
    - Tests verify command-line arguments passed to subprocess
    - Tests verify both .yml and .yaml extensions are handled
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add repo_lint parent directory to path for imports
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))

from tools.repo_lint.runners.yaml_runner import YAMLRunner  # noqa: E402  # pylint: disable=wrong-import-position


class TestYAMLRunner(unittest.TestCase):
    """Test YAML runner behavior.

    :Purpose:
        Validates yamllint integration.
    """

    def setUp(self):
        """Set up test fixtures.

        :Purpose:
            Create YAMLRunner instance with mocked repo root.
        """
        self.runner = YAMLRunner(repo_root=Path("/fake/repo"))

    @patch("tools.repo_lint.runners.yaml_runner.subprocess.run")
    def test_has_files_detects_yml(self, mock_run):
        """Test that has_files detects .yml files.

        :Purpose:
            Verify YAML file detection for .yml extension.

        :param mock_run: Mocked subprocess.run
        """
        mock_run.return_value = MagicMock(returncode=0, stdout="config.yml\n", stderr="")

        self.assertTrue(self.runner.has_files())

    @patch("tools.repo_lint.runners.yaml_runner.subprocess.run")
    def test_has_files_detects_yaml(self, mock_run):
        """Test that has_files detects .yaml files.

        :Purpose:
            Verify YAML file detection for .yaml extension.

        :param mock_run: Mocked subprocess.run
        """
        mock_run.return_value = MagicMock(returncode=0, stdout="config.yaml\n", stderr="")

        self.assertTrue(self.runner.has_files())

    @patch("tools.repo_lint.runners.yaml_runner.subprocess.run")
    def test_has_files_detects_both_extensions(self, mock_run):
        """Test that has_files detects both .yml and .yaml files.

        :Purpose:
            Verify YAML file detection for both extensions.

        :param mock_run: Mocked subprocess.run
        """
        mock_run.return_value = MagicMock(returncode=0, stdout="config.yml\nother.yaml\n", stderr="")

        self.assertTrue(self.runner.has_files())

    @patch("tools.repo_lint.runners.yaml_runner.subprocess.run")
    def test_yamllint_uses_parsable_format(self, mock_run):
        """Test that _run_yamllint uses -f parsable flag.

        :Purpose:
            Verify yamllint runs with parsable output format.

        :param mock_run: Mocked subprocess.run
        """
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="test.yml\n", stderr=""),  # git ls-files
            MagicMock(returncode=0, stdout="", stderr=""),  # yamllint
        ]

        result = self.runner._run_yamllint()  # pylint: disable=protected-access

        # Check yamllint call (second call)
        self.assertEqual(mock_run.call_count, 2)
        yamllint_args = mock_run.call_args_list[1][0][0]
        self.assertIn("-f", yamllint_args)
        self.assertIn("parsable", yamllint_args)
        self.assertTrue(result.passed)

    @patch("tools.repo_lint.runners.yaml_runner.subprocess.run")
    def test_yamllint_handles_violations(self, mock_run):
        """Test that _run_yamllint correctly parses violations.

        :Purpose:
            Verify violation parsing from yamllint output.

        :param mock_run: Mocked subprocess.run
        """
        mock_output = """test.yml:10:1: [error] syntax error: expected <block end>, but found '<block mapping start>'
test.yml:20:5: [warning] line too long (120 > 80 characters)"""
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="test.yml\n", stderr=""),  # git ls-files
            MagicMock(returncode=1, stdout=mock_output, stderr=""),  # yamllint
        ]

        result = self.runner._run_yamllint()  # pylint: disable=protected-access

        self.assertFalse(result.passed)
        self.assertEqual(result.tool, "yamllint")
        self.assertEqual(len(result.violations), 2)

    @patch("tools.repo_lint.runners.yaml_runner.subprocess.run")
    def test_empty_files_returns_passed(self, mock_run):
        """Test that empty file list returns passed result.

        :Purpose:
            Verify methods handle empty file lists gracefully.

        :param mock_run: Mocked subprocess.run
        """
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        self.assertTrue(self.runner._run_yamllint().passed)  # pylint: disable=protected-access

    @patch("tools.repo_lint.runners.yaml_runner.subprocess.run")
    def test_check_tools_detects_missing_yamllint(self, mock_run):
        """Test that check_tools detects missing yamllint.

        :Purpose:
            Verify tool detection correctly identifies missing yamllint.

        :param mock_run: Mocked subprocess.run
        """
        with patch("tools.repo_lint.runners.yaml_runner.command_exists", return_value=False):
            missing = self.runner.check_tools()
            self.assertIn("yamllint", missing)

    @patch("tools.repo_lint.runners.yaml_runner.subprocess.run")
    def test_fix_runs_same_as_check(self, mock_run):
        """Test that fix() runs same checks as check() (no auto-fix).

        :Purpose:
            Verify yamllint has no auto-fix mode (fix same as check).

        :param mock_run: Mocked subprocess.run
        """
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        check_results = self.runner.check()
        fix_results = self.runner.fix()

        # Both should call yamllint once
        self.assertEqual(len(check_results), 1)
        self.assertEqual(len(fix_results), 1)
        self.assertEqual(check_results[0].tool, "yamllint")
        self.assertEqual(fix_results[0].tool, "yamllint")


if __name__ == "__main__":
    unittest.main()
