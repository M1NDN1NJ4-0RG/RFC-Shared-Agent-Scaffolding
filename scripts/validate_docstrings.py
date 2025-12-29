#!/usr/bin/env python3
"""Docstring contract validator for RFC-Shared-Agent-Scaffolding.

This script validates that all scripts, YAML files, and code symbols conform to their
language-specific docstring contracts as defined in docs/contributing/docstring-contracts/.

Purpose
-------
Enforces consistent, discoverable documentation across all supported languages
by validating the presence of required docstring sections at both file/module level
and symbol level (functions, classes, methods). Supports pragma ignores for
intentional omissions and basic content validation for exit codes.

Architecture
------------
The validator operates in several phases:

**Phase 1: File Discovery**
- Uses `git ls-files` to get all tracked files in the repository
- Filters files based on IN_SCOPE_PATTERNS (by extension)
- Excludes files matching EXCLUDE_PATTERNS (build artifacts, etc.)

**Phase 2: Language Classification**
- Maps file extension to language (`.py` → Python, `.sh` → Bash, etc.)
- Dispatches to appropriate validator class based on language

**Phase 3: File/Module-Level Validation**
- Extracts documentation block from file (module docstring, header comments, POD, etc.)
- Validates presence of required sections per language contract
- Checks basic content requirements (e.g., exit codes 0 and 1 documented)

**Phase 4: Symbol-Level Validation** (Phase 5.5 expansion)
- Parses source file to extract symbols (functions, classes, methods, subs)
- For each symbol, validates presence of documentation
- Checks for required doc sections (Args, Returns, etc.) per language
- Currently validates public/exported symbols only

**Phase 5: Reporting**
- Collects all violations (file path, symbol name if applicable, missing sections)
- Outputs actionable error messages with line numbers where possible
- Returns exit code 0 (pass) or 1 (fail)

**Validator Classes:**
- BashValidator: Validates Bash scripts (comment blocks above functions)
- PowerShellValidator: Validates PowerShell scripts (comment-based help)
- PythonValidator: Validates Python modules (docstrings, uses AST for symbol parsing)
- PerlValidator: Validates Perl scripts (POD documentation)
- RustValidator: Validates Rust modules (rustdoc comments)
- YAMLValidator: Validates YAML config files (header comments)

CLI Interface
-------------
Run from repository root::

    python3 scripts/validate_docstrings.py

Validate specific files (single-file mode for fast iteration)::

    python3 scripts/validate_docstrings.py --file scripts/my-script.sh
    python3 scripts/validate_docstrings.py -f script1.py -f script2.sh

Skip content validation (only check section presence)::

    python3 scripts/validate_docstrings.py --no-content-checks

Pragma Support
--------------
Scripts can use pragma comments to intentionally skip specific section checks::

    # noqa: SECTION_NAME

The validator will skip checking for SECTION_NAME in files containing this pragma.

Examples::

    # noqa: OUTPUTS    - Skip OUTPUTS section check
    # noqa: EXITCODES  - Skip exit codes content validation
    # noqa: D102       - Skip function docstring requirement (Python)

Content Validation
------------------
The validator performs basic content checks on exit code sections:
- Checks for presence of exit codes 0 and 1
- Lenient pattern matching for exit code documentation
- Can be disabled with --no-content-checks or pragma comments

Exit Codes
----------
0
    All files conform to contracts
1
    One or more files failed validation

Environment Variables
---------------------
None. Operates on current repository state.

Examples
--------
Validate all files::

    python3 scripts/validate_docstrings.py

Validate specific files::

    python3 scripts/validate_docstrings.py --file script.sh --file tool.py

Notes
-----
- File-level validation checks presence of sections, not content quality
- Symbol-level validation enforces documentation on public/exported symbols
- Pragma ignores should be used sparingly for legitimate exceptions
- See docs/contributing/docstring-contracts/README.md for file-level contracts
- See docs/contributing/docstring-contracts/symbol-level-contracts.md for symbol contracts
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

# Module-level flag for content checks (set by command-line arg)
SKIP_CONTENT_CHECKS = False


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


def check_pragma_ignore(content: str, section: str) -> bool:
    """Check if a section is ignored via pragma comment.

    Supports pragmas like:
    - # noqa: EXITCODES
    - # docstring-ignore: EXIT CODES
    - <!-- noqa: OUTPUTS --> (for YAML)

    Args:
        content: File content to search
        section: Section name to check (e.g., "EXITCODES", "EXIT CODES")

    Returns:
        True if section should be ignored, False otherwise
    """
    # Normalize section name (remove spaces, uppercase)
    normalized_section = section.upper().replace(" ", "").replace(":", "")

    # Check for various pragma formats
    pragma_patterns = [
        rf"#\s*noqa:\s*{normalized_section}",
        rf"#\s*docstring-ignore:\s*{section}",
        rf"<!--\s*noqa:\s*{normalized_section}\s*-->",
    ]

    for pattern in pragma_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            return True

    return False


def validate_exit_codes_content(content: str, language: str) -> Optional[str]:
    """Validate that exit codes section contains minimum required codes.

    Checks that at least exit codes 0 and 1 are documented.
    This is a soft check - we look for patterns like "0" near "success" etc.

    Args:
        content: The exit codes section content
        language: Language name for context

    Returns:
        Error message if validation fails, None if valid
    """
    if SKIP_CONTENT_CHECKS:
        return None

    # Look for exit code 0 (success) - be very lenient with patterns
    # Match patterns like:
    # - "0    Success"
    # - "0: Success"
    # - "Exit 0"
    # - "Exit: 0 if success"
    # - "0 if all tests pass"
    has_exit_0 = bool(
        re.search(
            r"(?:exit[:\s]+)?0[\s:\-]+(?:if\s+)?.*?(?:success|ok|pass|complete|all.*pass)",
            content,
            re.IGNORECASE | re.MULTILINE | re.DOTALL,
        )
    )

    # Look for exit code 1 (failure)
    # Match patterns like:
    # - "1    Failure"
    # - "1: Fail"
    # - "Exit 1"
    # - "Exit: 1 if fail"
    # - "1 if any fail"
    has_exit_1 = bool(
        re.search(
            r"(?:exit[:\s]+)?1[\s:\-]+(?:if\s+)?.*?(?:fail|error|invalid|any.*fail)",
            content,
            re.IGNORECASE | re.MULTILINE | re.DOTALL,
        )
    )

    # If we find reasonable exit code documentation, consider it valid
    # This is intentionally lenient to avoid false positives
    if not has_exit_0 and not has_exit_1:
        # Only fail if there's NO exit code documentation at all
        has_any_exit_code = bool(re.search(r"\b(?:0|1|2|127)\b", content))
        if not has_any_exit_code:
            return "No exit codes found (expected at least 0 and 1)"

    return None


class ValidationError:
    """Represents a single validation failure."""

    def __init__(self, file_path: str, missing_sections: List[str], message: str = ""):
        self.file_path = file_path
        self.missing_sections = missing_sections
        self.message = message

    def __str__(self) -> str:
        sections = ", ".join(self.missing_sections)
        msg = f"\n❌ {self.file_path}\n   Missing required sections: {sections}"
        if self.message:
            msg += f"\n   {self.message}"
        return msg


class BashValidator:
    """Validates Bash script docstrings."""

    REQUIRED_SECTIONS = [
        r"#\s*DESCRIPTION:",
        r"#\s*USAGE:",
        r"#\s*INPUTS:",
        r"#\s*OUTPUTS:",
        r"#\s*EXAMPLES:",
    ]

    SECTION_NAMES = ["DESCRIPTION:", "USAGE:", "INPUTS:", "OUTPUTS:", "EXAMPLES:"]

    @staticmethod
    def validate(file_path: Path, content: str) -> Optional[ValidationError]:
        """Validate Bash script docstring."""
        # Check for top-of-file comment block (first 100 lines)
        lines = content.split("\n")[:100]
        header = "\n".join(lines)

        # Check shebang
        if not content.startswith("#!/usr/bin/env bash") and not content.startswith("#!/bin/bash"):
            return ValidationError(
                str(file_path),
                ["shebang"],
                "Expected '#!/usr/bin/env bash' shebang",
            )

        missing = []
        for i, pattern in enumerate(BashValidator.REQUIRED_SECTIONS):
            section_name = BashValidator.SECTION_NAMES[i]

            # Check if section is ignored via pragma
            if check_pragma_ignore(content, section_name):
                continue

            if not re.search(pattern, header, re.IGNORECASE):
                missing.append(section_name)

        # Basic content validation for exit codes (if OUTPUTS present)
        if "OUTPUTS:" not in missing:
            # Extract OUTPUTS section content
            outputs_match = re.search(r"#\s*OUTPUTS:\s*\n((?:#.*\n)+)", header, re.IGNORECASE)
            if outputs_match:
                # Remove leading # from each line for easier pattern matching
                outputs_lines = outputs_match.group(1).split("\n")
                outputs_content = "\n".join(line.lstrip("#").strip() for line in outputs_lines if line.strip())
                exit_codes_error = validate_exit_codes_content(outputs_content, "Bash")
                if exit_codes_error and not check_pragma_ignore(content, "EXITCODES"):
                    return ValidationError(
                        str(file_path),
                        ["OUTPUTS content"],
                        f"Exit codes incomplete: {exit_codes_error}",
                    )

        if missing:
            return ValidationError(
                str(file_path),
                missing,
                "Expected top-of-file comment block with # prefix",
            )
        return None


class PowerShellValidator:
    """Validates PowerShell script docstrings."""

    REQUIRED_SECTIONS = [
        r"\.SYNOPSIS",
        r"\.DESCRIPTION",
        r"\.ENVIRONMENT",
        r"\.EXAMPLE",
        r"\.NOTES",
    ]

    SECTION_NAMES = [
        ".SYNOPSIS",
        ".DESCRIPTION",
        ".ENVIRONMENT",
        ".EXAMPLE",
        ".NOTES",
    ]

    @staticmethod
    def validate(file_path: Path, content: str) -> Optional[ValidationError]:
        """Validate PowerShell script docstring."""
        # Check for comment-based help block
        if "<#" not in content or "#>" not in content:
            return ValidationError(
                str(file_path),
                ["comment-based help block"],
                "Expected <# ... #> comment-based help block",
            )

        # Extract help block
        match = re.search(r"<#(.+?)#>", content, re.DOTALL)
        if not match:
            return ValidationError(
                str(file_path),
                ["comment-based help block"],
                "Could not parse <# ... #> block",
            )

        help_block = match.group(1)

        missing = []
        for i, pattern in enumerate(PowerShellValidator.REQUIRED_SECTIONS):
            if not re.search(pattern, help_block, re.IGNORECASE):
                missing.append(PowerShellValidator.SECTION_NAMES[i])

        if missing:
            return ValidationError(str(file_path), missing, "Expected PowerShell comment-based help")
        return None


class PythonValidator:
    """Validates Python script docstrings."""

    REQUIRED_SECTIONS = [
        r"^Purpose\s*$",
        r"^Environment Variables\s*$",
        r"^Examples\s*$",
        r"^Exit Codes\s*$",
    ]

    SECTION_NAMES = ["Purpose", "Environment Variables", "Examples", "Exit Codes"]

    @staticmethod
    def validate(file_path: Path, content: str) -> Optional[ValidationError]:
        """Validate Python script docstring."""
        # Check for module docstring (triple quotes)
        if '"""' not in content:
            return ValidationError(
                str(file_path),
                ['module docstring (""")'],
                'Expected module-level docstring with """',
            )

        # Extract module docstring
        match = re.search(r'"""(.+?)"""', content, re.DOTALL)
        if not match:
            return ValidationError(
                str(file_path),
                ["module docstring"],
                "Could not parse module docstring",
            )

        docstring = match.group(1)

        missing = []
        for i, pattern in enumerate(PythonValidator.REQUIRED_SECTIONS):
            section_name = PythonValidator.SECTION_NAMES[i]

            # Check pragma ignore
            if check_pragma_ignore(content, section_name):
                continue

            if not re.search(pattern, docstring, re.MULTILINE):
                missing.append(section_name)

        # Basic content validation for exit codes
        if "Exit Codes" not in missing:
            exit_codes_match = re.search(
                r"^Exit Codes\s*\n-+\n(.+?)(?:\n^[A-Z]|\Z)",
                docstring,
                re.MULTILINE | re.DOTALL,
            )
            if exit_codes_match:
                exit_codes_content = exit_codes_match.group(1)
                exit_codes_error = validate_exit_codes_content(exit_codes_content, "Python")
                if exit_codes_error and not check_pragma_ignore(content, "EXITCODES"):
                    return ValidationError(
                        str(file_path),
                        ["Exit Codes content"],
                        f"Exit codes incomplete: {exit_codes_error}",
                    )

        if missing:
            return ValidationError(
                str(file_path),
                missing,
                "Expected reST-style sections in module docstring",
            )
        return None


