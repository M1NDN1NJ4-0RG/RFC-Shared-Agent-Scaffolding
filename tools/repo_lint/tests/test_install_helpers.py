#!/usr/bin/env python3
# pylint: disable=wrong-import-position,protected-access,unused-variable  # Test file needs special setup
"""Unit tests for install module (install/cleanup functionality).

:Purpose:
    Validates install_helpers.py functionality including:
    - Virtual environment creation
    - Python tool installation with pinned versions
    - Cleanup of repo-local installations
    - Error handling and verbose output

:Test Coverage:
    - create_venv() creates venv and upgrades pip to pinned version
    - install_python_tools() installs tools with correct versions
    - cleanup_repo_local() removes only repo-local directories
    - Error handling for failed installations
    - Platform-specific path handling (Windows vs Unix)

:Usage:
    Run tests from repository root::

        python3 -m pytest tools/repo_lint/tests/test_install_helpers.py
        # or
        python3 tools/repo_lint/tests/test_install_helpers.py

:Environment Variables:
    None. Tests are self-contained with mocked subprocess calls.

:Exit Codes:
    0
        All tests passed
    1
        One or more tests failed

:Examples:
    Run all tests::

        python3 -m pytest tools/repo_lint/tests/test_install_helpers.py -v

    Run specific test::

        python3 -m pytest tools/repo_lint/tests/test_install_helpers.py::TestInstallHelpers::test_create_venv_success -v

:Notes:
    - Tests use unittest.mock to avoid filesystem operations
    - Tests verify subprocess arguments and error handling
    - Tests validate pip version pinning per Phase 4 requirements
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add repo_lint parent directory to path for imports
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))

from tools.repo_lint.install.install_helpers import (  # noqa: E402
    cleanup_repo_local,
    create_venv,
    get_tools_path,
    get_venv_path,
    install_python_tools,
    venv_exists,
)
from tools.repo_lint.install.version_pins import PIP_VERSION, PYTHON_TOOLS  # noqa: E402


class TestVenvHelpers(unittest.TestCase):
    """Test virtual environment helper functions.

    :Purpose:
        Validates venv path helpers and existence checks.
    """

    @patch("tools.repo_lint.install.install_helpers.get_repo_root")
    def test_get_venv_path(self, mock_get_repo_root):
        """Test get_venv_path returns correct path.

        :Purpose:
            Verify venv path is repo_root/.venv-lint

        :param mock_get_repo_root: Mocked dependency for testing
        """
        mock_get_repo_root.return_value = Path("/fake/repo")
        venv_path = get_venv_path()
        self.assertEqual(venv_path, Path("/fake/repo/.venv-lint"))

    @patch("tools.repo_lint.install.install_helpers.get_repo_root")
    def test_get_tools_path(self, mock_get_repo_root):
        """Test get_tools_path returns correct path.

        :Purpose:
            Verify tools path is repo_root/.tools

        :param mock_get_repo_root: Mocked dependency for testing
        """
        mock_get_repo_root.return_value = Path("/fake/repo")
        tools_path = get_tools_path()
        self.assertEqual(tools_path, Path("/fake/repo/.tools"))

    @patch("tools.repo_lint.install.install_helpers.get_venv_path")
    def test_venv_exists_when_present(self, mock_get_venv_path):
        """Test venv_exists returns True when venv exists.

        :Purpose:
            Verify venv detection works correctly

        :param mock_get_venv_path: Mocked dependency for testing
        """
        # Mock venv path
        mock_venv = MagicMock()
        mock_venv.exists.return_value = True
        mock_get_venv_path.return_value = mock_venv

        # Mock python executable exists
        with patch("sys.platform", "linux"):
            mock_python = MagicMock()
            mock_python.exists.return_value = True
            mock_venv.__truediv__ = lambda self, path: mock_python if "bin/python" in str(path) else MagicMock()

            result = venv_exists()
            self.assertTrue(result)

    @patch("tools.repo_lint.install.install_helpers.get_venv_path")
    def test_venv_exists_when_missing(self, mock_get_venv_path):
        """Test venv_exists returns False when venv doesn't exist.

        :Purpose:
            Verify venv detection handles missing venv

        :param mock_get_venv_path: Mocked dependency for testing
        """
        mock_venv = MagicMock()
        mock_venv.exists.return_value = False
        mock_get_venv_path.return_value = mock_venv

        result = venv_exists()
        self.assertFalse(result)


class TestCreateVenv(unittest.TestCase):
    """Test virtual environment creation.

    :Purpose:
        Validates create_venv creates venv and upgrades pip correctly.
    """

    @patch("tools.repo_lint.install.install_helpers.venv_exists")
    @patch("tools.repo_lint.install.install_helpers.get_venv_path")
    @patch("tools.repo_lint.install.install_helpers.subprocess.run")
    @patch("sys.platform", "linux")
    def test_create_venv_success(self, mock_run, mock_get_venv_path, mock_venv_exists):
        """Test create_venv creates venv and upgrades pip.

        :Purpose:
            Verify venv creation and pip upgrade with pinned version
        :param mock_run: Mocked dependency for testing
        :param mock_get_venv_path: Mocked dependency for testing
        :param mock_venv_exists: Mocked dependency for testing
        """
        mock_venv_exists.return_value = False
        mock_get_venv_path.return_value = Path("/fake/repo/.venv-lint")
        mock_run.return_value = MagicMock(returncode=0)

        success, error = create_venv(verbose=False)

        self.assertTrue(success)
        self.assertIsNone(error)

        # Verify subprocess calls
        self.assertEqual(mock_run.call_count, 2)

        # First call: create venv
        first_call = mock_run.call_args_list[0]
        self.assertIn("-m", first_call[0][0])
        self.assertIn("venv", first_call[0][0])

        # Second call: upgrade pip to pinned version
        second_call = mock_run.call_args_list[1]
        self.assertIn("pip", second_call[0][0])
        self.assertIn(f"pip=={PIP_VERSION}", second_call[0][0])

    @patch("tools.repo_lint.install.install_helpers.venv_exists")
    @patch("tools.repo_lint.install.install_helpers.get_venv_path")
    def test_create_venv_already_exists(self, mock_get_venv_path, mock_venv_exists):
        """Test create_venv skips if venv already exists.

        :Purpose:
            Verify venv creation is skipped when venv exists
        :param mock_get_venv_path: Mocked dependency for testing
        :param mock_venv_exists: Mocked dependency for testing
        """
        mock_venv_exists.return_value = True
        mock_get_venv_path.return_value = Path("/fake/repo/.venv-lint")

        success, error = create_venv(verbose=True)

        self.assertTrue(success)
        self.assertIsNone(error)

    @patch("tools.repo_lint.install.install_helpers.venv_exists")
    @patch("tools.repo_lint.install.install_helpers.get_venv_path")
    @patch("tools.repo_lint.install.install_helpers.subprocess.run")
    @patch("sys.platform", "win32")
    def test_create_venv_windows_paths(self, mock_run, mock_get_venv_path, mock_venv_exists):
        """Test create_venv uses Windows-specific paths.

        :Purpose:
            Verify correct paths on Windows platform
        :param mock_run: Mocked dependency for testing
        :param mock_get_venv_path: Mocked dependency for testing
        :param mock_venv_exists: Mocked dependency for testing
        """
        mock_venv_exists.return_value = False
        mock_get_venv_path.return_value = Path("C:/fake/repo/.venv-lint")
        mock_run.return_value = MagicMock(returncode=0)

        success, error = create_venv(verbose=False)

        self.assertTrue(success)

        # Verify Windows python path used (Scripts/python.exe)
        second_call = mock_run.call_args_list[1]
        python_path = str(second_call[0][0][0])
        self.assertIn("Scripts", python_path)
        self.assertIn("python.exe", python_path)


class TestInstallPythonTools(unittest.TestCase):
    """Test Python tool installation.

    :Purpose:
        Validates install_python_tools installs tools with pinned versions.
    """

    @patch("tools.repo_lint.install.install_helpers.create_venv")
    @patch("tools.repo_lint.install.install_helpers.get_venv_path")
    @patch("tools.repo_lint.install.install_helpers.subprocess.run")
    @patch("sys.platform", "linux")
    def test_install_python_tools_success(self, mock_run, mock_get_venv_path, mock_create_venv):
        """Test install_python_tools installs all tools.

        :Purpose:
            Verify all Python tools are installed with correct versions
        :param mock_run: Mocked dependency for testing
        :param mock_get_venv_path: Mocked dependency for testing
        :param mock_create_venv: Mocked dependency for testing
        """
        mock_create_venv.return_value = (True, None)
        mock_get_venv_path.return_value = Path("/fake/repo/.venv-lint")
        mock_run.return_value = MagicMock(returncode=0)

        success, errors = install_python_tools(verbose=False)

        self.assertTrue(success)
        self.assertEqual(len(errors), 0)

        # Verify each tool was installed with pinned version
        self.assertEqual(mock_run.call_count, len(PYTHON_TOOLS))

        for i, (tool, version) in enumerate(PYTHON_TOOLS.items()):
            call_args = mock_run.call_args_list[i][0][0]
            self.assertIn("pip", str(call_args[0]))
            self.assertIn("install", call_args)
            self.assertIn(f"{tool}=={version}", call_args)

    @patch("tools.repo_lint.install.install_helpers.create_venv")
    @patch("tools.repo_lint.install.install_helpers.get_venv_path")
    @patch("tools.repo_lint.install.install_helpers.subprocess.run")
    @patch("sys.platform", "win32")
    def test_install_python_tools_windows_paths(self, mock_run, mock_get_venv_path, mock_create_venv):
        """Test install_python_tools uses Windows-specific paths.

        :Purpose:
            Verify correct pip path on Windows
        :param mock_run: Mocked dependency for testing
        :param mock_get_venv_path: Mocked dependency for testing
        :param mock_create_venv: Mocked dependency for testing
        """
        mock_create_venv.return_value = (True, None)
        mock_get_venv_path.return_value = Path("C:/fake/repo/.venv-lint")
        mock_run.return_value = MagicMock(returncode=0)

        success, errors = install_python_tools(verbose=False)

        self.assertTrue(success)

        # Verify Windows pip path used (Scripts/pip.exe)
        first_call = mock_run.call_args_list[0][0][0]
        pip_path = str(first_call[0])
        self.assertIn("Scripts", pip_path)
        self.assertIn("pip.exe", pip_path)

    @patch("tools.repo_lint.install.install_helpers.create_venv")
    def test_install_python_tools_venv_creation_fails(self, mock_create_venv):
        """Test install_python_tools handles venv creation failure.

        :Purpose:
            Verify error handling when venv creation fails

        :param mock_create_venv: Mocked dependency for testing
        """
        mock_create_venv.return_value = (False, "Venv creation failed")

        success, errors = install_python_tools(verbose=False)

        self.assertFalse(success)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0], "Venv creation failed")

    @patch("tools.repo_lint.install.install_helpers.create_venv")
    @patch("tools.repo_lint.install.install_helpers.get_venv_path")
    @patch("tools.repo_lint.install.install_helpers.subprocess.run")
    @patch("sys.platform", "linux")
    def test_install_python_tools_partial_failure(self, mock_run, mock_get_venv_path, mock_create_venv):
        """Test install_python_tools handles partial installation failures.

        :Purpose:
            Verify error collection when some tools fail to install
        :param mock_run: Mocked dependency for testing
        :param mock_get_venv_path: Mocked dependency for testing
        :param mock_create_venv: Mocked dependency for testing
        """
        mock_create_venv.return_value = (True, None)
        mock_get_venv_path.return_value = Path("/fake/repo/.venv-lint")

        # Make second tool installation fail
        def side_effect(*args, **kwargs):
            """Mock side effect that fails on second call.

            :param args: Subprocess args
            :param kwargs: Subprocess kwargs
            :returns: Mock return value or raises exception
            """
            call_count = mock_run.call_count
            if call_count == 2:
                from subprocess import CalledProcessError

                raise CalledProcessError(1, args[0])
            return MagicMock(returncode=0)

        mock_run.side_effect = side_effect

        success, errors = install_python_tools(verbose=False)

        self.assertFalse(success)
        self.assertGreater(len(errors), 0)


class TestCleanupRepoLocal(unittest.TestCase):
    """Test cleanup of repo-local installations.

    :Purpose:
        Validates cleanup_repo_local removes only repo-local directories.
    """

    @patch("tools.repo_lint.install.install_helpers.get_repo_root")
    @patch("tools.repo_lint.install.install_helpers.shutil.rmtree")
    def test_cleanup_repo_local_success(self, mock_rmtree, mock_get_repo_root):
        """Test cleanup_repo_local removes expected directories.

        :Purpose:
            Verify cleanup removes .venv-lint, .tools, .psmodules, .cpan-local
        :param mock_rmtree: Mocked dependency for testing
        :param mock_get_repo_root: Mocked dependency for testing
        """
        mock_get_repo_root.return_value = Path("/fake/repo")

        # Mock directory existence
        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = True

            success, messages = cleanup_repo_local(verbose=False)

            self.assertTrue(success)
            self.assertEqual(mock_rmtree.call_count, 4)

            # Verify each directory was removed
            removed_dirs = [str(call[0][0]) for call in mock_rmtree.call_args_list]
            self.assertIn("/fake/repo/.venv-lint", removed_dirs)
            self.assertIn("/fake/repo/.tools", removed_dirs)
            self.assertIn("/fake/repo/.psmodules", removed_dirs)
            self.assertIn("/fake/repo/.cpan-local", removed_dirs)

    @patch("tools.repo_lint.install.install_helpers.get_repo_root")
    @patch("tools.repo_lint.install.install_helpers.shutil.rmtree")
    def test_cleanup_repo_local_no_dirs_exist(self, mock_rmtree, mock_get_repo_root):
        """Test cleanup_repo_local handles missing directories.

        :Purpose:
            Verify cleanup handles case when no directories exist
        :param mock_rmtree: Mocked dependency for testing
        :param mock_get_repo_root: Mocked dependency for testing
        """
        mock_get_repo_root.return_value = Path("/fake/repo")

        # Mock directory doesn't exist
        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = False

            success, messages = cleanup_repo_local(verbose=False)

            self.assertTrue(success)
            self.assertEqual(mock_rmtree.call_count, 0)
            self.assertIn("No repo-local installations found", messages[0])

    @patch("tools.repo_lint.install.install_helpers.get_repo_root")
    @patch("tools.repo_lint.install.install_helpers.shutil.rmtree")
    def test_cleanup_repo_local_partial_failure(self, mock_rmtree, mock_get_repo_root):
        """Test cleanup_repo_local handles removal failures.

        :Purpose:
            Verify error handling when directory removal fails
        :param mock_rmtree: Mocked dependency for testing
        :param mock_get_repo_root: Mocked dependency for testing
        """
        mock_get_repo_root.return_value = Path("/fake/repo")

        # Mock one directory removal fails
        def side_effect(path, **kwargs):
            """Mock side effect that fails for .venv-lint.

            :param path: Path to remove
            :param kwargs: Additional arguments
            :raises OSError: For .venv-lint path
            """
            if ".venv-lint" in str(path):
                raise OSError("Permission denied")

        mock_rmtree.side_effect = side_effect

        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = True

            success, messages = cleanup_repo_local(verbose=False)

            self.assertFalse(success)
            # Should have one error message about .venv-lint
            error_messages = [msg for msg in messages if "✗" in msg]
            self.assertGreater(len(error_messages), 0)


if __name__ == "__main__":
    unittest.main()
