"""Test suite for Phase 2.8: Environment & PATH Management features.

This module tests the environment management commands added in Phase 2.8:
- repo-lint which: Environment diagnostic
- repo-lint env: Shell integration snippet generation
- repo-lint activate: Subshell launcher with venv activation

:Purpose:
    Validate Phase 2.8 implementation of environment and PATH management utilities.
    Tests cover venv resolution, shell detection, PATH snippet generation, and all
    three new CLI commands (which, env, activate).

:Environment Variables:
    None directly used. Tests may set environment variables temporarily via patching
    to test shell detection and config directory resolution.

:Examples:
    Run all Phase 2.8 tests::

        python3 -m pytest tools/repo_lint/tests/test_phase_2_8_features.py -v

    Run specific test class::

        python3 -m pytest tools/repo_lint/tests/test_phase_2_8_features.py::TestWhichCommand -v

:Exit Codes:
    Uses pytest exit codes:
    - 0: All tests passed
    - 1: Tests failed
    - 2: Test execution error
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.repo_lint.env_utils import (
    detect_shell,
    generate_shell_snippet,
    get_user_config_dir,
    get_venv_activate_script,
    get_venv_bin_dir,
    is_in_venv,
    resolve_venv,
)


class TestEnvUtils(unittest.TestCase):
    """Test suite for env_utils module."""

    def test_is_in_venv(self):
        """Test venv detection."""
        # This test runs in actual venv, so should be True
        result = is_in_venv()
        # In actual CI/dev environments, we're likely in a venv
        self.assertIsInstance(result, bool)

    def test_detect_shell(self):
        """Test shell detection."""
        shell = detect_shell()
        # Should return one of the known shell types or "unknown"
        self.assertIn(
            shell,
            ["bash", "zsh", "fish", "powershell", "cmd", "unknown"],
        )

    def test_generate_shell_snippet_bash(self):
        """Test shell snippet generation for bash."""
        venv_path = Path("/tmp/test-venv")
        snippet, ext = generate_shell_snippet(venv_path, "bash")
        self.assertIn("export PATH=", snippet)
        self.assertEqual(ext, ".bash")
        self.assertIn("/tmp/test-venv/bin", snippet)

    def test_generate_shell_snippet_zsh(self):
        """Test shell snippet generation for zsh."""
        venv_path = Path("/tmp/test-venv")
        snippet, ext = generate_shell_snippet(venv_path, "zsh")
        self.assertIn("export PATH=", snippet)
        self.assertEqual(ext, ".zsh")

    def test_generate_shell_snippet_fish(self):
        """Test shell snippet generation for fish."""
        venv_path = Path("/tmp/test-venv")
        snippet, ext = generate_shell_snippet(venv_path, "fish")
        self.assertIn("set -gx PATH", snippet)
        self.assertEqual(ext, ".fish")

    def test_generate_shell_snippet_powershell(self):
        """Test shell snippet generation for powershell."""
        venv_path = Path("/tmp/test-venv")
        snippet, ext = generate_shell_snippet(venv_path, "powershell")
        self.assertIn("$env:PATH", snippet)
        self.assertEqual(ext, ".ps1")

    def test_generate_shell_snippet_cmd(self):
        """Test shell snippet generation for cmd."""
        venv_path = Path("/tmp/test-venv")
        snippet, ext = generate_shell_snippet(venv_path, "cmd")
        self.assertIn("SET PATH=", snippet)
        self.assertEqual(ext, ".bat")

    def test_generate_shell_snippet_unknown_shell(self):
        """Test shell snippet generation with unknown shell type."""
        venv_path = Path("/tmp/test-venv")
        with self.assertRaises(ValueError) as ctx:
            generate_shell_snippet(venv_path, "unknown-shell")
        self.assertIn("Unknown shell type", str(ctx.exception))

    def test_get_venv_bin_dir_unix(self):
        """Test bin directory detection on Unix-like systems."""
        venv_path = Path("/tmp/test-venv")
        with patch("platform.system", return_value="Linux"):
            bin_dir = get_venv_bin_dir(venv_path)
            self.assertEqual(bin_dir, Path("/tmp/test-venv/bin"))

    def test_get_venv_bin_dir_windows(self):
        """Test bin directory detection on Windows."""
        venv_path = Path("C:/test-venv")
        with patch("platform.system", return_value="Windows"):
            bin_dir = get_venv_bin_dir(venv_path)
            self.assertEqual(bin_dir, Path("C:/test-venv/Scripts"))

    def test_get_venv_activate_script_unix(self):
        """Test activate script detection on Unix-like systems."""
        venv_path = Path("/tmp/test-venv")
        with patch("platform.system", return_value="Linux"):
            activate_script = get_venv_activate_script(venv_path)
            self.assertEqual(activate_script, Path("/tmp/test-venv/bin/activate"))

    def test_get_venv_activate_script_windows(self):
        """Test activate script detection on Windows."""
        venv_path = Path("C:/test-venv")
        with patch("platform.system", return_value="Windows"):
            activate_script = get_venv_activate_script(venv_path)
            self.assertEqual(activate_script, Path("C:/test-venv/Scripts/Activate.ps1"))

    def test_get_user_config_dir_unix(self):
        """Test user config directory on Unix-like systems."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("platform.system", return_value="Linux"):
                with patch.dict("os.environ", {"HOME": tmpdir}, clear=True):
                    config_dir = get_user_config_dir()
                    # Should create and return the directory
                    self.assertTrue(str(config_dir).endswith("repo-lint"))
                    self.assertTrue(config_dir.exists())

    def test_resolve_venv_explicit(self):
        """Test venv resolution with explicit path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            venv_path = Path(tmpdir) / "test-venv"
            venv_path.mkdir()
            # Create minimal venv structure
            bin_dir = venv_path / "bin"
            bin_dir.mkdir()
            (bin_dir / "python").touch()

            resolved = resolve_venv(explicit_venv=venv_path)
            self.assertEqual(resolved, venv_path)

    def test_resolve_venv_nonexistent(self):
        """Test venv resolution with nonexistent explicit path."""
        with self.assertRaises(RuntimeError) as ctx:
            resolve_venv(explicit_venv=Path("/nonexistent/venv"))
        self.assertIn("does not exist", str(ctx.exception))


class TestWhichCommand(unittest.TestCase):
    """Test suite for 'repo-lint which' command."""

    def test_which_command_exists(self):
        """Test that 'repo-lint which' command exists."""
        result = subprocess.run(
            ["repo-lint", "which", "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("Show repo-lint environment", result.stdout)

    def test_which_command_output(self):
        """Test 'repo-lint which' produces output."""
        result = subprocess.run(
            ["repo-lint", "which"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("repo-lint Environment Information", result.stdout)
        self.assertIn("Repository root", result.stdout)

    def test_which_command_json_output(self):
        """Test 'repo-lint which --json' produces valid JSON."""
        result = subprocess.run(
            ["repo-lint", "which", "--json"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)

        # Parse JSON output
        data = json.loads(result.stdout)
        self.assertIn("repo_root", data)
        self.assertIn("venv_path", data)
        self.assertIn("detected_shell", data)
        self.assertIn("in_venv", data)


class TestEnvCommand(unittest.TestCase):
    """Test suite for 'repo-lint env' command."""

    def test_env_command_exists(self):
        """Test that 'repo-lint env' command exists."""
        result = subprocess.run(
            ["repo-lint", "env", "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("Generate shell integration snippet", result.stdout)

    def test_env_command_output(self):
        """Test 'repo-lint env' produces output."""
        result = subprocess.run(
            ["repo-lint", "env"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("Shell Integration Snippet", result.stdout)
        # Should contain PATH export/set
        self.assertTrue(
            "export PATH=" in result.stdout or "set -gx PATH" in result.stdout or "$env:PATH" in result.stdout
        )

    def test_env_command_path_only(self):
        """Test 'repo-lint env --path-only' produces only PATH line."""
        result = subprocess.run(
            ["repo-lint", "env", "--path-only"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        # Should be a single line with PATH
        lines = [line for line in result.stdout.strip().split("\n") if line.strip()]
        self.assertEqual(len(lines), 1)
        # Should contain PATH
        self.assertTrue("PATH=" in result.stdout or "PATH" in result.stdout)

    def test_env_command_with_shell(self):
        """Test 'repo-lint env --shell bash' specifies shell."""
        result = subprocess.run(
            ["repo-lint", "env", "--shell", "bash"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("export PATH=", result.stdout)


class TestActivateCommand(unittest.TestCase):
    """Test suite for 'repo-lint activate' command."""

    def test_activate_command_exists(self):
        """Test that 'repo-lint activate' command exists."""
        result = subprocess.run(
            ["repo-lint", "activate", "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("Launch subshell with repo-lint venv activated", result.stdout)

    def test_activate_print_mode(self):
        """Test 'repo-lint activate --print' shows command."""
        result = subprocess.run(
            ["repo-lint", "activate", "--print"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        # Should contain shell command
        self.assertTrue(
            "bash" in result.stdout or "zsh" in result.stdout or "fish" in result.stdout or "pwsh" in result.stdout
        )

    def test_activate_with_command(self):
        """Test 'repo-lint activate --command' runs command."""
        result = subprocess.run(
            ["repo-lint", "activate", "--command", "echo test"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("test", result.stdout)

    def test_activate_ci_mode_requires_command(self):
        """Test 'repo-lint activate --ci' requires --command."""
        result = subprocess.run(
            ["repo-lint", "activate", "--ci"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("--ci mode requires --command", result.stderr)

    def test_activate_ci_mode_with_command(self):
        """Test 'repo-lint activate --ci --command' works."""
        result = subprocess.run(
            ["repo-lint", "activate", "--ci", "--command", "echo ci-test"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("ci-test", result.stdout)


if __name__ == "__main__":
    unittest.main()
