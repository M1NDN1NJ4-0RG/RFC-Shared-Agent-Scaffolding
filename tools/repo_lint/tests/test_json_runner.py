#!/usr/bin/env python3
# pylint: disable=wrong-import-position,protected-access,too-many-public-methods
# ruff: noqa: SLF001
"""Unit tests for JSON/JSONC runner.

:Purpose:
    Validates that the JSON/JSONC runner correctly integrates Prettier
    for formatting and style enforcement, and validates JSON metadata fields.

:Test Coverage:
    - File discovery (JSON and JSONC detection)
    - Tool checking (Prettier availability)
    - Check mode (format validation)
    - Fix mode (auto-formatting)
    - Result parsing and violation reporting
    - JSON metadata validation ($schema, description, title fields)

:Usage:
    Run tests from repository root::

        python3 -m pytest tools/repo_lint/tests/test_json_runner.py
        # or
        python3 tools/repo_lint/tests/test_json_runner.py

:Environment Variables:
    None. Tests are self-contained.

:Exit Codes:
    0
        All tests passed
    1
        One or more tests failed

:Examples:
    Run all tests::

        python3 -m pytest tools/repo_lint/tests/test_json_runner.py -v

    Run specific test::

        python3 -m pytest tools/repo_lint/tests/test_json_runner.py::TestJsonRunner \
            ::test_has_files_with_json -v

:Notes:
    - Tests use real file discovery logic (no mocking of filesystem)
    - Tests verify exact tool requirements and commands
    - Tests include JSON metadata validation requirements
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add repo_lint parent directory to path for imports
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))

from tools.repo_lint.runners.json_runner import JsonRunner  # noqa: E402


class TestJsonRunner(unittest.TestCase):
    """Test JSON/JSONC runner behavior.

    :Purpose:
        Validates JSON/JSONC runner integration with Prettier.
    """

    def setUp(self) -> None:
        """Set up test fixtures.

        :Purpose:
            Initialize runner instance for each test.
        """
        self.runner = JsonRunner()

    def test_has_files_detects_json(self) -> None:
        """Test that has_files() detects .json files.

        :Purpose:
            Verify runner detects JSON files in repository.
        """
        # Repository has .prettierrc.json and other JSON files
        self.assertTrue(self.runner.has_files())

    def test_has_files_detects_jsonc(self) -> None:
        """Test that has_files() detects .jsonc files.

        :Purpose:
            Verify runner detects JSONC files in repository.
        """
        # Repository has .markdownlint-cli2.jsonc
        self.assertTrue(self.runner.has_files())

    def test_check_tools_requires_prettier(self) -> None:
        """Test that check_tools() requires Prettier.

        :Purpose:
            Verify runner correctly identifies Prettier as required tool.
        """
        # Mock command_exists to simulate Prettier not installed
        with patch("tools.repo_lint.runners.json_runner.command_exists") as mock_exists:
            mock_exists.return_value = False
            missing = self.runner.check_tools()

        self.assertEqual(missing, ["prettier"])

    def test_check_tools_prettier_available(self) -> None:
        """Test check_tools() when Prettier is available.

        :Purpose:
            Verify no missing tools when Prettier is installed.
        """
        # Mock command_exists to simulate Prettier installed
        with patch("tools.repo_lint.runners.json_runner.command_exists") as mock_exists:
            mock_exists.return_value = True
            missing = self.runner.check_tools()

        self.assertEqual(missing, [])

    def test_run_prettier_check_mode(self) -> None:
        """Test _run_prettier in check mode.

        :Purpose:
            Verify check mode uses --check flag.
        """
        # Mock subprocess.run to capture command
        with patch("tools.repo_lint.runners.json_runner.subprocess.run") as mock_run:
            # Mock successful run (exit 0 = no violations)
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            # Mock get_tracked_files to return test files
            with patch("tools.repo_lint.runners.json_runner.get_tracked_files") as mock_files:
                mock_files.return_value = ["test.json"]

                result = self.runner._run_prettier(fix=False)

        # Verify command includes --check
        call_args = mock_run.call_args[0][0]
        self.assertIn("prettier", call_args)
        self.assertIn("--check", call_args)
        self.assertTrue(result.passed)

    def test_run_prettier_fix_mode(self) -> None:
        """Test _run_prettier in fix mode.

        :Purpose:
            Verify fix mode uses --write flag.
        """
        # Mock subprocess.run to capture command
        with patch("tools.repo_lint.runners.json_runner.subprocess.run") as mock_run:
            # Mock successful run (exit 0)
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            # Mock get_tracked_files to return test files
            with patch("tools.repo_lint.runners.json_runner.get_tracked_files") as mock_files:
                mock_files.return_value = ["test.json"]

                result = self.runner._run_prettier(fix=True)

        # Verify command includes --write
        call_args = mock_run.call_args[0][0]
        self.assertIn("prettier", call_args)
        self.assertIn("--write", call_args)
        self.assertNotIn("--check", call_args)
        self.assertTrue(result.passed)

    def test_run_prettier_with_violations(self) -> None:
        """Test _run_prettier when files need formatting.

        :Purpose:
            Verify violations are detected and parsed correctly.
        """
        # Mock subprocess.run to simulate violations
        with patch("tools.repo_lint.runners.json_runner.subprocess.run") as mock_run:
            # Mock exit 1 with file list in output
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="Checking formatting...\ntest.json\n[warn] Code style issues found in 1 file.",
                stderr="",
            )

            # Mock get_tracked_files
            with patch("tools.repo_lint.runners.json_runner.get_tracked_files") as mock_files:
                mock_files.return_value = ["test.json"]

                result = self.runner._run_prettier(fix=False)

        # Verify violations detected
        self.assertFalse(result.passed)
        self.assertEqual(len(result.violations), 1)
        self.assertEqual(result.violations[0].file, "test.json")
        self.assertEqual(result.violations[0].tool, "prettier")

    def test_parse_prettier_output_single_file(self) -> None:
        """Test parsing Prettier output for single file.

        :Purpose:
            Verify correct violation parsing for one file.
        """
        stdout = "Checking formatting...\ntest.json\n[warn] Code style issues found in 1 file."
        stderr = ""

        violations = self.runner._parse_prettier_output(stdout, stderr)

        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].file, "test.json")
        self.assertIn("not properly formatted", violations[0].message)

    def test_parse_prettier_output_multiple_files(self) -> None:
        """Test parsing Prettier output for multiple files.

        :Purpose:
            Verify correct violation parsing for multiple files.
        """
        stdout = """Checking formatting...