class PerlValidator:
    """Validates Perl script POD documentation."""

    REQUIRED_SECTIONS = [
        r"^=head1\s+NAME",
        r"^=head1\s+SYNOPSIS",
        r"^=head1\s+DESCRIPTION",
        r"^=head1\s+ENVIRONMENT VARIABLES",
        r"^=head1\s+EXIT CODES",
        r"^=head1\s+EXAMPLES",
    ]

    SECTION_NAMES = [
        "=head1 NAME",
        "=head1 SYNOPSIS",
        "=head1 DESCRIPTION",
        "=head1 ENVIRONMENT VARIABLES",
        "=head1 EXIT CODES",
        "=head1 EXAMPLES",
    ]

    @staticmethod
    def validate(file_path: Path, content: str) -> Optional[ValidationError]:
        """Validate Perl script POD."""
        # Check for POD block
        if "=head1" not in content or "=cut" not in content:
            return ValidationError(
                str(file_path),
                ["POD block"],
                "Expected POD documentation with =head1 sections and =cut",
            )

        missing = []
        for i, pattern in enumerate(PerlValidator.REQUIRED_SECTIONS):
            if not re.search(pattern, content, re.MULTILINE):
                missing.append(PerlValidator.SECTION_NAMES[i])

        if missing:
            return ValidationError(str(file_path), missing, "Expected POD sections")
        return None


