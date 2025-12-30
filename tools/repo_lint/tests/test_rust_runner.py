#!/usr/bin/env python3
"""Tests for Rust language runner.

:Purpose:
    Validate RustRunner functionality including file detection, tool checking,
    linting, formatting, and docstring validation.

:Environment Variables:
    None

:Examples:
    Run tests::

        pytest tools/repo_lint/tests/test_rust_runner.py -v

:Exit Codes:
    Pytest exit codes (0 = success, 1+ = failures)
"""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tools.repo_lint.common import LintResult
from tools.repo_lint.runners.rust_runner import RustRunner


@pytest.fixture
def mock_repo_root(tmp_path):
    """Create a mock repository root with Rust structure.

    :param tmp_path: Pytest temporary directory fixture
    :returns: Path to mock repository root
    """
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    # Create rust/ directory
    rust_dir = repo_root / "rust"
    rust_dir.mkdir()

    # Create Cargo.toml
    cargo_toml = rust_dir / "Cargo.toml"
    cargo_toml.write_text(
        """[package]
name = "test"
version = "0.1.0"

[dependencies]
"""
    )

    # Create src/ directory with main.rs
    src_dir = rust_dir / "src"
    src_dir.mkdir()

    main_rs = src_dir / "main.rs"
    main_rs.write_text(
        """//! Test module
//!
//! # Purpose
//! Testing
//!
//! # Examples
//! None
//!
//! # Exit Codes
//! 0 = success

fn main() {
    println!("Hello");
}
"""
    )

    return repo_root


@pytest.fixture
def rust_runner(mock_repo_root):
    """Create a RustRunner instance for testing.

    :param mock_repo_root: Mock repository root fixture
    :returns: RustRunner instance
    """
    return RustRunner(repo_root=mock_repo_root, verbose=False)


class TestRustRunnerFileDetection:
    """Test suite for Rust file detection."""

    def test_has_files_with_rust_files(self, rust_runner, mock_repo_root):
        """Test has_files returns True when Rust files exist.

        :param rust_runner: RustRunner fixture
        :param mock_repo_root: Mock repository root
        """
        # Initialize git repo
        subprocess.run(["git", "init"], cwd=mock_repo_root, check=True, capture_output=True)
        subprocess.run(["git", "add", "."], cwd=mock_repo_root, check=True, capture_output=True)

        assert rust_runner.has_files() is True

    def test_has_files_without_rust_files(self, tmp_path):
        """Test has_files returns False when no Rust files exist.

        :param tmp_path: Pytest temporary directory
        """
        repo_root = tmp_path / "empty"
        repo_root.mkdir()

        # Initialize git repo
        subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True)

        runner = RustRunner(repo_root=repo_root, verbose=False)
        assert runner.has_files() is False


class TestRustRunnerToolChecking:
    """Test suite for Rust tool availability checking."""

    @patch("tools.repo_lint.runners.base.command_exists")
    @patch("subprocess.run")
    def test_check_tools_all_present(self, mock_run, mock_command_exists, rust_runner):
        """Test check_tools when all tools are available.

        :param mock_run: Mock subprocess.run
        :param mock_command_exists: Mock command_exists function
        :param rust_runner: RustRunner fixture
        """
        # Mock all tools as present
        mock_command_exists.return_value = True
        mock_run.return_value = MagicMock(returncode=0)

        missing = rust_runner.check_tools()
        assert missing == []

    @patch("tools.repo_lint.runners.base.command_exists")
    @patch("subprocess.run")
    def test_check_tools_cargo_missing(self, mock_run, mock_command_exists, rust_runner):
        """Test check_tools when cargo is missing.

        :param mock_run: Mock subprocess.run
        :param mock_command_exists: Mock command_exists function
        :param rust_runner: RustRunner fixture
        """

        def command_exists_side_effect(cmd):
            return cmd != "cargo"

        mock_command_exists.side_effect = command_exists_side_effect
        # Mock cargo clippy version check to fail (since cargo isn't available)
        mock_run.return_value = MagicMock(returncode=1)

        missing = rust_runner.check_tools()
        # When cargo is missing, both cargo and clippy will be reported missing
        assert "cargo" in missing or len(missing) > 0

    @patch("tools.repo_lint.runners.base.command_exists")
    @patch("subprocess.run")
    def test_check_tools_clippy_missing(self, mock_run, mock_command_exists, rust_runner):
        """Test check_tools when clippy is missing.

        :param mock_run: Mock subprocess.run
        :param mock_command_exists: Mock command_exists function
        :param rust_runner: RustRunner fixture
        """
        mock_command_exists.return_value = True
        # Clippy version check fails
        mock_run.return_value = MagicMock(returncode=1)

        missing = rust_runner.check_tools()
        assert "clippy" in missing


