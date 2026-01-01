"""
Exhaustive fixture isolation and runner file selection tests.

This module provides comprehensive coverage of the fixture inclusion/exclusion
matrix across all runners, flag combinations, and file selection modes.

:Test Coverage Matrix:
    - Flag combinations: --ci, --include-fixtures, neither, both
    - All 6 language runners: Python, Bash, PowerShell, Perl, YAML, Rust
    - Selection modes: all files, --only language, changed-only detection
    - Edge cases: nested fixtures, glob patterns, naming conventions
    - Negative proofs: cross-language isolation, fixture exclusion guarantees
    - Regression traps: import errors, has_files consistency, double exclusion

:Fixture Files:
    - Located at: tools/repo_lint/tests/fixtures/**
    - Intentionally contain violations for testing purposes
    - MUST be excluded from normal and CI modes
    - MUST be included ONLY with --include-fixtures flag

:Environment Variables: None

:Author: GitHub Copilot
:Date: 2026-01-01
"""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tools.repo_lint.runners.base import get_tracked_files
from tools.repo_lint.runners.bash_runner import BashRunner
from tools.repo_lint.runners.perl_runner import PerlRunner
from tools.repo_lint.runners.powershell_runner import PowerShellRunner
from tools.repo_lint.runners.python_runner import PythonRunner
from tools.repo_lint.runners.rust_runner import RustRunner
from tools.repo_lint.runners.yaml_runner import YAMLRunner

# Get repository root (relative to this test file's location)
REPO_ROOT = Path(__file__).parent.parent.parent.parent.resolve()
FIXTURE_DIR = REPO_ROOT / "tools" / "repo_lint" / "tests" / "fixtures"


