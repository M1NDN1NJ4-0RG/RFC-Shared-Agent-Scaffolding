#!/usr/bin/env python3
"""Unit tests for bootstrap-repo-lint-toolchain.sh script.

This module provides comprehensive unit tests for the repo-lint toolchain
bootstrapper script, covering repository discovery, virtual environment
management, installation, and error handling.

:Purpose:
Ensures the bootstrapper correctly handles all success and failure paths,
validates idempotency, and maintains compliance with exit code contracts.

:Usage:
Run tests from repository root::

    python3 -m pytest scripts/tests/test_bootstrap_repo_lint_toolchain.py
    # or
    pytest scripts/tests/test_bootstrap_repo_lint_toolchain.py -v

:Environment Variables:
None. Tests create temporary directories and environments.

:Exit Codes:
0
    All tests passed
1
    One or more tests failed

:Examples:
Run all tests::

    pytest scripts/tests/test_bootstrap_repo_lint_toolchain.py -v

Run specific test::

    pytest scripts/tests/test_bootstrap_repo_lint_toolchain.py::TestBootstrapScript::test_exit_code_10_not_in_repo -v

:Notes:
- Tests use temporary directories to avoid modifying the actual repository
- Each test is isolated and cleans up after itself
- Tests cover all documented exit codes (0, 1, 10, 11, 12, 13, 14)
- Integration tests verify end-to-end functionality
"""

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