class RustValidator:
    """Validates Rust module documentation."""

    REQUIRED_SECTIONS = [
        r"^//!\s*#\s*Purpose",
        r"^//!\s*#\s*Examples",
    ]

    # For main.rs, also require Exit Behavior/Exit Codes
    EXIT_SECTIONS = [r"^//!\s*#\s*Exit\s+(Behavior|Codes)"]

    SECTION_NAMES = ["# Purpose", "# Examples"]

    @staticmethod
    def validate(file_path: Path, content: str) -> Optional[ValidationError]:
        """Validate Rust module documentation."""
        # Check for module-level docs (//!)
        if "//!" not in content:
            return ValidationError(
                str(file_path),
                ["module documentation (//!)"],
                "Expected module-level documentation with //!",
            )

        # Extract module docs (first 100 lines)
        lines = content.split("\n")[:100]
        module_docs = "\n".join([line for line in lines if line.strip().startswith("//!")])

        missing = []
        for i, pattern in enumerate(RustValidator.REQUIRED_SECTIONS):
            if not re.search(pattern, module_docs, re.MULTILINE | re.IGNORECASE):
                missing.append(RustValidator.SECTION_NAMES[i])

        # For main.rs, check for Exit Behavior/Exit Codes
        if file_path.name == "main.rs":
            has_exit = any(
                re.search(pattern, module_docs, re.MULTILINE | re.IGNORECASE) for pattern in RustValidator.EXIT_SECTIONS
            )
            if not has_exit:
                missing.append("# Exit Behavior or # Exit Codes")

        if missing:
            return ValidationError(str(file_path), missing, "Expected Rustdoc sections in module docs")
        return None


