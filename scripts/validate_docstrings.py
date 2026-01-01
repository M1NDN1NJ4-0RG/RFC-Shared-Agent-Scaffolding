#!/usr/bin/env python3
"""Docstring contract validator for RFC-Shared-Agent-Scaffolding.

This script validates that all scripts, YAML files, and code symbols conform to their
language-specific docstring contracts as defined in docs/contributing/docstring-contracts/.

:Purpose:
    Enforces consistent, discoverable documentation across all supported languages
    by validating the presence of required docstring sections at both file/module level
    and symbol level (functions, classes, methods). Supports pragma ignores for
    intentional omissions and basic content validation for exit codes.

:Architecture:

    The validator operates in several phases:

    **Phase 1: File Discovery**
        - Uses ``git ls-files`` to get all tracked files in the repository
        - Filters files based on IN_SCOPE_PATTERNS (by extension)
        - Excludes files matching EXCLUDE_PATTERNS (build artifacts, etc.)

    **Phase 2: Language Classification**
        - Maps file extension to language (``.py`` → Python, ``.sh`` → Bash, etc.)
        - Dispatches to appropriate validator module based on language

    **Phase 3: File/Module-Level Validation**
        - Extracts documentation block from file (module docstring, header comments, POD, etc.)
        - Validates presence of required sections per language contract
        - Checks basic content requirements (e.g., exit codes 0 and 1 documented)

    **Phase 4: Symbol-Level Validation** (Phase 5.5 expansion)
        - Parses source file to extract symbols (functions, classes, methods, subs)
        - For each symbol, validates presence of documentation
        - Checks for required doc sections (Args, Returns, etc.) per language
        - Validates all symbols (public and private) unless explicitly exempted via pragma

:Symbol Discovery Mechanisms:

    Each language validator uses appropriate parsing techniques:

    - **Python:** AST module to parse syntax tree and extract FunctionDef, AsyncFunctionDef,
      ClassDef nodes. Validates presence of docstrings and required sections (Args, Returns, etc.)
    - **Bash:** Regex patterns to detect function definitions (function name() or name())
      and checks for comment blocks immediately preceding the definition
    - **Perl:** Regex to detect 'sub name' declarations and checks for POD documentation
      (=head2, =item, etc.) or inline comments preceding the sub
    - **PowerShell:** Regex to detect 'function Name' declarations and checks for
      comment-based help blocks (<# .SYNOPSIS ... #>) preceding or within the function
    - **Rust:** Regex to detect 'pub fn', 'pub struct', 'pub enum', etc. and checks
      for rustdoc comments (///) preceding the item

:Modular Design (Phase 5.5):

    Language-specific validation logic is isolated in separate modules under
    ``scripts/docstring_validators/``:

    - ``common.py``: Shared utilities (ValidationError, pragma checking, exit code validation)
    - ``bash_validator.py``: BashValidator class
    - ``powershell_validator.py``: PowerShellValidator class
    - ``python_validator.py``: PythonValidator class (uses AST)
    - ``perl_validator.py``: PerlValidator class
    - ``rust_validator.py``: RustValidator class
    - ``yaml_validator.py``: YAMLValidator class

    This script serves as the CLI entrypoint, handling:
    - Argument parsing
    - File discovery via git
    - Dispatch to language-specific validators
    - Unified result reporting

:Reporting:

    - Collects all violations (file path, symbol name if applicable, missing sections)
    - Outputs actionable error messages with line numbers where possible
    - Returns exit code 0 (pass) or 1 (fail)

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

:Content Validation:

    The validator performs basic content checks on exit code sections:

    - Checks for presence of exit codes 0 and 1
    - Lenient pattern matching for exit code documentation
    - Can be disabled with --no-content-checks or pragma comments

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

import argparse
import subprocess
import sys
import warnings
from pathlib import Path
from typing import List

# Add scripts directory to path for imports
try:
    scripts_dir = Path(__file__).resolve().parent
    repo_root = scripts_dir.parent  # Get repository root (parent of scripts/)
except NameError:
    # __file__ may not be defined in some interactive contexts
    scripts_dir = Path.cwd()
    repo_root = scripts_dir

if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

# Add repository root to path for tools.repo_lint imports (Phase 2.9)
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

# Import validator classes from modular package
# pylint: disable=wrong-import-position
from docstring_validators.bash_validator import BashValidator  # noqa: E402
from docstring_validators.common import ValidationError  # noqa: E402
from docstring_validators.perl_validator import PerlValidator  # noqa: E402
from docstring_validators.powershell_validator import PowerShellValidator  # noqa: E402
from docstring_validators.python_validator import PythonValidator  # noqa: E402
from docstring_validators.rust_validator import RustValidator  # noqa: E402
from docstring_validators.yaml_validator import YAMLValidator  # noqa: E402

# Access common module for SKIP_CONTENT_CHECKS flag
common_module = sys.modules["docstring_validators.common"]  # noqa: E402


# Phase 2.9 YAML-first migration: Patterns loaded from YAML configuration
# DEPRECATED: Direct constant access will be removed in future version


def _get_in_scope_patterns():
    """Load in-scope patterns from YAML configuration (Phase 2.9).

    :returns: List of file patterns to include in validation
    """
    # pylint: disable=import-outside-toplevel
    from tools.repo_lint.yaml_loader import get_in_scope_patterns

    return get_in_scope_patterns()


def _get_exclude_patterns():
    """Load exclusion patterns from YAML configuration (Phase 2.9).

    :returns: List of file patterns to exclude from validation
    """
    # pylint: disable=import-outside-toplevel
    from tools.repo_lint.yaml_loader import get_exclusion_patterns

    return get_exclusion_patterns()


# Backward compatibility with deprecation warning
def __getattr__(name):
    """Provide backward compatibility for pattern constants with deprecation warning.

    :param name: Attribute name being accessed
    :returns: Pattern list from YAML config
    :raises AttributeError: If attribute doesn't exist
    """
    if name == "IN_SCOPE_PATTERNS":
        warnings.warn(
            "IN_SCOPE_PATTERNS constant is deprecated. Use _get_in_scope_patterns() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return _get_in_scope_patterns()
    elif name == "EXCLUDE_PATTERNS":
        warnings.warn(
            "EXCLUDE_PATTERNS constant is deprecated. Use _get_exclude_patterns() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return _get_exclude_patterns()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def get_tracked_files(include_fixtures: bool = False) -> List[Path]:
    """Get all tracked files matching in-scope patterns using git (YAML-first, Phase 2.9).

    :param include_fixtures: Whether to include test fixture files (vector mode)
    :returns: List of Path objects for files that match in-scope patterns and are not excluded

    :Note:
        Updated in Phase 2.9 to load patterns from YAML configuration instead of
        hardcoded constants. When include_fixtures=True (vector mode), test fixture
        files are included in the results.
    """
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

    # Load patterns from YAML configuration (Phase 2.9)
    in_scope_patterns = _get_in_scope_patterns()
    exclude_patterns = _get_exclude_patterns()

    # Filter files by patterns
    # Note: Using repository root to construct absolute paths from git ls-files relative paths
    repo_root_dir = Path.cwd()
    matched_files = []

    # Directories to exclude (test fixtures with intentional violations)
    # TODO: Remove this hardcoded list and use get_linting_exclusion_paths() from yaml_loader  # pylint: disable=fixme
    # This duplicates the YAML config and is not maintainable. Should call the aggregation
    # function instead of maintaining a parallel list here.
    # NOTE: These are also in YAML config, but kept here for directory-based filtering
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
        # Compatibility-friendly check: treat file as excluded if it is the
        # directory itself or is located within that directory.
        # Skip fixture exclusions when in vector mode (include_fixtures=True)
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


def get_language_from_extension(file_path: Path) -> str:
    """Determine language from file extension.

    :param file_path: Path to file
    :returns: Language name (python, bash, perl, powershell, yaml, rust) or empty string if unknown"""
    suffix = file_path.suffix.lower()

    if suffix in [".sh", ".bash", ".zsh"]:
        return "bash"
    elif suffix == ".ps1":
        return "powershell"
    elif suffix == ".py":
        return "python"
    elif suffix in [".pl", ".pm"]:
        return "perl"
    elif suffix == ".rs":
        return "rust"
    elif suffix in [".yml", ".yaml"]:
        return "yaml"
    else:
        return ""


def filter_files_by_language(files: List[Path], language: str) -> List[Path]:
    """Filter files to only those matching specified language.

    :param files: List of file paths to filter
    :param language: Language to filter by (python, bash, perl, powershell, yaml, rust, all)
    :returns: Filtered list of file paths"""
    if language == "all":
        return files

    return [f for f in files if get_language_from_extension(f) == language]


def validate_file(file_path: Path) -> List[ValidationError]:
    """Validate a single file based on its extension.

    :param file_path: Path to file to validate
    :returns: List of validation errors (empty if file passes)"""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        return [ValidationError(str(file_path), ["read error"], str(e))]

    # Dispatch to appropriate validator
    suffix = file_path.suffix.lower()

    if suffix in [".sh", ".bash", ".zsh"]:
        return BashValidator.validate(file_path, content)
    elif suffix == ".ps1":
        return PowerShellValidator.validate(file_path, content)
    elif suffix == ".py":
        return PythonValidator.validate(file_path, content)
    elif suffix in [".pl", ".pm"]:
        return PerlValidator.validate(file_path, content)
    elif suffix == ".rs":
        return RustValidator.validate(file_path, content)
    elif suffix in [".yml", ".yaml"]:
        return YAMLValidator.validate(file_path, content)
    else:
        # Unknown extension, skip
        return []


def main() -> int:
    """Main entry point.

    :returns: Exit code (0 for success, 1 for failure)"""
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

    # Validate each file
    errors: List[ValidationError] = []
    for file_path in files:
        file_errors = validate_file(file_path)
        errors.extend(file_errors)

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