class TestRustRunnerFormatting:
    """Test suite for rustfmt functionality."""

    @patch("subprocess.run")
    def test_rustfmt_check_passes(self, mock_run, rust_runner):
        """Test rustfmt check when code is properly formatted.

        :param mock_run: Mock subprocess.run
        :param rust_runner: RustRunner fixture
        """
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        result = rust_runner._run_rustfmt_check()  # pylint: disable=protected-access

        assert isinstance(result, LintResult)
        assert result.tool == "rustfmt"
        assert result.passed is True
        assert len(result.violations) == 0

    @patch("subprocess.run")
    def test_rustfmt_check_fails(self, mock_run, rust_runner):
        """Test rustfmt check when code needs formatting.

        :param mock_run: Mock subprocess.run
        :param rust_runner: RustRunner fixture
        """
        mock_run.return_value = MagicMock(
            returncode=1, stdout="Diff in src/main.rs at line 10\nDiff in src/lib.rs at line 5", stderr=""
        )

        result = rust_runner._run_rustfmt_check()  # pylint: disable=protected-access

        assert isinstance(result, LintResult)
        assert result.tool == "rustfmt"
        assert result.passed is False
        assert len(result.violations) == 2

    @patch("subprocess.run")
    def test_rustfmt_fix_success(self, mock_run, rust_runner):
        """Test rustfmt fix mode succeeds.

        :param mock_run: Mock subprocess.run
        :param rust_runner: RustRunner fixture
        """
        # First call: cargo fmt (fix)
        # Second call: cargo clippy (check)
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="", stderr=""),  # cargo fmt
            MagicMock(returncode=0, stdout="", stderr=""),  # cargo clippy
        ]

        results = rust_runner.fix()

        assert len(results) == 2
        assert results[0].tool == "rustfmt"
        assert results[0].passed is True

    def test_rustfmt_no_rust_directory(self, tmp_path):
        """Test rustfmt when rust/ directory doesn't exist.

        :param tmp_path: Pytest temporary directory
        """
        repo_root = tmp_path / "no_rust"
        repo_root.mkdir()

        runner = RustRunner(repo_root=repo_root, verbose=False)
        result = runner._run_rustfmt_check()  # pylint: disable=protected-access

        assert result.tool == "rustfmt"
        assert result.passed is True


class TestRustRunnerClippy:
    """Test suite for clippy linting."""

    @patch("subprocess.run")
    def test_clippy_passes(self, mock_run, rust_runner):
        """Test clippy when no warnings are found.

        :param mock_run: Mock subprocess.run
        :param rust_runner: RustRunner fixture
        """
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        result = rust_runner._run_clippy()  # pylint: disable=protected-access

        assert isinstance(result, LintResult)
        assert result.tool == "clippy"
        assert result.passed is True
        assert len(result.violations) == 0

    @patch("subprocess.run")
    def test_clippy_json_output_parsing(self, mock_run, rust_runner):
        """Test clippy JSON output parsing with structured violations.

        :param mock_run: Mock subprocess.run
        :param rust_runner: RustRunner fixture
        """
        json_output = """{"reason":"compiler-message","package_id":"test 0.1.0","target":{},"message":{"message":"unused variable: `x`","code":{"code":"unused_variables","explanation":""},"level":"warning","spans":[{"file_name":"src/main.rs","byte_start":100,"byte_end":101,"line_start":5,"line_end":5,"column_start":9,"column_end":10,"is_primary":true,"text":[{"text":"    let x = 5;","highlight_start":9,"highlight_end":10}],"label":"unused variable","suggested_replacement":null,"suggestion_applicability":null,"expansion":null}],"children":[],"rendered":"warning: unused variable: `x`\\n"}}
"""
        mock_run.return_value = MagicMock(returncode=1, stdout=json_output, stderr="")

        result = rust_runner._run_clippy()  # pylint: disable=protected-access

        assert isinstance(result, LintResult)
        assert result.tool == "clippy"
        assert result.passed is False
        assert len(result.violations) >= 1

        # Check first violation has structured data
        violation = result.violations[0]
        assert violation.file == "src/main.rs"
        assert violation.line == 5
        assert "unused" in violation.message.lower()

    @patch("subprocess.run")
    def test_clippy_fallback_text_parsing(self, mock_run, rust_runner):
        """Test clippy falls back to text parsing when JSON fails.

        :param mock_run: Mock subprocess.run
        :param rust_runner: RustRunner fixture
        """
        text_output = "warning: unused variable\nerror: mismatched types\n"
        mock_run.return_value = MagicMock(returncode=1, stdout=text_output, stderr="")

        result = rust_runner._run_clippy()  # pylint: disable=protected-access

        assert isinstance(result, LintResult)
        assert result.tool == "clippy"
        assert result.passed is False
        # Should have violations from fallback parsing
        assert len(result.violations) >= 1


