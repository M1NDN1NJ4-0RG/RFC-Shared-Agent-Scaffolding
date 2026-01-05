"""Unit tests for virtual environment resolution utilities.

This module tests the venv_resolver module to ensure correct virtual
environment detection and resolution across platforms.

:Purpose:
    Validate venv_resolver functionality with comprehensive unit tests.
    Tests cover precedence rules, cross-platform behavior, and error handling.

:Environment Variables:
    None. Tests use mocking for environment simulation.

:Examples:
    Run tests with::

        python3 -m unittest tools.repo_lint.tests.test_venv_resolver

:Exit Codes:
    Standard unittest exit codes (0 for success, 1 for failures).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.repo_lint.env.venv_resolver import (
    VenvNotFoundError,
    get_activation_script,
    get_current_venv,
    get_venv_bin_dir,
    is_venv_active,
    resolve_venv,
)


class TestVenvActive(unittest.TestCase):
    """Test virtual environment activation detection."""

    def test_is_venv_active_when_active(self):
        """Test is_venv_active returns True when venv is active."""
        # sys.prefix != sys.base_prefix indicates venv is active
        with patch("tools.repo_lint.env.venv_resolver.sys.prefix", "/venv"):
            with patch("tools.repo_lint.env.venv_resolver.sys.base_prefix", "/usr"):
                self.assertTrue(is_venv_active())

    def test_is_venv_active_when_not_active(self):
        """Test is_venv_active returns False when venv is not active."""
        # sys.prefix == sys.base_prefix indicates no venv
        with patch("tools.repo_lint.env.venv_resolver.sys.prefix", "/usr"):
            with patch("tools.repo_lint.env.venv_resolver.sys.base_prefix", "/usr"):
                self.assertFalse(is_venv_active())


class TestGetCurrentVenv(unittest.TestCase):
    """Test current virtual environment detection."""

    def test_get_current_venv_when_active(self):
        """Test get_current_venv returns venv path when active."""
        with patch("tools.repo_lint.env.venv_resolver.sys.prefix", "/venv"):
            with patch("tools.repo_lint.env.venv_resolver.sys.base_prefix", "/usr"):
                venv = get_current_venv()
                self.assertIsNotNone(venv)
                self.assertEqual(venv, Path("/venv"))

    def test_get_current_venv_when_not_active(self):
        """Test get_current_venv returns None when not active."""
        with patch("tools.repo_lint.env.venv_resolver.sys.prefix", "/usr"):
            with patch("tools.repo_lint.env.venv_resolver.sys.base_prefix", "/usr"):
                venv = get_current_venv()
                self.assertIsNone(venv)


class TestGetVenvBinDir(unittest.TestCase):
    """Test bin/Scripts directory resolution."""

    def test_get_venv_bin_dir_unix(self):
        """Test bin directory on Unix-like systems."""
        with patch("tools.repo_lint.env.venv_resolver.sys.platform", "linux"):
            venv_path = Path("/home/user/.venv")
            bin_dir = get_venv_bin_dir(venv_path)
            self.assertEqual(bin_dir, Path("/home/user/.venv/bin"))

    def test_get_venv_bin_dir_windows(self):
        """Test Scripts directory on Windows."""
        with patch("tools.repo_lint.env.venv_resolver.sys.platform", "win32"):
            venv_path = Path("C:/Users/user/.venv")
            bin_dir = get_venv_bin_dir(venv_path)
            self.assertEqual(bin_dir, Path("C:/Users/user/.venv/Scripts"))


class TestGetActivationScript(unittest.TestCase):
    """Test activation script path resolution."""

    def test_activation_script_default_unix(self):
        """Test default activation script on Unix."""
        with patch("tools.repo_lint.env.venv_resolver.sys.platform", "linux"):
            venv_path = Path("/home/user/.venv")
            script = get_activation_script(venv_path)
            self.assertEqual(script, Path("/home/user/.venv/bin/activate"))

    def test_activation_script_default_windows(self):
        """Test default activation script on Windows."""
        with patch("tools.repo_lint.env.venv_resolver.sys.platform", "win32"):
            venv_path = Path("C:/Users/user/.venv")
            script = get_activation_script(venv_path)
            self.assertEqual(script, Path("C:/Users/user/.venv/Scripts/activate.bat"))

    def test_activation_script_bash(self):
        """Test bash activation script."""
        with patch("tools.repo_lint.env.venv_resolver.sys.platform", "linux"):
            venv_path = Path("/home/user/.venv")
            script = get_activation_script(venv_path, shell="bash")
            self.assertEqual(script, Path("/home/user/.venv/bin/activate"))

    def test_activation_script_zsh(self):
        """Test zsh activation script."""
        with patch("tools.repo_lint.env.venv_resolver.sys.platform", "linux"):
            venv_path = Path("/home/user/.venv")
            script = get_activation_script(venv_path, shell="zsh")
            self.assertEqual(script, Path("/home/user/.venv/bin/activate"))

    def test_activation_script_fish(self):
        """Test fish activation script."""
        with patch("tools.repo_lint.env.venv_resolver.sys.platform", "linux"):
            venv_path = Path("/home/user/.venv")
            script = get_activation_script(venv_path, shell="fish")
            self.assertEqual(script, Path("/home/user/.venv/bin/activate.fish"))

    def test_activation_script_fish_on_windows_raises(self):
        """Test fish activation script on Windows raises ValueError."""
        with patch("tools.repo_lint.env.venv_resolver.sys.platform", "win32"):
            venv_path = Path("C:/Users/user/.venv")
            with self.assertRaises(ValueError) as ctx:
                get_activation_script(venv_path, shell="fish")
            self.assertIn("Fish shell is not supported on Windows", str(ctx.exception))

    def test_activation_script_powershell(self):
        """Test PowerShell activation script."""
        with patch("tools.repo_lint.env.venv_resolver.sys.platform", "linux"):
            venv_path = Path("/home/user/.venv")
            script = get_activation_script(venv_path, shell="powershell")
            self.assertEqual(script, Path("/home/user/.venv/bin/Activate.ps1"))

    def test_activation_script_cmd(self):
        """Test CMD activation script."""
        with patch("tools.repo_lint.env.venv_resolver.sys.platform", "win32"):
            venv_path = Path("C:/Users/user/.venv")
            script = get_activation_script(venv_path, shell="cmd")
            self.assertEqual(script, Path("C:/Users/user/.venv/Scripts/activate.bat"))

    def test_activation_script_cmd_on_unix_raises(self):
        """Test CMD activation script on Unix raises ValueError."""
        with patch("tools.repo_lint.env.venv_resolver.sys.platform", "linux"):
            venv_path = Path("/home/user/.venv")
            with self.assertRaises(ValueError) as ctx:
                get_activation_script(venv_path, shell="cmd")
            self.assertIn("CMD is only supported on Windows", str(ctx.exception))

    def test_activation_script_unsupported_shell_raises(self):
        """Test unsupported shell raises ValueError."""
        venv_path = Path("/home/user/.venv")
        with self.assertRaises(ValueError) as ctx:
            get_activation_script(venv_path, shell="tcsh")
        self.assertIn("Unsupported shell: tcsh", str(ctx.exception))


class TestResolveVenv(unittest.TestCase):
    """Test virtual environment resolution with precedence rules."""

    def test_resolve_venv_explicit_path(self):
        """Test explicit --venv flag takes highest priority."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a minimal venv structure for testing
            # Note: We create empty files rather than real executables
            # since we only need to test the validation logic, not actual execution
            venv_path = Path(tmpdir) / "custom_venv"
            venv_path.mkdir()
            bin_dir = venv_path / "bin"
            bin_dir.mkdir()
            (bin_dir / "python").touch()

            result = resolve_venv(explicit_path=str(venv_path))
            self.assertEqual(result, venv_path.resolve())

    def test_resolve_venv_explicit_path_not_exists(self):
        """Test explicit path that doesn't exist raises error."""
        with self.assertRaises(VenvNotFoundError) as ctx:
            resolve_venv(explicit_path="/nonexistent/venv")
        self.assertIn("does not exist", str(ctx.exception))

    def test_resolve_venv_explicit_path_not_valid_venv(self):
        """Test explicit path that exists but is not a venv raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create directory but no Python executable
            venv_path = Path(tmpdir) / "not_a_venv"
            venv_path.mkdir()
            with self.assertRaises(VenvNotFoundError) as ctx:
                resolve_venv(explicit_path=str(venv_path))
            self.assertIn("not a valid virtual environment", str(ctx.exception))

    def test_resolve_venv_repo_root_dotenv(self):
        """Test .venv/ under repo root with valid structure.

        This test validates that .venv directory under repo root is detected
        and properly validated for containing a Python executable.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            venv_path = repo_root / ".venv"
            venv_path.mkdir()
            # Create minimal venv structure with Python executable
            bin_dir = venv_path / "bin"
            bin_dir.mkdir()
            (bin_dir / "python").touch()

            result = resolve_venv(repo_root=repo_root)
            self.assertEqual(result, venv_path)

    def test_resolve_venv_current_venv(self):
        """Test currently active venv takes third priority."""
        with patch("tools.repo_lint.env.venv_resolver.sys.prefix", "/active/venv"):
            with patch("tools.repo_lint.env.venv_resolver.sys.base_prefix", "/usr"):
                result = resolve_venv()
                self.assertEqual(result, Path("/active/venv"))

    def test_resolve_venv_no_venv_found_raises(self):
        """Test error when no venv can be resolved."""
        with patch("tools.repo_lint.env.venv_resolver.sys.prefix", "/usr"):
            with patch("tools.repo_lint.env.venv_resolver.sys.base_prefix", "/usr"):
                with tempfile.TemporaryDirectory() as tmpdir:
                    repo_root = Path(tmpdir)
                    # No .venv/ exists, not in active venv
                    with self.assertRaises(VenvNotFoundError) as ctx:
                        resolve_venv(repo_root=repo_root)
                    self.assertIn("No virtual environment found", str(ctx.exception))

    def test_resolve_venv_precedence_explicit_over_repo(self):
        """Test explicit path takes precedence over repo .venv."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create repo .venv
            repo_root = Path(tmpdir) / "repo"
            repo_root.mkdir()
            repo_venv = repo_root / ".venv"
            repo_venv.mkdir()

            # Create explicit venv
            explicit_venv = Path(tmpdir) / "explicit"
            explicit_venv.mkdir()
            bin_dir = explicit_venv / "bin"
            bin_dir.mkdir()
            (bin_dir / "python").touch()

            result = resolve_venv(explicit_path=str(explicit_venv), repo_root=repo_root)
            self.assertEqual(result, explicit_venv.resolve())

    def test_resolve_venv_precedence_repo_over_current(self):
        """Test repo .venv takes precedence over current venv."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            venv_path = repo_root / ".venv"
            venv_path.mkdir()
            # Create minimal venv structure with Python executable
            bin_dir = venv_path / "bin"
            bin_dir.mkdir()
            (bin_dir / "python").touch()

            with patch("tools.repo_lint.env.venv_resolver.sys.prefix", "/other/venv"):
                with patch("tools.repo_lint.env.venv_resolver.sys.base_prefix", "/usr"):
                    result = resolve_venv(repo_root=repo_root)
                    # Should return repo .venv, not current venv
                    self.assertEqual(result, venv_path)


if __name__ == "__main__":
    unittest.main()
