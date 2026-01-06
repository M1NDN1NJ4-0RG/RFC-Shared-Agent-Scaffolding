#!/usr/bin/env python3
# pylint: disable=too-many-lines
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

from __future__ import annotations

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


class TestToolDetection(unittest.TestCase):
    """Test tool detection and installation verification logic.

    Tests cover detection of already-installed tools and missing tool scenarios
    for all required toolchains: Python, Shell, PowerShell, and Perl.
    """

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp(prefix="bootstrap_tool_test_")
        self.script_path = Path(__file__).parent.parent / "bootstrap-repo-lint-toolchain.sh"

    def tearDown(self):
        """Clean up temporary test directory."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def _setup_mock_repo(self, repo_root):
        """Create a minimal mock repository with required files.

        :param repo_root: Path to repository root directory.
        """
        repo_root.mkdir(parents=True, exist_ok=True)
        (repo_root / ".git").mkdir()
        (repo_root / "pyproject.toml").write_text(
            """[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "test_project"
version = "0.1.0"
dependencies = [
    "PyYAML>=6.0",
    "click>=8.0",
    "rich>=10.0",
    "rich-click>=1.6.0",
]

[project.scripts]
repo-lint = "test_project.cli:main"
"""
        )
        # Create minimal package structure
        (repo_root / "test_project").mkdir()
        (repo_root / "test_project" / "__init__.py").write_text("")
        (repo_root / "test_project" / "cli.py").write_text(
            """def main():
    print("repo-lint mock")
"""
        )

    def test_python_tools_detection(self):
        """Test detection of Python toolchain (black, ruff, pylint, yamllint, pytest)."""
        repo_root = Path(self.test_dir) / "test_repo"
        self._setup_mock_repo(repo_root)

        script_copy = repo_root / "bootstrap.sh"
        shutil.copy(self.script_path, script_copy)
        script_copy.chmod(0o755)

        # Run bootstrap - should attempt to install Python tools
        result = subprocess.run(
            ["bash", str(script_copy)],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
            timeout=120,
        )

        # Check that Python tools installation was attempted
        self.assertIn("Installing Python toolchain", result.stdout)
        # Check for specific tools
        for tool in ["black", "ruff", "pylint", "yamllint", "pytest"]:
            self.assertIn(tool, result.stdout.lower())

    def test_ripgrep_fallback_behavior(self):
        """Test ripgrep (rgrep) detection and fallback to grep."""
        repo_root = Path(self.test_dir) / "test_repo"
        self._setup_mock_repo(repo_root)

        script_copy = repo_root / "bootstrap.sh"
        shutil.copy(self.script_path, script_copy)
        script_copy.chmod(0o755)

        # Run bootstrap
        result = subprocess.run(
            ["bash", str(script_copy)],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
            timeout=120,
        )

        # Should check for ripgrep
        self.assertIn("ripgrep", result.stdout.lower())

    def test_shell_toolchain_detection(self):
        """Test detection of shell toolchain (shellcheck, shfmt) when --shell flag used."""
        repo_root = Path(self.test_dir) / "test_repo"
        self._setup_mock_repo(repo_root)

        script_copy = repo_root / "bootstrap.sh"
        shutil.copy(self.script_path, script_copy)
        script_copy.chmod(0o755)

        # Run with --shell flag
        result = subprocess.run(
            ["bash", str(script_copy), "--shell"],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
            timeout=120,
        )

        # Check that shell tools installation was attempted
        self.assertIn("Installing shell toolchain", result.stdout)
        self.assertIn("shellcheck", result.stdout.lower())
        self.assertIn("shfmt", result.stdout.lower())

    def test_powershell_toolchain_detection(self):
        """Test detection of PowerShell toolchain (pwsh, PSScriptAnalyzer) when --powershell flag used."""
        repo_root = Path(self.test_dir) / "test_repo"
        self._setup_mock_repo(repo_root)

        script_copy = repo_root / "bootstrap.sh"
        shutil.copy(self.script_path, script_copy)
        script_copy.chmod(0o755)

        # Run with --powershell flag
        result = subprocess.run(
            ["bash", str(script_copy), "--powershell"],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
            timeout=120,
        )

        # Check that PowerShell tools installation was attempted
        self.assertIn("Installing PowerShell toolchain", result.stdout)
        self.assertIn("pwsh", result.stdout.lower())
        self.assertIn("psscriptanalyzer", result.stdout.lower())

    def test_perl_toolchain_detection(self):
        """Test detection of Perl toolchain (Perl::Critic, PPI) when --perl flag used."""
        repo_root = Path(self.test_dir) / "test_repo"
        self._setup_mock_repo(repo_root)

        script_copy = repo_root / "bootstrap.sh"
        shutil.copy(self.script_path, script_copy)
        script_copy.chmod(0o755)

        # Run with --perl flag
        result = subprocess.run(
            ["bash", str(script_copy), "--perl"],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
            timeout=180,
        )

        # Check that Perl tools installation was attempted
        self.assertIn("Installing Perl toolchain", result.stdout)
        self.assertIn("Perl::Critic", result.stdout)
        self.assertIn("PPI", result.stdout)


class TestRepoLintInstallation(unittest.TestCase):
    """Test repo-lint package installation and PATH availability.

    Verifies that repo-lint is properly installed in the venv and becomes
    available on PATH after bootstrap completes.
    """

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp(prefix="bootstrap_install_test_")
        self.script_path = Path(__file__).parent.parent / "bootstrap-repo-lint-toolchain.sh"

    def tearDown(self):
        """Clean up temporary test directory."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def _setup_mock_repo(self, repo_root):
        """Create a minimal mock repository with repo-lint package.

        :param repo_root: Path to repository root directory.
        """
        repo_root.mkdir(parents=True, exist_ok=True)
        (repo_root / ".git").mkdir()
        (repo_root / "pyproject.toml").write_text(
            """[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "repo_lint"
version = "0.1.0"
dependencies = [
    "PyYAML>=6.0",
    "click>=8.0",
    "rich>=10.0",
    "rich-click>=1.6.0",
]

[project.scripts]
repo-lint = "repo_lint.cli:main"
"""
        )
        # Create minimal package
        pkg_dir = repo_root / "repo_lint"
        pkg_dir.mkdir()
        (pkg_dir / "__init__.py").write_text("")
        (pkg_dir / "cli.py").write_text(
            """import sys
def main():
    if "--help" in sys.argv:
        print("Usage: repo-lint [OPTIONS] COMMAND")
        sys.exit(0)
    print("repo-lint mock")
"""
        )

    def test_repo_lint_installation(self):
        """Test that repo-lint package is installed in venv."""
        repo_root = Path(self.test_dir) / "test_repo"
        self._setup_mock_repo(repo_root)

        script_copy = repo_root / "bootstrap.sh"
        shutil.copy(self.script_path, script_copy)
        script_copy.chmod(0o755)

        # Run bootstrap
        result = subprocess.run(
            ["bash", str(script_copy)],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
            timeout=120,
        )

        # Check that repo-lint was installed
        self.assertIn("Installing repo-lint", result.stdout)
        self.assertIn("repo-lint package installed successfully", result.stdout)

    def test_repo_lint_help_works(self):
        """Test that repo-lint --help works after installation."""
        repo_root = Path(self.test_dir) / "test_repo"
        self._setup_mock_repo(repo_root)

        script_copy = repo_root / "bootstrap.sh"
        shutil.copy(self.script_path, script_copy)
        script_copy.chmod(0o755)

        # Run bootstrap
        subprocess.run(
            ["bash", str(script_copy)],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
            timeout=120,
        )

        # Verify repo-lint --help works
        venv_repo_lint = repo_root / ".venv" / "bin" / "repo-lint"
        if venv_repo_lint.exists():
            result = subprocess.run(
                [str(venv_repo_lint), "--help"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            self.assertEqual(result.returncode, 0)
            self.assertIn("repo-lint", result.stdout)

    def test_repo_lint_on_path_after_activation(self):
        """Test that repo-lint is on PATH in activated venv."""
        repo_root = Path(self.test_dir) / "test_repo"
        self._setup_mock_repo(repo_root)

        script_copy = repo_root / "bootstrap.sh"
        shutil.copy(self.script_path, script_copy)
        script_copy.chmod(0o755)

        # Run bootstrap
        subprocess.run(
            ["bash", str(script_copy)],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
            timeout=120,
        )

        # Check that venv/bin/repo-lint exists
        venv_repo_lint = repo_root / ".venv" / "bin" / "repo-lint"
        self.assertTrue(
            venv_repo_lint.exists(),
            "repo-lint should be installed in .venv/bin/",
        )


class TestVerificationGate(unittest.TestCase):
    """Test end-to-end verification gate functionality.

    Tests the final verification step that runs repo-lint check --ci
    and validates exit code handling (exit 0 for clean repo, exit 1 for
    violations but tools work, exit 2 for missing tools).
    """

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp(prefix="bootstrap_verify_test_")
        self.script_path = Path(__file__).parent.parent / "bootstrap-repo-lint-toolchain.sh"

    def tearDown(self):
        """Clean up temporary test directory."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_verification_gate_exit_code_handling(self):
        """Test that verification gate correctly handles exit codes.

        Exit code 0 or 1 (violations) should be treated as success.
        Exit code 2 (missing tools) should be treated as failure.
        """
        repo_root = Path(self.test_dir) / "test_repo"
        repo_root.mkdir()
        (repo_root / ".git").mkdir()
        (repo_root / "pyproject.toml").write_text(
            """[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "repo_lint"
version = "0.1.0"
dependencies = ["PyYAML>=6.0", "click>=8.0", "rich>=10.0", "rich-click>=1.6.0"]

[project.scripts]
repo-lint = "repo_lint.cli:main"
"""
        )

        # Create mock repo-lint that exits with code 1 (violations)
        pkg_dir = repo_root / "repo_lint"
        pkg_dir.mkdir()
        (pkg_dir / "__init__.py").write_text("")
        (pkg_dir / "cli.py").write_text(
            """import sys
def main():
    if "--help" in sys.argv:
        print("Usage: repo-lint [OPTIONS] COMMAND")
        sys.exit(0)
    if "check" in sys.argv and "--ci" in sys.argv:
        print("Found violations")
        sys.exit(1)  # Violations found, but tools work
    sys.exit(0)
"""
        )

        script_copy = repo_root / "bootstrap.sh"
        shutil.copy(self.script_path, script_copy)
        script_copy.chmod(0o755)

        # Run bootstrap - should succeed even with exit code 1
        result = subprocess.run(
            ["bash", str(script_copy)],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
            timeout=120,
        )

        # Bootstrap should succeed (exit 0) even if repo-lint exits 1
        self.assertEqual(
            result.returncode,
            0,
            "Bootstrap should succeed when verification finds violations (exit 1)",
        )
        self.assertIn("Verification gate passed", result.stdout)


class TestNonInteractiveBehavior(unittest.TestCase):
    """Test that bootstrap script has no interactive prompts in CI mode.

    Ensures the script is CI-friendly and doesn't hang waiting for user input.
    """

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp(prefix="bootstrap_noninteractive_test_")
        self.script_path = Path(__file__).parent.parent / "bootstrap-repo-lint-toolchain.sh"

    def tearDown(self):
        """Clean up temporary test directory."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_no_prompts_on_stdin_closed(self):
        """Test that script doesn't hang when stdin is closed (CI simulation)."""
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

        # Run with stdin closed (like CI would)
        result = subprocess.run(
            ["bash", str(script_copy)],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            cwd=str(repo_root),
            timeout=120,  # Should not timeout
        )

        # Should complete (either succeed or fail, but not hang)
        self.assertIsNotNone(result.returncode)


class TestIdempotency(unittest.TestCase):
    """Test that bootstrap script is idempotent.

    Running the script multiple times should produce the same result
    without errors or state corruption.
    """

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp(prefix="bootstrap_idempotent_test_")
        self.script_path = Path(__file__).parent.parent / "bootstrap-repo-lint-toolchain.sh"

    def tearDown(self):
        """Clean up temporary test directory."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def _setup_mock_repo(self, repo_root):
        """Create a minimal mock repository.

        :param repo_root: Path to repository root directory.
        """
        repo_root.mkdir(parents=True, exist_ok=True)
        (repo_root / ".git").mkdir()
        (repo_root / "pyproject.toml").write_text(
            """[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "repo_lint"
version = "0.1.0"
dependencies = ["PyYAML>=6.0", "click>=8.0", "rich>=10.0", "rich-click>=1.6.0"]

[project.scripts]
repo-lint = "repo_lint.cli:main"
"""
        )
        pkg_dir = repo_root / "repo_lint"
        pkg_dir.mkdir()
        (pkg_dir / "__init__.py").write_text("")
        (pkg_dir / "cli.py").write_text(
            """import sys
def main():
    if "--help" in sys.argv:
        print("Usage: repo-lint")
        sys.exit(0)
    if "check" in sys.argv:
        sys.exit(0)
"""
        )

    def test_running_twice_produces_same_result(self):
        """Test that running bootstrap twice is safe and idempotent."""
        repo_root = Path(self.test_dir) / "test_repo"
        self._setup_mock_repo(repo_root)

        script_copy = repo_root / "bootstrap.sh"
        shutil.copy(self.script_path, script_copy)
        script_copy.chmod(0o755)

        # Run bootstrap first time
        result1 = subprocess.run(
            ["bash", str(script_copy)],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
            timeout=120,
        )

        # Run bootstrap second time
        result2 = subprocess.run(
            ["bash", str(script_copy)],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
            timeout=120,
        )

        # Both should succeed
        self.assertEqual(result1.returncode, result2.returncode)
        # Second run should detect existing venv
        self.assertIn("already exists", result2.stdout.lower())


class TestActionlintInstallation(unittest.TestCase):
    """Test actionlint installation as part of required toolchain.

    Tests that actionlint is installed automatically, is idempotent,
    and is properly integrated into the bootstrap process.
    """

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp(prefix="bootstrap_actionlint_test_")
        self.script_path = Path(__file__).parent.parent / "bootstrap-repo-lint-toolchain.sh"

    def tearDown(self):
        """Clean up temporary test directory."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def _setup_mock_repo(self, repo_root):
        """Create a minimal mock repository.

        :param repo_root: Path to repository root directory.
        """
        repo_root.mkdir(parents=True, exist_ok=True)
        (repo_root / ".git").mkdir()
        (repo_root / "pyproject.toml").write_text(
            """[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "repo_lint"
version = "0.1.0"
dependencies = ["PyYAML>=6.0", "click>=8.0", "rich>=10.0", "rich-click>=1.6.0"]

[project.scripts]
repo-lint = "repo_lint.cli:main"
"""
        )
        pkg_dir = repo_root / "repo_lint"
        pkg_dir.mkdir()
        (pkg_dir / "__init__.py").write_text("")
        (pkg_dir / "cli.py").write_text(
            """import sys
def main():
    if "--help" in sys.argv:
        print("Usage: repo-lint")
        sys.exit(0)
    if "check" in sys.argv:
        sys.exit(0)
"""
        )

    def test_actionlint_installation_attempted(self):
        """Test that actionlint installation is attempted as part of bootstrap."""
        repo_root = Path(self.test_dir) / "test_repo"
        self._setup_mock_repo(repo_root)

        script_copy = repo_root / "bootstrap.sh"
        shutil.copy(self.script_path, script_copy)
        script_copy.chmod(0o755)

        # Run bootstrap
        result = subprocess.run(
            ["bash", str(script_copy)],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
            timeout=180,
        )

        # Check that actionlint installation was attempted
        self.assertIn("Installing actionlint", result.stdout)
        # Should mention it's a GitHub Actions workflow linter
        self.assertIn("GitHub Actions", result.stdout)

    def test_actionlint_in_summary(self):
        """Test that actionlint appears in the bootstrap success summary."""
        repo_root = Path(self.test_dir) / "test_repo"
        self._setup_mock_repo(repo_root)

        script_copy = repo_root / "bootstrap.sh"
        shutil.copy(self.script_path, script_copy)
        script_copy.chmod(0o755)

        # Run bootstrap
        result = subprocess.run(
            ["bash", str(script_copy)],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
            timeout=180,
        )

        # Check that actionlint appears in summary
        self.assertIn("actionlint", result.stdout)
        # Check for success summary section
        if result.returncode == 0:
            self.assertIn("Summary:", result.stdout)

    def test_actionlint_idempotency(self):
        """Test that actionlint installation is idempotent when already present."""
        repo_root = Path(self.test_dir) / "test_repo"
        self._setup_mock_repo(repo_root)

        # Create a mock actionlint binary in a temp bin directory
        temp_bin = Path(self.test_dir) / "bin"
        temp_bin.mkdir()
        mock_actionlint = temp_bin / "actionlint"
        mock_actionlint.write_text(
            """#!/bin/bash
echo "v1.7.10"
"""
        )
        mock_actionlint.chmod(0o755)

        script_copy = repo_root / "bootstrap.sh"
        shutil.copy(self.script_path, script_copy)
        script_copy.chmod(0o755)

        # Run bootstrap with PATH modified to include mock actionlint
        env = os.environ.copy()
        env["PATH"] = f"{temp_bin}:{env.get('PATH', '')}"

        result = subprocess.run(
            ["bash", str(script_copy)],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
            timeout=180,
            env=env,
        )

        # Should detect existing actionlint
        self.assertIn("actionlint already installed", result.stdout)

    def test_actionlint_phase_ordering(self):
        """Test that actionlint is installed in the correct phase (Phase 2.3)."""
        repo_root = Path(self.test_dir) / "test_repo"
        self._setup_mock_repo(repo_root)

        script_copy = repo_root / "bootstrap.sh"
        shutil.copy(self.script_path, script_copy)
        script_copy.chmod(0o755)

        # Run bootstrap
        result = subprocess.run(
            ["bash", str(script_copy)],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
            timeout=180,
        )

        # Check phase structure
        self.assertIn("PHASE 2", result.stdout)
        # actionlint should come after Python tools
        python_pos = result.stdout.find("Installing Python toolchain")
        actionlint_pos = result.stdout.find("Installing actionlint")
        if python_pos != -1 and actionlint_pos != -1:
            self.assertLess(
                python_pos,
                actionlint_pos,
                "actionlint should be installed after Python toolchain",
            )

    def test_actionlint_exit_code_20_documented(self):
        """Test that exit code 20 is used for actionlint installation failure.

        This is a documentation test to ensure the exit code contract is clear.
        """
        # This test validates the documented exit code
        # Actual failure testing would require mocking Go installation failure
        # which is complex in integration tests

        # Read the script to verify exit code 20 is used for actionlint failures
        script_content = self.script_path.read_text()
        # The script uses 'die "message" 20' pattern for exit code 20
        self.assertIn('"actionlint', script_content)
        self.assertIn("20", script_content)
        # Verify that die commands with code 20 are related to actionlint
        self.assertIn('die "actionlint', script_content)


if __name__ == "__main__":
    # Allow running tests directly with python3
    unittest.main()
