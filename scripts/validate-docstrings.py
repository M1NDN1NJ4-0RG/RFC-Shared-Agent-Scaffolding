#!/usr/bin/env python3
"""Docstring contract validator for RFC-Shared-Agent-Scaffolding.

This script validates that all scripts and YAML files conform to their
language-specific docstring contracts as defined in docs/docstrings/.

Purpose
-------
Enforces consistent, discoverable documentation across all supported languages
by validating the presence of required docstring sections.

CLI Interface
-------------
Run from repository root::

    python3 scripts/validate-docstrings.py

Environment Variables
---------------------
None. This script does not use environment variables.

Exit Codes
----------
0
    All files conform to docstring contracts
1
    Validation failures detected (violations printed to stdout)

Examples
--------
Run validator from repository root::

    python3 scripts/validate-docstrings.py

Run in CI::

    python3 scripts/validate-docstrings.py || exit 1

Notes
-----
- Validation is lightweight: checks presence of sections, not content quality
- Uses regex-based pattern matching (no heavy parsing)
- Scans only tracked files (via git ls-files)
- Provides actionable error messages with file path and missing sections
- Validates ALL scripts in repository (not just specific directories)
"""

import re
import subprocess
import sys
from pathlib import Path
from typing import List, Optional


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
        if not content.startswith("#!/usr/bin/env bash") and not content.startswith(
            "#!/bin/bash"
        ):
            return ValidationError(
                str(file_path),
                ["shebang"],
                "Expected '#!/usr/bin/env bash' shebang",
            )

        missing = []
        for i, pattern in enumerate(BashValidator.REQUIRED_SECTIONS):
            if not re.search(pattern, header, re.IGNORECASE):
                missing.append(BashValidator.SECTION_NAMES[i])

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
            return ValidationError(
                str(file_path), missing, "Expected PowerShell comment-based help"
            )
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
            if not re.search(pattern, docstring, re.MULTILINE):
                missing.append(PythonValidator.SECTION_NAMES[i])

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
        module_docs = "\n".join([l for l in lines if l.strip().startswith("//!")])

        missing = []
        for i, pattern in enumerate(RustValidator.REQUIRED_SECTIONS):
            if not re.search(pattern, module_docs, re.MULTILINE | re.IGNORECASE):
                missing.append(RustValidator.SECTION_NAMES[i])

        # For main.rs, check for Exit Behavior/Exit Codes
        if file_path.name == "main.rs":
            has_exit = any(
                re.search(pattern, module_docs, re.MULTILINE | re.IGNORECASE)
                for pattern in RustValidator.EXIT_SECTIONS
            )
            if not has_exit:
                missing.append("# Exit Behavior or # Exit Codes")

        if missing:
            return ValidationError(
                str(file_path), missing, "Expected Rustdoc sections in module docs"
            )
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
    print("🔍 Validating docstring contracts...\n")

    # Get files to validate
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
        print(
            f"\n💡 Tip: See docs/docstrings/README.md for contract details and templates\n"
        )
        return 1
    else:
        print(f"✅ All {len(files)} files conform to docstring contracts\n")
        return 0


if __name__ == "__main__":
    sys.exit(main())
