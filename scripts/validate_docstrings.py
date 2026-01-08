"""Docstring contract validator for RFC-Shared-Agent-Scaffolding.

DEPRECATED: This script is now a thin CLI wrapper around the internal
tools.repo_lint.docstrings module. For programmatic use, import the
internal module directly.

This script validates that all scripts, YAML files, and code symbols conform to their
language-specific docstring contracts as defined in docs/contributing/docstring-contracts/.

:Purpose:
    Provides CLI interface for docstring validation. The actual validation logic
    has been migrated to tools.repo_lint.docstrings for first-class integration
    with repo_lint.

:Architecture:
    This is now a compatibility wrapper that:
    - Parses CLI arguments
    - Calls the internal validation module
    - Formats and displays results

:CLI Interface:
    Run from repository root::

        python3 scripts/validate_docstrings.py

    Validate specific files (single-file mode for fast iteration)::

        python3 scripts/validate_docstrings.py --file scripts/my-script.sh
        python3 scripts/validate_docstrings.py -f script1.py -f script2.sh

    Validate only Python files::

        python3 scripts/validate_docstrings.py --language python

    Validate only Bash files::

        python3 scripts/validate_docstrings.py --language bash

    Skip content validation (only check section presence)::

        python3 scripts/validate_docstrings.py --no-content-checks

:Pragma Support:
    Scripts can use pragma comments to intentionally skip specific section checks::

        # noqa: SECTION_NAME

    The validator will skip checking for SECTION_NAME in files containing this pragma.

    Examples::

        # noqa: OUTPUTS    - Skip OUTPUTS section check
        # noqa: EXITCODES  - Skip exit codes content validation
        # noqa: D102       - Skip function docstring requirement (Python)

:Exit Codes:
    0
        All files conform to contracts
    1
        One or more files failed validation

:Environment Variables:
    None. Operates on current repository state.

:Examples:
    Validate all files::

        python3 scripts/validate_docstrings.py

    Validate specific files::

        python3 scripts/validate_docstrings.py --file script.sh --file tool.py

:Notes:
    - File-level validation checks presence of sections, not content quality
    - Symbol-level validation enforces documentation on all symbols (public and private)
      unless explicitly exempted via pragma
    - Pragma ignores should be used sparingly for legitimate exceptions
    - See docs/contributing/docstring-contracts/README.md for file-level contracts
    - See docs/contributing/docstring-contracts/symbol-level-contracts.md for symbol contracts
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

# Add repository root to path for tools.repo_lint imports
try:
    scripts_dir = Path(__file__).resolve().parent
    repo_root = scripts_dir.parent  # Get repository root (parent of scripts/)
except NameError:
    # __file__ may not be defined in some interactive contexts
    scripts_dir = Path.cwd()
    repo_root = scripts_dir

if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

# Import from internal module
# pylint: disable=wrong-import-position
from tools.repo_lint.docstrings import ValidationError, validate_files  # noqa: E402
from tools.repo_lint.yaml_loader import get_exclusion_patterns, get_in_scope_patterns  # noqa: E402


def get_tracked_files(include_fixtures: bool = False) -> List[Path]:
    """Get all tracked files matching in-scope patterns using git.

    :param include_fixtures: Whether to include test fixture files (vector mode)
    :returns: List of Path objects for files that match in-scope patterns and are not excluded
    """
    import subprocess

    try:
        result = subprocess.run(
            ["git", "ls-files"],
            capture_output=True,
            text=True,
            check=True,
        )
        all_files = result.stdout.strip().split("\n")
    except subprocess.CalledProcessError:
        print("Error: Could not get tracked files from git", file=sys.stderr)
        sys.exit(1)

    # Load patterns from YAML configuration
    in_scope_patterns = get_in_scope_patterns()
    exclude_patterns = get_exclusion_patterns()

    # Filter files by patterns
    repo_root_dir = Path.cwd()
    matched_files = []

    # Directories to exclude (test fixtures with intentional violations)
    exclude_dirs = [
        Path("conformance/repo-lint/vectors/fixtures"),
        Path("conformance/repo-lint/fixtures/violations"),
        Path("scripts/tests/fixtures"),
        Path("conformance/repo-lint/unsafe-fix-fixtures"),
        Path("tools/repo_lint/tests/fixtures"),
    ]

    for file_path in all_files:
        p = Path(file_path)

        # Check if file is in an excluded directory
        excluded = False
        if not include_fixtures:
            for exclude_dir in exclude_dirs:
                if p == exclude_dir or exclude_dir in p.parents:
                    excluded = True
                    break

        if excluded:
            continue

        # Check if file matches any exclude pattern (from YAML)
        for exclude_pattern in exclude_patterns:
            if p.match(exclude_pattern):
                excluded = True
                break

        if excluded:
            continue

        # Check if file matches any in-scope pattern (from YAML)
        for pattern in in_scope_patterns:
            if p.match(pattern):
                matched_files.append(repo_root_dir / p)
                break

    return matched_files


def filter_files_by_language(files: List[Path], language: str) -> List[Path]:
    """Filter files to only those matching specified language.

    :param files: List of file paths to filter
    :param language: Language to filter by (python, bash, perl, powershell, yaml, rust, all)
    :returns: Filtered list of file paths
    """
    if language == "all":
        return files

    # Determine language from extension
    lang_extensions = {
        "bash": [".sh", ".bash", ".zsh"],
        "powershell": [".ps1"],
        "python": [".py"],
        "perl": [".pl", ".pm"],
        "rust": [".rs"],
        "yaml": [".yml", ".yaml"],
    }

    allowed_extensions = lang_extensions.get(language, [])
    return [f for f in files if f.suffix.lower() in allowed_extensions]


def main() -> int:
    """Main entry point.

    :returns: Exit code (0 for success, 1 for failure)
    """
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Validate docstring contracts for scripts and YAML files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate all files in repository
  python3 scripts/validate-docstrings.py

  # Validate a single file (fast iteration)
  python3 scripts/validate-docstrings.py --file scripts/my-script.sh

  # Validate multiple specific files
  python3 scripts/validate-docstrings.py --file script1.py --file script2.sh
        """,
    )
    parser.add_argument(
        "--file",
        "-f",
        action="append",
        dest="files",
        help="Validate specific file(s) instead of all tracked files. Can be specified multiple times.",
    )
    parser.add_argument(
        "--no-content-checks",
        action="store_true",
        help="Skip content validation (e.g., exit code completeness checks). Only check section presence.",
    )
    parser.add_argument(
        "--language",
        "-l",
        choices=["python", "bash", "perl", "powershell", "yaml", "rust", "all"],
        default="all",
        help="Restrict validation to specific language files only. Default: all",
    )
    parser.add_argument(
        "--include-fixtures",
        action="store_true",
        help="Include test fixture files in validation (vector mode for testing)",
    )

    args = parser.parse_args()

    # Set global flag for content checks in common module
    import tools.repo_lint.docstrings.common as common_module  # noqa: E402

    common_module.SKIP_CONTENT_CHECKS = args.no_content_checks

    print("🔍 Validating docstring contracts...\n")

    # Get files to validate
    if args.files:
        # Single-file mode: validate specific files
        files = [Path(f).resolve() for f in args.files]
        # Verify files exist
        for f in files:
            if not f.exists():
                print(f"❌ Error: File not found: {f}", file=sys.stderr)
                return 1
        print(f"Validating {len(files)} specified file(s)\n")
    else:
        # Full repository scan
        files = get_tracked_files(include_fixtures=args.include_fixtures)
        print(f"Found {len(files)} files in scope\n")

    # Apply language filter
    original_count = len(files)
    files = filter_files_by_language(files, args.language)
    if args.language != "all":
        print(f"Filtered to {len(files)} {args.language} file(s) (from {original_count} total)\n")

    # Validate using internal module
    errors: List[ValidationError] = validate_files(files, language=args.language)

    # Report results
    if errors:
        # Count unique files with violations
        unique_files = len(set(e.file_path for e in errors))
        print(f"\n❌ Validation FAILED: {len(errors)} violation(s) in {unique_files} file(s)\n")
        for error in errors:
            print(error)
        print("\n💡 Tip: See docs/contributing/docstring-contracts/ for contract details and templates\n")
        print("💡 Tip: Use # noqa: SECTION or # noqa: D102 pragmas to exempt specific items\n")
        return 1
    else:
        print(f"✅ All {len(files)} files conform to docstring contracts\n")
        return 0


if __name__ == "__main__":
    sys.exit(main())
