#!/usr/bin/env python3
# pylint: disable=wrong-import-position,protected-access  # Test file needs special setup
"""Unit tests for base runner functions.

:Purpose:
    Validates base.py functionality including:
    - Repository root detection with and without .git
    - Fallback behavior for non-Git directories

:Test Coverage:
    - find_repo_root() finds .git when present
    - find_repo_root() falls back to cwd when .git not found
    - find_repo_root() walks up directory tree correctly

:Usage:
    Run tests from repository root::

        python3 -m pytest tools/repo_lint/tests/test_base_runner.py
        # or
        python3 tools/repo_lint/tests/test_base_runner.py

:Environment Variables:
    None. Tests are self-contained with mocked Path operations.

:Exit Codes:
    0
        All tests passed
    1
        One or more tests failed

:Examples:
    Run all tests::

        python3 -m pytest tools/repo_lint/tests/test_base_runner.py -v

    Run specific test::

        python3 -m pytest tools/repo_lint/tests/test_base_runner.py::TestFindRepoRoot::test_finds_git_directory -v

:Notes:
    - Tests use unittest.mock to avoid filesystem operations
    - Tests verify fallback behavior for non-Git directories
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

# Add repo_lint parent directory to path for imports
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))

from tools.repo_lint.runners.base import find_repo_root  # noqa: E402


class TestFindRepoRoot(unittest.TestCase):
    """Test find_repo_root() function.

    :Purpose:
        Validates repository root detection with and without .git directory.
    """

    @patch("pathlib.Path.cwd")
    def test_finds_git_directory(self, mock_cwd):
        """Test find_repo_root returns repo root when .git exists.

        :Purpose:
            Verify normal operation when .git directory is found

        :param mock_cwd: Mocked Path.cwd
        """
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a fake .git directory
            git_dir = Path(tmpdir) / ".git"
            git_dir.mkdir()

            # Mock cwd to return tmpdir
            mock_cwd.return_value = Path(tmpdir)

            root = find_repo_root()
            self.assertEqual(root, Path(tmpdir))

    @patch("pathlib.Path.cwd")
    def test_fallback_when_no_git(self, mock_cwd):
        """Test find_repo_root returns cwd when .git not found.

        :Purpose:
            Verify fallback behavior for non-Git directories

        :param mock_cwd: Mocked Path.cwd
        """
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            # Don't create .git directory
            mock_cwd.return_value = Path(tmpdir)

            root = find_repo_root()
            # Should fall back to cwd when .git not found
            self.assertEqual(root, Path(tmpdir))

    @patch("pathlib.Path.cwd")
    def test_walks_up_directory_tree(self, mock_cwd):
        """Test find_repo_root walks up directory tree correctly.

        :Purpose:
            Verify search traverses parent directories

        :param mock_cwd: Mocked Path.cwd
        """
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create nested directories a/b/c
            nested_dir = Path(tmpdir) / "a" / "b" / "c"
            nested_dir.mkdir(parents=True)

            # Create .git at the root
            git_dir = Path(tmpdir) / ".git"
            git_dir.mkdir()

            # Mock cwd to return nested directory
            mock_cwd.return_value = nested_dir

            root = find_repo_root()
            # Should find .git at tmpdir, not at nested_dir
            self.assertEqual(root, Path(tmpdir))

    @patch("pathlib.Path.cwd")
    def test_consistency_with_get_repo_root(self, mock_cwd):
        """Test find_repo_root has same behavior as get_repo_root.

        :Purpose:
            Verify both functions use consistent fallback logic

        :param mock_cwd: Mocked Path.cwd
        """
        import tempfile

        from tools.repo_lint.install.install_helpers import get_repo_root

        with tempfile.TemporaryDirectory() as tmpdir:
            # Don't create .git directory
            mock_cwd.return_value = Path(tmpdir)

            root1 = find_repo_root()
            root2 = get_repo_root()

            # Both should return the same fallback (cwd)
            self.assertEqual(root1, root2)
            self.assertEqual(root1, Path(tmpdir))


if __name__ == "__main__":
    unittest.main()