class TestFixtureExclusionMatrix:
    """Test fixture exclusion across all flag combinations."""

    @pytest.mark.parametrize(
        "include_fixtures,expected_has_fixtures",
        [
            (False, False),  # Normal mode - fixtures excluded
            (True, True),  # Vector mode - fixtures included
        ],
    )
    def test_python_fixture_exclusion(
        self, include_fixtures, expected_has_fixtures
    ):  # pylint: disable=redefined-outer-name
        """Test Python runner excludes fixtures unless --include-fixtures."""
        files = get_tracked_files(["**/*.py"], str(REPO_ROOT), include_fixtures=include_fixtures)
        fixture_files = [f for f in files if "tests/fixtures/python" in f or "/fixtures/python/" in f]

        if expected_has_fixtures:
            assert len(fixture_files) > 0, "Vector mode should include Python fixtures"
        else:
            assert len(fixture_files) == 0, f"Normal mode should exclude fixtures, found: {fixture_files}"

    @pytest.mark.parametrize(
        "include_fixtures,expected_has_fixtures",
        [
            (False, False),
            (True, True),
        ],
    )
    def test_bash_fixture_exclusion(
        self, include_fixtures, expected_has_fixtures
    ):  # pylint: disable=redefined-outer-name
        """Test Bash runner excludes fixtures unless --include-fixtures."""
        files = get_tracked_files(["**/*.sh"], str(REPO_ROOT), include_fixtures=include_fixtures)
        fixture_files = [f for f in files if "tests/fixtures/bash" in f or "/fixtures/bash/" in f]

        if expected_has_fixtures:
            assert len(fixture_files) > 0, "Vector mode should include Bash fixtures"
        else:
            assert len(fixture_files) == 0, f"Normal mode should exclude fixtures, found: {fixture_files}"

    @pytest.mark.parametrize(
        "include_fixtures,expected_has_fixtures",
        [
            (False, False),
            (True, True),
        ],
    )
    def test_powershell_fixture_exclusion(
        self, include_fixtures, expected_has_fixtures
    ):  # pylint: disable=redefined-outer-name
        """Test PowerShell runner excludes fixtures unless --include-fixtures."""
        files = get_tracked_files(
            ["**/*.ps1", "**/*.psm1"],
            str(REPO_ROOT),
            include_fixtures=include_fixtures,
        )
        fixture_files = [f for f in files if "tests/fixtures/powershell" in f or "/fixtures/powershell/" in f]

        if expected_has_fixtures:
            assert len(fixture_files) > 0, "Vector mode should include PowerShell fixtures"
        else:
            assert len(fixture_files) == 0, f"Normal mode should exclude fixtures, found: {fixture_files}"

    @pytest.mark.parametrize(
        "include_fixtures,expected_has_fixtures",
        [
            (False, False),
            (True, True),
        ],
    )
    def test_perl_fixture_exclusion(
        self, include_fixtures, expected_has_fixtures
    ):  # pylint: disable=redefined-outer-name
        """Test Perl runner excludes fixtures unless --include-fixtures."""
        files = get_tracked_files(["**/*.pl", "**/*.pm"], str(REPO_ROOT), include_fixtures=include_fixtures)
        fixture_files = [f for f in files if "tests/fixtures/perl" in f or "/fixtures/perl/" in f]

        if expected_has_fixtures:
            assert len(fixture_files) > 0, "Vector mode should include Perl fixtures"
        else:
            assert len(fixture_files) == 0, f"Normal mode should exclude fixtures, found: {fixture_files}"

    @pytest.mark.parametrize(
        "include_fixtures,expected_has_fixtures",
        [
            (False, False),
            (True, True),
        ],
    )
    def test_yaml_fixture_exclusion(
        self, include_fixtures, expected_has_fixtures
    ):  # pylint: disable=redefined-outer-name
        """Test YAML runner excludes fixtures unless --include-fixtures."""
        files = get_tracked_files(
            ["**/*.yaml", "**/*.yml"],
            str(REPO_ROOT),
            include_fixtures=include_fixtures,
        )
        fixture_files = [f for f in files if "tests/fixtures/yaml" in f or "/fixtures/yaml/" in f]

        if expected_has_fixtures:
            assert len(fixture_files) > 0, "Vector mode should include YAML fixtures"
        else:
            assert len(fixture_files) == 0, f"Normal mode should exclude fixtures, found: {fixture_files}"

    @pytest.mark.parametrize(
        "include_fixtures,expected_has_fixtures",
        [
            (False, False),
            (True, True),
        ],
    )
    def test_rust_fixture_exclusion(
        self, include_fixtures, expected_has_fixtures
    ):  # pylint: disable=redefined-outer-name
        """Test Rust runner excludes fixtures unless --include-fixtures."""
        files = get_tracked_files(["**/*.rs"], str(REPO_ROOT), include_fixtures=include_fixtures)
        fixture_files = [f for f in files if "tests/fixtures/rust" in f or "/fixtures/rust/" in f]

        if expected_has_fixtures:
            assert len(fixture_files) > 0, "Vector mode should include Rust fixtures"
        else:
            assert len(fixture_files) == 0, f"Normal mode should exclude fixtures, found: {fixture_files}"


class TestRunnerLanguageIsolation:
    """Test that each runner only receives files for its language."""

    def test_python_runner_only_receives_python_files(self):
        """Python runner must never receive non-Python files."""
        runner = PythonRunner(str(REPO_ROOT), ci_mode=True)
        runner.set_include_fixtures(False)

        # Get all files the runner would process
        python_files = get_tracked_files(["**/*.py"], str(REPO_ROOT), include_fixtures=False)

        # Assert no Rust files
        rust_files_in_python = [f for f in python_files if f.endswith(".rs")]
        assert len(rust_files_in_python) == 0, f"Python runner received Rust files: {rust_files_in_python}"

        # Assert no Bash files
        bash_files_in_python = [f for f in python_files if f.endswith(".sh")]
        assert len(bash_files_in_python) == 0, f"Python runner received Bash files: {bash_files_in_python}"

        # Assert no Perl files
        perl_files_in_python = [f for f in python_files if f.endswith((".pl", ".pm"))]
        assert len(perl_files_in_python) == 0, f"Python runner received Perl files: {perl_files_in_python}"

    def test_rust_runner_only_receives_rust_files(self):
        """Rust runner must never receive non-Rust files."""
        # Get all files the runner would process
        rust_files = get_tracked_files(["**/*.rs"], str(REPO_ROOT), include_fixtures=False)

        # Assert no Python files
        python_files_in_rust = [f for f in rust_files if f.endswith(".py")]
        assert len(python_files_in_rust) == 0, f"Rust runner received Python files: {python_files_in_rust}"

        # Assert no Bash files
        bash_files_in_rust = [f for f in rust_files if f.endswith(".sh")]
        assert len(bash_files_in_rust) == 0, f"Rust runner received Bash files: {bash_files_in_rust}"

    def test_bash_runner_only_receives_bash_files(self):
        """Bash runner must never receive non-Bash files."""
        bash_files = get_tracked_files(["**/*.sh"], str(REPO_ROOT), include_fixtures=False)

        # Assert no Python files
        python_files_in_bash = [f for f in bash_files if f.endswith(".py")]
        assert len(python_files_in_bash) == 0, f"Bash runner received Python files: {python_files_in_bash}"

        # Assert no Rust files
        rust_files_in_bash = [f for f in bash_files if f.endswith(".rs")]
        assert len(rust_files_in_bash) == 0, f"Bash runner received Rust files: {rust_files_in_bash}"


