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
import os
import subprocess
import sys
from pathlib import Path
from typing import List

# Add scripts directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Import validator classes from modular package
# pylint: disable=wrong-import-position
from docstring_validators.bash_validator import BashValidator  # noqa: E402
from docstring_validators.common import ValidationError  # noqa: E402
from docstring_validators.perl_validator import PerlValidator  # noqa: E402
from docstring_validators.powershell_validator import PowerShellValidator  # noqa: E402
from docstring_validators.python_validator import PythonValidator  # noqa: E402
from docstring_validators.rust_validator import RustValidator  # noqa: E402
from docstring_validators.yaml_validator import YAMLValidator  # noqa: E402
import docstring_validators.common as common_module  # noqa: E402


# In-scope directory patterns for validation
# Strategy: Include ALL scripts repository-wide, with explicit exclusions
IN_SCOPE_PATTERNS = [
    # All Bash scripts
    "**/*.sh",
    "**/*.bash",
    "**/*.zsh",
    # All PowerShell scripts
    "**/*.ps1",
    # All Python scripts
    "**/*.py",
    # All Perl scripts
    "**/*.pl",
    "**/*.pm",
    # All Rust source files
    "rust/src/**/*.rs",
    # All YAML workflow and config files
    ".github/workflows/*.yml",
    ".github/workflows/*.yaml",
    ".github/ISSUE_TEMPLATE/*.yml",
    ".github/ISSUE_TEMPLATE/*.yaml",
]

# Patterns to exclude from validation
EXCLUDE_PATTERNS = [
    # Build artifacts and dependencies
    "dist/**",
    "target/**",
    "node_modules/**",
    "__pycache__/**",
    "*.pyc",
    # Git directory
    ".git/**",
    # Rust test files (these are tested via cargo test, not as standalone scripts)
    "rust/tests/**",
    # Temporary files
    "tmp/**",
    ".tmp/**",
]


def get_tracked_files() -> List[Path]:
    """Get all tracked files matching in-scope patterns using git.

    :returns: List of Path objects for files that match in-scope patterns and are not excluded"""
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

    # Filter files by patterns
    repo_root = Path.cwd()
    matched_files = []

    for file_path in all_files:
        p = Path(file_path)

        # Check if file matches any exclude pattern first
        excluded = False
        for exclude_pattern in EXCLUDE_PATTERNS:
            if p.match(exclude_pattern):
                excluded = True
                break

        if excluded:
            continue

        # Check if file matches any in-scope pattern
        for pattern in IN_SCOPE_PATTERNS:
            if p.match(pattern):
                matched_files.append(repo_root / p)
                break

    return matched_files


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
        files = get_tracked_files()
        print(f"Found {len(files)} files in scope\n")

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