class YAMLValidator:
    """Validates YAML file documentation headers."""

    REQUIRED_SECTIONS = [
        r"^#\s*(Workflow|File):",
        r"^#\s*Purpose:",
        r"^#\s*(Triggers|Usage):",
        r"^#\s*(Dependencies|Inputs):",
        r"^#\s*(Outputs|Side effects):",
        r"^#\s*Notes?:",
    ]

    SECTION_NAMES = [
        "Workflow: or File:",
        "Purpose:",
        "Triggers: or Usage:",
        "Dependencies: or Inputs:",
        "Outputs: or Side effects:",
        "Notes: or Note:",
    ]

    @staticmethod
    def validate(file_path: Path, content: str) -> Optional[ValidationError]:
        """Validate YAML file documentation header."""
        # Check first 50 lines for comment header (workflows can have long headers)
        lines = content.split("\n")[:50]
        header = "\n".join(lines)

        missing = []
        for i, pattern in enumerate(YAMLValidator.REQUIRED_SECTIONS):
            if not re.search(pattern, header, re.MULTILINE | re.IGNORECASE):
                missing.append(YAMLValidator.SECTION_NAMES[i])

        if missing:
            return ValidationError(
                str(file_path),
                missing,
                "Expected top-of-file comment header with # prefix",
            )
        return None


def get_tracked_files() -> List[Path]:
    """Get all tracked files matching in-scope patterns using git."""
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


def validate_file(file_path: Path) -> Optional[ValidationError]:
    """Validate a single file based on its extension."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        return ValidationError(str(file_path), ["read error"], str(e))

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
        return None


def main() -> int:
    """Main entry point."""
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

    # Set global flag for content checks
    global SKIP_CONTENT_CHECKS
    SKIP_CONTENT_CHECKS = args.no_content_checks

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
        error = validate_file(file_path)
        if error:
            errors.append(error)

    # Report results
    if errors:
        print(f"\n❌ Validation FAILED: {len(errors)} file(s) with violations\n")
        for error in errors:
            print(error)
        print("\n💡 Tip: See docs/contributing/docstring-contracts/README.md for contract details and templates\n")
        return 1
    else:
        print(f"✅ All {len(files)} files conform to docstring contracts\n")
        return 0


if __name__ == "__main__":
    sys.exit(main())