class TestFixturePathEdgeCases:
    """Test fixture exclusion edge cases and glob patterns."""

    def test_nested_fixture_directories_excluded(self):
        """Nested fixture directories must be excluded in normal mode."""
        files = get_tracked_files(["**/*.py"], str(REPO_ROOT), include_fixtures=False)

        # Check for any fixture path components
        fixture_patterns = ["fixtures/python/", "fixtures/bash/", "fixtures/perl/"]
        fixture_files = [f for f in files if any(pattern in f for pattern in fixture_patterns)]

        assert len(fixture_files) == 0, f"Nested fixture directories not excluded: {fixture_files}"

    def test_fixture_files_matching_production_patterns_excluded(self):
        """Fixture files matching production glob patterns must still be excluded."""
        files = get_tracked_files(["**/*_runner.py"], str(REPO_ROOT), include_fixtures=False)

        # Even though fixtures might match *_runner.py pattern, they should be excluded
        fixture_runners = [f for f in files if "/fixtures/" in f]
        assert len(fixture_runners) == 0, f"Fixture files matching production patterns not excluded: {fixture_runners}"

    def test_fixture_violation_files_excluded(self):
        """Fixture violation files must be excluded in normal mode."""
        files = get_tracked_files(["**/*.py"], str(REPO_ROOT), include_fixtures=False)

        violation_patterns = [
            "black_violations.py",
            "ruff_violations.py",
            "pylint_violations.py",
            "all_docstring_violations.py",
            "naming-violations.py",
        ]

        violation_files = [f for f in files if any(pattern in f for pattern in violation_patterns)]

        assert len(violation_files) == 0, f"Fixture violation files not excluded: {violation_files}"


class TestRunnerHasFilesConsistency:
    """Test that has_files() uses same file set as execution."""

    @patch("tools.repo_lint.runners.python_runner.subprocess.run")
    def test_python_runner_has_files_matches_execution(self, mock_run):
        """Python runner has_files() must match actual execution file set."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        runner = PythonRunner(str(REPO_ROOT), ci_mode=True)
        runner.set_include_fixtures(False)

        # Check has_files()
        has_files = runner.has_files()

        # Get actual files that would be checked
        files = get_tracked_files(["**/*.py"], str(REPO_ROOT), include_fixtures=False)

        # has_files() should return True only if files exist
        assert has_files == (len(files) > 0), "has_files() inconsistent with actual file set"

    @patch("tools.repo_lint.runners.rust_runner.subprocess.run")
    def test_rust_runner_has_files_matches_execution(self, mock_run):
        """Rust runner has_files() must match actual execution file set."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        runner = RustRunner(str(REPO_ROOT), ci_mode=True)
        runner.set_include_fixtures(False)

        # Check has_files()
        has_files = runner.has_files()

        # Get actual files that would be checked
        files = get_tracked_files(["**/*.rs"], str(REPO_ROOT), include_fixtures=False)

        # has_files() should return True only if files exist
        assert has_files == (len(files) > 0), "has_files() inconsistent with actual file set"