class TestRustRunnerDocstrings:
    """Test suite for Rust docstring validation."""

    @patch("subprocess.run")
    def test_docstring_validation_passes(self, mock_run, rust_runner):
        """Test docstring validation when all docstrings are present.

        :param mock_run: Mock subprocess.run
        :param rust_runner: RustRunner fixture
        """
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        result = rust_runner._run_docstring_validation()  # pylint: disable=protected-access

        assert isinstance(result, LintResult)
        assert result.tool == "rust-docstrings"
        assert result.passed is True
        assert len(result.violations) == 0

    @patch("subprocess.run")
    @patch("pathlib.Path.exists")
    def test_docstring_validation_fails(self, mock_exists, mock_run, rust_runner):
        """Test docstring validation when docstrings are missing.

        :param mock_exists: Mock Path.exists
        :param mock_run: Mock subprocess.run
        :param rust_runner: RustRunner fixture
        """
        # Mock rust/ directory and validator script exist
        mock_exists.return_value = True

        output = """Checking Rust files for docstring compliance...
rust/src/main.rs: Missing docstring for function 'helper'
rust/src/lib.rs: Missing module-level documentation
"""
        mock_run.return_value = MagicMock(returncode=1, stdout=output, stderr="")

        result = rust_runner._run_docstring_validation()  # pylint: disable=protected-access

        assert isinstance(result, LintResult)
        assert result.tool == "rust-docstrings"
        assert result.passed is False
        assert len(result.violations) == 2

        # Check violation details
        assert result.violations[0].file == "rust/src/main.rs"
        assert "helper" in result.violations[0].message

    def test_docstring_validation_no_rust_directory(self, tmp_path):
        """Test docstring validation when rust/ directory doesn't exist.

        :param tmp_path: Pytest temporary directory
        """
        repo_root = tmp_path / "no_rust"
        repo_root.mkdir()

        runner = RustRunner(repo_root=repo_root, verbose=False)
        result = runner._run_docstring_validation()  # pylint: disable=protected-access

        assert result.tool == "rust-docstrings"
        assert result.passed is True


class TestRustRunnerIntegration:
    """Integration tests for RustRunner."""

    @patch("tools.repo_lint.runners.base.command_exists")
    @patch("subprocess.run")
    def test_check_runs_all_tools(self, mock_run, mock_command_exists, rust_runner):
        """Test check() runs all linting tools.

        :param mock_run: Mock subprocess.run
        :param mock_command_exists: Mock command_exists function
        :param rust_runner: RustRunner fixture
        """
        mock_command_exists.return_value = True
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        results = rust_runner.check()

        # Should run rustfmt, clippy, and docstring validation
        assert len(results) == 3
        tools = [r.tool for r in results]
        assert "rustfmt" in tools
        assert "clippy" in tools
        assert "rust-docstrings" in tools

    @patch("tools.repo_lint.runners.base.command_exists")
    @patch("subprocess.run")
    def test_fix_runs_formatter_and_checks(self, mock_run, mock_command_exists, rust_runner):
        """Test fix() runs formatter and re-checks.

        :param mock_run: Mock subprocess.run
        :param mock_command_exists: Mock command_exists function
        :param rust_runner: RustRunner fixture
        """
        mock_command_exists.return_value = True
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        results = rust_runner.fix()

        # Should run rustfmt (fix) and clippy (check)
        assert len(results) == 2
        assert results[0].tool == "rustfmt"
        assert results[1].tool == "clippy"