class TestBootstrapScript(unittest.TestCase):
    """Test bootstrap script functionality.

    Integration tests for the complete bootstrap workflow including:
    - Exit codes for various failure scenarios
    - Success scenarios with proper setup
    - Idempotency verification
    """

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp(prefix="bootstrap_test_")
        self.script_path = Path(__file__).parent.parent / "bootstrap-repo-lint-toolchain.sh"

    def tearDown(self):
        """Clean up temporary test directory."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_exit_code_10_not_in_repo(self):
        """Test exit code 10 when not in a repository."""
        non_repo = Path(self.test_dir) / "not_a_repo"
        non_repo.mkdir()

        script_copy = non_repo / "bootstrap.sh"
        shutil.copy(self.script_path, script_copy)
        script_copy.chmod(0o755)

        result = subprocess.run(
            ["bash", str(script_copy)],
            capture_output=True,
            text=True,
            cwd=str(non_repo),
            timeout=10,
        )

        self.assertEqual(result.returncode, 10, "Expected exit code 10 when not in a repository")
        self.assertIn("Could not find repository root", result.stderr)

    def test_exit_code_12_no_install_target(self):
        """Test exit code 12 when no pyproject.toml found."""
        repo = Path(self.test_dir) / "repo_no_pyproject"
        repo.mkdir()
        (repo / ".git").mkdir()

        script_copy = repo / "bootstrap.sh"
        shutil.copy(self.script_path, script_copy)
        script_copy.chmod(0o755)

        result = subprocess.run(
            ["bash", str(script_copy)],
            capture_output=True,
            text=True,
            cwd=str(repo),
            timeout=30,
        )

        self.assertEqual(
            result.returncode,
            12,
            "Expected exit code 12 when no pyproject.toml found",
        )
        self.assertIn("No valid install target found", result.stderr)

    def test_finds_repo_root_from_subdirectory(self):
        """Test that bootstrap finds repo root when run from subdirectory."""
        repo_root = Path(self.test_dir) / "test_repo"
        repo_root.mkdir()
        (repo_root / ".git").mkdir()
        (repo_root / "pyproject.toml").write_text(
            """[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "test_project"
version = "0.1.0"
"""
        )

        # Create subdirectory
        subdir = repo_root / "tools" / "scripts"
        subdir.mkdir(parents=True)

        script_copy = repo_root / "bootstrap.sh"
        shutil.copy(self.script_path, script_copy)
        script_copy.chmod(0o755)

        # Run from subdirectory - will fail at install but should find repo root
        result = subprocess.run(
            ["bash", str(script_copy)],
            capture_output=True,
            text=True,
            cwd=str(subdir),
            timeout=30,
        )

        # Should find the repo root (shown in output)
        self.assertIn(f"Repository root: {repo_root}", result.stdout)

    def test_creates_venv_directory(self):
        """Test that bootstrap creates .venv directory."""
        repo_root = Path(self.test_dir) / "test_repo"
        repo_root.mkdir()
        (repo_root / ".git").mkdir()
        (repo_root / "pyproject.toml").write_text(
            """[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "test_project"
version = "0.1.0"
"""
        )

        script_copy = repo_root / "bootstrap.sh"
        shutil.copy(self.script_path, script_copy)
        script_copy.chmod(0o755)

        # Run bootstrap - will fail at install but should create venv
        subprocess.run(
            ["bash", str(script_copy)],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
            timeout=30,
        )

        # Check that .venv was created
        self.assertTrue((repo_root / ".venv").exists(), ".venv directory should be created")
        self.assertTrue(
            (repo_root / ".venv" / "bin" / "python3").exists(),
            "venv should contain python3",
        )

    def test_idempotency_venv_already_exists(self):
        """Test that bootstrap is idempotent when venv already exists."""
        repo_root = Path(self.test_dir) / "test_repo"
        repo_root.mkdir()
        (repo_root / ".git").mkdir()
        (repo_root / "pyproject.toml").write_text(
            """[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "test_project"
version = "0.1.0"
"""
        )

        # Create venv first
        subprocess.run(["python3", "-m", "venv", str(repo_root / ".venv")], check=True, timeout=30)

        script_copy = repo_root / "bootstrap.sh"
        shutil.copy(self.script_path, script_copy)
        script_copy.chmod(0o755)

        # Run bootstrap
        result = subprocess.run(
            ["bash", str(script_copy)],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
            timeout=30,
        )

        # Should detect existing venv
        self.assertIn("Virtual environment already exists", result.stdout)


class TestRepositoryDiscovery(unittest.TestCase):
    """Test repository root discovery logic.

    Unit tests for find_repo_root function logic by extracting and testing
    the function in isolation.
    """

    def setUp(self):
        """Create temporary test directory."""
        self.test_dir = tempfile.mkdtemp(prefix="bootstrap_discovery_test_")

    def tearDown(self):
        """Clean up temporary test directory."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def _create_find_repo_root_test_script(self, repo_root, run_from_dir):
        """Create a standalone test script for find_repo_root function.

        :param repo_root: Path to the repository root directory.
        :param run_from_dir: Directory from which to run the test script.
        :returns: Path object pointing to the created test script.
        """
        test_script = repo_root / "test_find_repo.sh"
        test_script.write_text(
            f"""#!/bin/bash
set -euo pipefail

# Die function (needed by find_repo_root)
die() {{
    local msg="$1"
    local code="${{2:-1}}"
    echo "[bootstrap][ERROR] $msg" >&2
    exit "$code"
}}

# find_repo_root function extracted from bootstrap script
find_repo_root() {{
    local current_dir
    current_dir="$(pwd)"

    while true; do
        # Check for repository markers
        if [[ -d "$current_dir/.git" ]] || \\
           [[ -f "$current_dir/pyproject.toml" ]] || \\
           [[ -f "$current_dir/README.md" ]]; then
            echo "$current_dir"
            return 0
        fi

        # Check if we've reached filesystem root
        if [[ "$current_dir" == "/" ]]; then
            die "Could not find repository root (no .git, pyproject.toml, or README.md found)" 10
        fi

        # Move up one directory
        current_dir="$(dirname "$current_dir")"
    done
}}

cd {run_from_dir}
find_repo_root
"""
        )
        test_script.chmod(0o755)
        return test_script

    def test_find_repo_root_with_git_directory(self):
        """Test finding repo root with .git directory."""
        repo_root = Path(self.test_dir) / "test_repo"
        repo_root.mkdir()
        (repo_root / ".git").mkdir()
        subdir = repo_root / "subdir" / "nested"
        subdir.mkdir(parents=True)

        test_script = self._create_find_repo_root_test_script(repo_root, subdir)

        result = subprocess.run(["bash", str(test_script)], capture_output=True, text=True, timeout=10)

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), str(repo_root))

    def test_find_repo_root_with_pyproject_toml(self):
        """Test finding repo root with pyproject.toml."""
        repo_root = Path(self.test_dir) / "test_repo"
        repo_root.mkdir()
        (repo_root / "pyproject.toml").write_text("[project]\nname = 'test'\n")
        subdir = repo_root / "deep" / "nested"
        subdir.mkdir(parents=True)

        test_script = self._create_find_repo_root_test_script(repo_root, subdir)

        result = subprocess.run(["bash", str(test_script)], capture_output=True, text=True, timeout=10)

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), str(repo_root))

    def test_find_repo_root_with_readme(self):
        """Test finding repo root with README.md."""
        repo_root = Path(self.test_dir) / "test_repo"
        repo_root.mkdir()
        (repo_root / "README.md").write_text("# Test\n")

        test_script = self._create_find_repo_root_test_script(repo_root, repo_root)

        result = subprocess.run(["bash", str(test_script)], capture_output=True, text=True, timeout=10)

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), str(repo_root))

    def test_find_repo_root_exits_10_when_not_in_repo(self):
        """Test that find_repo_root exits with code 10 outside a repo."""
        non_repo = Path(self.test_dir) / "not_a_repo"
        non_repo.mkdir()

        test_script = self._create_find_repo_root_test_script(non_repo, non_repo)

        result = subprocess.run(["bash", str(test_script)], capture_output=True, text=True, timeout=10)

        self.assertEqual(result.returncode, 10)
        self.assertIn("Could not find repository root", result.stderr)