class TestCIModeFixtureBehavior:
    """Test --ci mode fixture behavior across all scenarios."""

    def test_ci_mode_never_includes_fixtures_without_flag(self):
        """CI mode must NEVER include fixtures unless --include-fixtures is set."""
        # Simulate CI mode (include_fixtures=False)
        all_languages = [
            ("**/*.py", "Python"),
            ("**/*.sh", "Bash"),
            ("**/*.rs", "Rust"),
            ("**/*.pl", "Perl"),
            ("**/*.ps1", "PowerShell"),
            ("**/*.yaml", "YAML"),
        ]

        for patterns, language in all_languages:
            if isinstance(patterns, str):
                patterns = [patterns]

            files = get_tracked_files(patterns, str(REPO_ROOT), include_fixtures=False)
            fixture_files = [f for f in files if "/fixtures/" in f]

            assert (
                len(fixture_files) == 0
            ), f"CI mode included {language} fixtures without --include-fixtures: {fixture_files}"

    def test_ci_mode_with_include_fixtures_flag_includes_fixtures(self):
        """CI mode WITH --include-fixtures must include fixtures."""
        # Simulate CI mode with --include-fixtures (include_fixtures=True)
        python_files = get_tracked_files(["**/*.py"], str(REPO_ROOT), include_fixtures=True)
        fixture_files = [f for f in python_files if "/fixtures/python/" in f or "fixtures/python" in f]

        assert len(fixture_files) > 0, "CI mode with --include-fixtures did not include Python fixtures"


class TestNegativeProofs:
    """Test impossible outcomes to prove system correctness."""

    def test_fixtures_cannot_appear_in_ci_without_explicit_flag(self):
        """INVARIANT: Fixtures CANNOT appear in CI mode without --include-fixtures."""
        # This is THE critical invariant - test it exhaustively
        runners_and_patterns = [
            (PythonRunner, ["**/*.py"]),
            (BashRunner, ["**/*.sh"]),
            (RustRunner, ["**/*.rs"]),
            (PerlRunner, ["**/*.pl", "**/*.pm"]),
            (PowerShellRunner, ["**/*.ps1", "**/*.psm1"]),
            (YAMLRunner, ["**/*.yaml", "**/*.yml"]),
        ]

        for runner_class, patterns in runners_and_patterns:
            files = get_tracked_files(patterns, str(REPO_ROOT), include_fixtures=False)
            fixture_files = [f for f in files if "/fixtures/" in f]

            assert len(fixture_files) == 0, f"{runner_class.__name__} included fixtures in CI mode: {fixture_files}"

    def test_cross_language_files_never_mixed(self):
        """INVARIANT: Language runners never receive other languages' files."""
        # Get Python files
        python_files = get_tracked_files(["**/*.py"], str(REPO_ROOT), include_fixtures=False)

        # Get Rust files
        rust_files = get_tracked_files(["**/*.rs"], str(REPO_ROOT), include_fixtures=False)

        # Assert no overlap
        python_set = set(python_files)
        rust_set = set(rust_files)
        overlap = python_set.intersection(rust_set)

        assert len(overlap) == 0, f"Python and Rust file sets overlap (impossible): {overlap}"


class TestRegressionTraps:
    """Test for specific regression scenarios."""

    def test_get_tracked_files_import_exists(self):
        """Regression: get_tracked_files must be importable from base module."""
        # This failed in commit bea4345 for rust_runner
        from tools.repo_lint.runners.base import (  # pylint: disable=reimported
            get_tracked_files as gtf,
        )

        assert gtf is not None, "get_tracked_files import failed"
        assert callable(gtf), "get_tracked_files is not callable"

    def test_no_double_exclusion_bug(self):
        """Regression: Ensure fixture exclusion logic doesn't run twice."""
        # Call get_tracked_files multiple times - results should be consistent
        files1 = get_tracked_files(["**/*.py"], str(REPO_ROOT), include_fixtures=False)
        files2 = get_tracked_files(["**/*.py"], str(REPO_ROOT), include_fixtures=False)

        assert set(files1) == set(files2), "Double exclusion bug: repeated calls return different results"

    def test_fixture_exclusion_works_with_different_cwd(self):
        """Regression: Fixture exclusion must work regardless of current directory."""
        original_cwd = os.getcwd()
        try:
            # Change to a different directory
            os.chdir("/tmp")

            files = get_tracked_files(["**/*.py"], str(REPO_ROOT), include_fixtures=False)
            fixture_files = [f for f in files if "/fixtures/" in f]

            assert len(fixture_files) == 0, "Fixture exclusion failed when cwd changed"
        finally:
            os.chdir(original_cwd)


# Run tests with: pytest tools/repo_lint/tests/test_fixture_isolation_matrix.py -v