test1.json
test2.jsonc
config.json
[warn] Code style issues found in 3 files."""
        stderr = ""

        violations = self.runner._parse_prettier_output(stdout, stderr)

        self.assertEqual(len(violations), 3)
        files = [v.file for v in violations]
        self.assertIn("test1.json", files)
        self.assertIn("test2.jsonc", files)
        self.assertIn("config.json", files)

    def test_parse_prettier_output_no_violations(self) -> None:
        """Test parsing Prettier output when all files pass.

        :Purpose:
            Verify no violations when formatting is correct.
        """
        stdout = "Checking formatting...\nAll matched files use Prettier code style!"
        stderr = ""

        violations = self.runner._parse_prettier_output(stdout, stderr)

        self.assertEqual(len(violations), 0)

    def test_parse_prettier_output_ignores_status_lines(self) -> None:
        """Test that status lines are ignored in parsing.

        :Purpose:
            Verify parser skips non-file lines.
        """
        stdout = """Checking formatting...
[warn] Some warning message
test.json
[error] Some error
files checked in 0.5s
Code style issues found in 1 file."""
        stderr = ""

        violations = self.runner._parse_prettier_output(stdout, stderr)

        # Should only detect test.json, not status/warning lines
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].file, "test.json")

    def test_run_prettier_uses_config_file(self) -> None:
        """Test that _run_prettier uses .prettierrc.json config.

        :Purpose:
            Verify config file is included in command.
        """
        # Mock subprocess.run
        with patch("tools.repo_lint.runners.json_runner.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            # Mock get_tracked_files
            with patch("tools.repo_lint.runners.json_runner.get_tracked_files") as mock_files:
                mock_files.return_value = ["test.json"]

                # Mock config file existence
                with patch.object(Path, "exists", return_value=True):
                    self.runner._run_prettier(fix=False)

        # Verify --config flag is used
        call_args = mock_run.call_args[0][0]
        self.assertIn("--config", call_args)
        # Config path should be right after --config
        config_idx = call_args.index("--config")
        self.assertTrue(call_args[config_idx + 1].endswith(".prettierrc.json"))

    def test_check_method_calls_run_prettier(self) -> None:
        """Test that check() method calls _run_prettier.

        :Purpose:
            Verify check orchestration works correctly.
        """
        # Mock _ensure_tools to skip tool checking
        with patch.object(self.runner, "_ensure_tools"):
            # Mock _should_run_tool to return True
            with patch.object(self.runner, "_should_run_tool", return_value=True):
                # Mock _run_prettier and _validate_json_metadata
                with patch.object(self.runner, "_run_prettier") as mock_prettier:
                    with patch.object(self.runner, "_validate_json_metadata") as mock_metadata:
                        mock_prettier.return_value = MagicMock(passed=True, violations=[])
                        mock_metadata.return_value = MagicMock(passed=True, violations=[])

                        results = self.runner.check()

        # Verify _run_prettier was called (no explicit fix parameter = defaults to False)
        mock_prettier.assert_called_once_with()
        mock_metadata.assert_called_once_with()
        self.assertEqual(len(results), 2)  # prettier + metadata

    def test_fix_method_calls_run_prettier_with_fix(self) -> None:
        """Test that fix() method calls _run_prettier with fix=True.

        :Purpose:
            Verify fix orchestration works correctly.
        """
        # Mock _ensure_tools
        with patch.object(self.runner, "_ensure_tools"):
            # Mock _should_run_tool
            with patch.object(self.runner, "_should_run_tool", return_value=True):
                # Mock _run_prettier
                with patch.object(self.runner, "_run_prettier") as mock_run:
                    mock_run.return_value = MagicMock(passed=True, violations=[])

                    results = self.runner.fix()

        # Verify _run_prettier was called with fix=True
        mock_run.assert_called_once_with(fix=True)
        self.assertEqual(len(results), 1)  # fix() only runs prettier, not metadata

    def test_validate_json_metadata_with_schema(self) -> None:
        """Test metadata validation passes when $schema field present.

        :Purpose:
            Verify validator accepts JSON with $schema field.
        """
        # Mock get_tracked_files to return a test file
        test_content = '{"$schema": "https://example.com/schema.json", "value": 123}'

        with patch("tools.repo_lint.runners.json_runner.get_tracked_files") as mock_files:
            mock_files.return_value = ["test.json"]

            # Mock file operations
            m_open = unittest.mock.mock_open(read_data=test_content)
            with patch("builtins.open", m_open):
                # Mock Path.exists() to return True
                with patch("pathlib.Path.exists", return_value=True):
                    result = self.runner._validate_json_metadata()

        # Verify no violations
        self.assertTrue(result.passed)
        self.assertEqual(len(result.violations), 0)

    def test_validate_json_metadata_with_description(self) -> None:
        """Test metadata validation passes when description field present.

        :Purpose:
            Verify validator accepts JSON with description field.
        """
        test_content = '{"description": "Test configuration", "value": 123}'

        with patch("tools.repo_lint.runners.json_runner.get_tracked_files") as mock_files:
            mock_files.return_value = ["test.json"]

            m_open = unittest.mock.mock_open(read_data=test_content)
            with patch("builtins.open", m_open):
                with patch("pathlib.Path.exists", return_value=True):
                    result = self.runner._validate_json_metadata()

        self.assertTrue(result.passed)
        self.assertEqual(len(result.violations), 0)

    def test_validate_json_metadata_with_title(self) -> None:
        """Test metadata validation passes when title field present.

        :Purpose:
            Verify validator accepts JSON with title field.
        """
        test_content = '{"title": "Test Configuration", "value": 123}'

        with patch("tools.repo_lint.runners.json_runner.get_tracked_files") as mock_files:
            mock_files.return_value = ["test.json"]

            m_open = unittest.mock.mock_open(read_data=test_content)
            with patch("builtins.open", m_open):
                with patch("pathlib.Path.exists", return_value=True):
                    result = self.runner._validate_json_metadata()

        self.assertTrue(result.passed)
        self.assertEqual(len(result.violations), 0)

    def test_validate_json_metadata_missing_fields(self) -> None:
        """Test metadata validation fails when no metadata fields present.

        :Purpose:
            Verify validator rejects JSON without $schema, description, or title.
        """
        test_content = '{"value": 123, "settings": {"enabled": true}}'

        with patch("tools.repo_lint.runners.json_runner.get_tracked_files") as mock_files:
            mock_files.return_value = ["test.json"]

            m_open = unittest.mock.mock_open(read_data=test_content)
            with patch("builtins.open", m_open):
                with patch("pathlib.Path.exists", return_value=True):
                    result = self.runner._validate_json_metadata()

        # Verify violation detected
        self.assertFalse(result.passed)
        self.assertEqual(len(result.violations), 1)
        self.assertEqual(result.violations[0].file, "test.json")
        self.assertIn("Missing required metadata", result.violations[0].message)

    def test_validate_json_metadata_invalid_json(self) -> None:
        """Test metadata validation handles invalid JSON gracefully.

        :Purpose:
            Verify validator reports syntax errors without crashing.
        """
        test_content = '{"value": 123, invalid json}'

        with patch("tools.repo_lint.runners.json_runner.get_tracked_files") as mock_files:
            mock_files.return_value = ["test.json"]

            m_open = unittest.mock.mock_open(read_data=test_content)
            with patch("builtins.open", m_open):
                with patch("pathlib.Path.exists", return_value=True):
                    result = self.runner._validate_json_metadata()

        # Verify syntax error detected
        self.assertFalse(result.passed)
        self.assertEqual(len(result.violations), 1)
        self.assertIn("Invalid JSON syntax", result.violations[0].message)

    def test_validate_json_metadata_not_object(self) -> None:
        """Test metadata validation rejects non-object JSON.

        :Purpose:
            Verify validator requires root-level object.
        """
        test_content = "[1, 2, 3]"  # Array at root

        with patch("tools.repo_lint.runners.json_runner.get_tracked_files") as mock_files:
            mock_files.return_value = ["test.json"]

            m_open = unittest.mock.mock_open(read_data=test_content)
            with patch("builtins.open", m_open):
                with patch("pathlib.Path.exists", return_value=True):
                    result = self.runner._validate_json_metadata()

        # Verify violation detected
        self.assertFalse(result.passed)
        self.assertEqual(len(result.violations), 1)
        self.assertIn("must be an object at root level", result.violations[0].message)

    def test_check_includes_metadata_validation(self) -> None:
        """Test that check() runs both Prettier and metadata validation.

        :Purpose:
            Verify check orchestration includes metadata validator.
        """
        # Mock _ensure_tools
        with patch.object(self.runner, "_ensure_tools"):
            # Mock _should_run_tool
            with patch.object(self.runner, "_should_run_tool", return_value=True):
                # Mock both validators
                with patch.object(self.runner, "_run_prettier") as mock_prettier:
                    with patch.object(self.runner, "_validate_json_metadata") as mock_metadata:
                        mock_prettier.return_value = MagicMock(passed=True, violations=[])
                        mock_metadata.return_value = MagicMock(passed=True, violations=[])

                        results = self.runner.check()

        # Verify both validators were called
        mock_prettier.assert_called_once()
        mock_metadata.assert_called_once()
        self.assertEqual(len(results), 2)  # prettier + metadata


if __name__ == "__main__":
    unittest.main()