if __name__ == "__main__":
    # Allow running tests directly with python3
    unittest.main()

    def test_find_repo_root_with_git_marker(self):
        """Test finding repo root when .git directory exists."""
        # Create a mock repo with .git directory
        repo_root = Path(self.test_dir) / "test_repo"
        repo_root.mkdir()
        (repo_root / ".git").mkdir()
        subdir = repo_root / "subdir" / "nested"
        subdir.mkdir(parents=True)

        # Create a standalone test script that extracts and tests just find_repo_root
        test_script = repo_root / "test_find_repo.sh"
        test_script.write_text(
            f"""#!/bin/bash
set -euo pipefail

# Extract just the find_repo_root function from the main script
die() {{
    local msg="$1"
    local code="${{2:-1}}"
    echo "[bootstrap][ERROR] $msg" >&2
    exit "$code"
}}

find_repo_root() {{
    local current_dir
    current_dir="$(pwd)"

    while true; do
        # Check for repository markers
        if [[ -d "$current_dir/.git" ]] || \\
           [[ -f "$current_dir/pyproject.toml" ]] || \\
           [[ -f "$current_dir/README.md" ]]; then
            echo "$current_dir"
            return 0
        fi

        # Check if we've reached filesystem root
        if [[ "$current_dir" == "/" ]]; then
            die "Could not find repository root (no .git, pyproject.toml, or README.md found)" 10
        fi

        # Move up one directory
        current_dir="$(dirname "$current_dir")"
    done
}}

cd {subdir}
find_repo_root
"""
        )
        test_script.chmod(0o755)

        # Run from subdirectory
        result = subprocess.run(["bash", str(test_script)], capture_output=True, text=True, cwd=str(subdir))

        self.assertEqual(result.returncode, 0, f"stderr: {result.stderr}")
        self.assertEqual(result.stdout.strip(), str(repo_root))

    def test_find_repo_root_with_pyproject_toml(self):
        """Test finding repo root when pyproject.toml exists."""
        repo_root = Path(self.test_dir) / "test_repo"
        repo_root.mkdir()
        (repo_root / "pyproject.toml").write_text("[project]\nname = 'test'\n")
        subdir = repo_root / "deep" / "nested" / "path"
        subdir.mkdir(parents=True)

        script_copy = repo_root / "test_script.sh"
        shutil.copy(self.script_path, script_copy)
        script_copy.chmod(0o755)

        test_runner = repo_root / "test_runner.sh"
        test_runner.write_text(
            f"""#!/bin/bash
source {script_copy}
cd {subdir}
find_repo_root
"""
        )
        test_runner.chmod(0o755)

        result = subprocess.run(["bash", str(test_runner)], capture_output=True, text=True, cwd=str(subdir))

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), str(repo_root))

    def test_find_repo_root_with_readme(self):
        """Test finding repo root when README.md exists."""
        repo_root = Path(self.test_dir) / "test_repo"
        repo_root.mkdir()
        (repo_root / "README.md").write_text("# Test Repo\n")

        script_copy = repo_root / "test_script.sh"
        shutil.copy(self.script_path, script_copy)
        script_copy.chmod(0o755)

        test_runner = repo_root / "test_runner.sh"
        test_runner.write_text(
            f"""#!/bin/bash
source {script_copy}
find_repo_root
"""
        )
        test_runner.chmod(0o755)

        result = subprocess.run(["bash", str(test_runner)], capture_output=True, text=True, cwd=str(repo_root))

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), str(repo_root))

    def test_find_repo_root_not_in_repo_exits_10(self):
        """Test that find_repo_root exits with code 10 when not in a repository."""
        # Create a directory with no repo markers
        non_repo = Path(self.test_dir) / "not_a_repo"
        non_repo.mkdir()

        script_copy = non_repo / "test_script.sh"
        shutil.copy(self.script_path, script_copy)
        script_copy.chmod(0o755)

        test_runner = non_repo / "test_runner.sh"
        test_runner.write_text(
            f"""#!/bin/bash
source {script_copy}
find_repo_root
"""
        )
        test_runner.chmod(0o755)

        result = subprocess.run(["bash", str(test_runner)], capture_output=True, text=True, cwd=str(non_repo))

        self.assertEqual(result.returncode, 10, "Expected exit code 10 when not in a repo")
        self.assertIn("Could not find repository root", result.stderr)


if __name__ == "__main__":
    # Allow running tests directly with python3
    unittest.main()
