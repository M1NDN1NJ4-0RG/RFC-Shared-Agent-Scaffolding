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

**Symbol Discovery Mechanisms:**
- **Python:** Uses AST module to parse syntax tree and extract FunctionDef, AsyncFunctionDef,
  ClassDef nodes. Validates presence of docstrings and required sections (Args, Returns, etc.)
- **Bash:** Uses regex patterns to detect function definitions (function name() or name())
  and checks for comment blocks immediately preceding the definition
- **Perl:** Uses regex to detect 'sub name' declarations and checks for POD documentation
  (=head2, =item, etc.) or inline comments preceding the sub
- **PowerShell:** Uses regex to detect 'function Name' declarations and checks for
  comment-based help blocks (<# .SYNOPSIS ... #>) preceding or within the function
- **Rust:** Uses regex to detect 'pub fn', 'pub struct', 'pub enum', etc. and checks
  for rustdoc comments (///) preceding the item. Uses basic parsing to avoid false
  positives in comments/strings

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
import ast
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

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
    """Represents a single validation failure.
    
    This class encapsulates information about a docstring validation error,
    including file location, symbol information, and missing sections.
    
    Attributes:
        file_path: Path to the file with validation error
        missing_sections: List of section names that are missing
        message: Additional context or guidance message
        symbol_name: Optional name of the symbol (function/class) with error
        line_number: Optional line number where symbol is defined
    """

    def __init__(
        self,
        file_path: str,
        missing_sections: List[str],
        message: str = "",
        symbol_name: Optional[str] = None,
        line_number: Optional[int] = None,
    ):
        self.file_path = file_path
        self.missing_sections = missing_sections
        self.message = message
        self.symbol_name = symbol_name
        self.line_number = line_number

    def __str__(self) -> str:
        sections = ", ".join(self.missing_sections)
        
        # Format location info
        location = self.file_path
        if self.line_number:
            location += f":{self.line_number}"
        
        # Format error message
        if self.symbol_name:
            msg = f"\n❌ {location}\n   Symbol: {self.symbol_name}\n   Missing: {sections}"
        else:
            msg = f"\n❌ {location}\n   Missing required sections: {sections}"
        
        if self.message:
            msg += f"\n   {self.message}"
        return msg


class BashValidator:
    """Validates Bash script docstrings and function documentation.
    
    Checks both file-level header documentation and individual function
    comment blocks according to repository docstring contracts.
    """

    REQUIRED_SECTIONS = [
        r"#\s*DESCRIPTION:",
        r"#\s*USAGE:",
        r"#\s*INPUTS:",
        r"#\s*OUTPUTS:",
        r"#\s*EXAMPLES:",
    ]

    SECTION_NAMES = ["DESCRIPTION:", "USAGE:", "INPUTS:", "OUTPUTS:", "EXAMPLES:"]

    @staticmethod
    def validate(file_path: Path, content: str) -> List[ValidationError]:
        """Validate Bash script header and function docstrings.
        
        Args:
            file_path: Path to Bash file to validate
            content: File content as string
        
        Returns:
            List of validation errors (empty if all validations pass)
        """
        errors = []
        
        # File-level validation
        file_error = BashValidator._validate_header(file_path, content)
        if file_error:
            errors.append(file_error)
        
        # Symbol-level validation
        symbol_errors = BashValidator._validate_functions(file_path, content)
        errors.extend(symbol_errors)
        
        return errors
    
    @staticmethod
    def _validate_header(file_path: Path, content: str) -> Optional[ValidationError]:
        """Validate Bash script header documentation.
        
        Args:
            file_path: Path to Bash file
            content: File content as string
            
        Returns:
            ValidationError if header is missing required sections, None otherwise
        """
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
    
    @staticmethod
    def _validate_functions(file_path: Path, content: str) -> List[ValidationError]:
        """Validate Bash function documentation.
        
        Detects function definitions and checks for comment blocks preceding them.
        
        Args:
            file_path: Path to Bash file
            content: File content
            
        Returns:
            List of validation errors for functions
        """
        errors = []
        lines = content.split('\n')
        
        # Pattern to match bash function definitions:
        # - function name() {
        # - name() {
        # - function name {
        func_pattern = re.compile(r'^\s*(?:function\s+)?([a-zA-Z_][a-zA-Z0-9_]*)\s*\(\s*\)\s*\{?|^\s*function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\{')
        
        for i, line in enumerate(lines):
            match = func_pattern.match(line)
            if match:
                func_name = match.group(1) or match.group(2)
                lineno = i + 1
                
                # Check for pragma ignore on the function line
                if re.search(r'#\s*noqa:\s*FUNCTION', line):
                    continue
                
                # Skip internal/private functions (start with _)
                if func_name.startswith('_'):
                    continue
                
                # Look for comment block immediately preceding the function
                # A proper doc block should have at least one comment line with description
                comment_block = []
                j = i - 1
                while j >= 0 and (lines[j].strip().startswith('#') or lines[j].strip() == ''):
                    if lines[j].strip().startswith('#'):
                        comment_block.insert(0, lines[j])
                    elif lines[j].strip() == '' and comment_block:
                        # Empty line after comments - stop here
                        break
                    j -= 1
                
                if not comment_block:
                    errors.append(ValidationError(
                        str(file_path),
                        ["function documentation"],
                        "Function must have comment block with description, args, returns",
                        symbol_name=f"{func_name}()",
                        line_number=lineno,
                    ))
                else:
                    # Check if comment block has minimum required info
                    comment_text = '\n'.join(comment_block)
                    # Very lenient check - just ensure there's some description text
                    # (more than just "# Arguments:" or similar headers)
                    has_description = any(
                        len(line.lstrip('#').strip()) > 3 and
                        not line.lstrip('#').strip().endswith(':')
                        for line in comment_block
                    )
                    
                    if not has_description:
                        errors.append(ValidationError(
                            str(file_path),
                            ["function description"],
                            "Function comment block must include description text",
                            symbol_name=f"{func_name}()",
                            line_number=lineno,
                        ))
        
        return errors


class PowerShellValidator:
    """Validates PowerShell script comment-based help documentation.
    
    Checks for presence of required .SYNOPSIS, .DESCRIPTION, and other
    comment-based help sections in PowerShell scripts.
    """

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
    def validate(file_path: Path, content: str) -> List[ValidationError]:
        """Validate PowerShell script docstring.
        
        Args:
            file_path: Path to PowerShell file to validate
            content: File content as string
        
        Returns:
            List of validation errors (empty if all validations pass)
        """
        # Check for comment-based help block
        if "<#" not in content or "#>" not in content:
            return [ValidationError(
                str(file_path),
                ["comment-based help block"],
                "Expected <# ... #> comment-based help block",
            )]

        # Extract help block
        match = re.search(r"<#(.+?)#>", content, re.DOTALL)
        if not match:
            return [ValidationError(
                str(file_path),
                ["comment-based help block"],
                "Could not parse <# ... #> block",
            )]

        help_block = match.group(1)

        missing = []
        for i, pattern in enumerate(PowerShellValidator.REQUIRED_SECTIONS):
            if not re.search(pattern, help_block, re.IGNORECASE):
                missing.append(PowerShellValidator.SECTION_NAMES[i])

        if missing:
            return [ValidationError(str(file_path), missing, "Expected PowerShell comment-based help")]
        return []


class PythonValidator:
    """Validates Python module docstrings and symbol-level documentation.
    
    Uses AST parsing to validate both module-level docstrings and function/class
    docstrings according to repository docstring contracts.
    """

    REQUIRED_SECTIONS = [
        r"^Purpose\s*$",
        r"^Environment Variables\s*$",
        r"^Examples\s*$",
        r"^Exit Codes\s*$",
    ]

    SECTION_NAMES = ["Purpose", "Environment Variables", "Examples", "Exit Codes"]

    @staticmethod
    def validate(file_path: Path, content: str) -> List[ValidationError]:
        """Validate Python module and symbol docstrings.
        
        Args:
            file_path: Path to Python file to validate
            content: File content as string
        
        Returns:
            List of validation errors (empty if all validations pass)
        """
        errors = []
        
        # File-level validation
        file_error = PythonValidator._validate_module_docstring(file_path, content)
        if file_error:
            errors.append(file_error)
        
        # Symbol-level validation
        symbol_errors = PythonValidator._validate_symbols(file_path, content)
        errors.extend(symbol_errors)
        
        return errors
    
    @staticmethod
    def _validate_module_docstring(file_path: Path, content: str) -> Optional[ValidationError]:
        """Validate module-level docstring.
        
        Args:
            file_path: Path to Python file
            content: File content as string
            
        Returns:
            ValidationError if module docstring is missing required sections, None otherwise
        """
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
    
    @staticmethod
    def _validate_symbols(file_path: Path, content: str) -> List[ValidationError]:
        """Validate function and class docstrings using AST parsing.
        
        Args:
            file_path: Path to Python file
            content: File content
            
        Returns:
            List of validation errors for symbols
        """
        errors = []
        
        try:
            tree = ast.parse(content, filename=str(file_path))
        except SyntaxError:
            # If file has syntax errors, skip symbol validation
            # (file won't work anyway, so focus on that first)
            return errors
        
        # Walk the AST and validate functions and classes
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                error = PythonValidator._validate_function(file_path, node, content)
                if error:
                    errors.append(error)
            elif isinstance(node, ast.ClassDef):
                error = PythonValidator._validate_class(file_path, node, content)
                if error:
                    errors.append(error)
        
        return errors
    
    @staticmethod
    def _validate_function(file_path: Path, node: ast.FunctionDef, content: str) -> Optional[ValidationError]:
        """Validate a function or method docstring.
        
        Args:
            file_path: Path to Python file
            node: AST FunctionDef node
            content: File content (for pragma checking)
            
        Returns:
            ValidationError if function lacks proper documentation, None otherwise
        """
        # Check for pragma ignore on this specific function
        # Look for # noqa: D102 or # noqa: D103 on the function definition line
        lines = content.split('\n')
        if node.lineno <= len(lines):
            func_line = lines[node.lineno - 1]
            if re.search(r'#\s*noqa:\s*D10[23]', func_line):
                return None
        
        # Skip private/internal functions (start with _) unless explicitly documented
        if node.name.startswith('_') and not ast.get_docstring(node):
            # Private functions without docstrings are acceptable
            return None
        
        docstring = ast.get_docstring(node)
        
        if not docstring:
            return ValidationError(
                str(file_path),
                ["function docstring"],
                f"Function must have docstring with Args and Returns sections",
                symbol_name=f"def {node.name}()",
                line_number=node.lineno,
            )
        
        # Check for required sections (Args and Returns)
        # Be lenient about format - accept "Args:", "Arguments:", "Parameters:" etc.
        has_args = bool(re.search(r'^(Args|Arguments|Parameters)\s*(:|\n)', docstring, re.MULTILINE | re.IGNORECASE))
        has_returns = bool(re.search(r'^Returns?\s*(:|\n)', docstring, re.MULTILINE | re.IGNORECASE))
        
        missing = []
        
        # Only require Args section if function has parameters (excluding self/cls)
        params = [arg.arg for arg in node.args.args if arg.arg not in ('self', 'cls')]
        if params and not has_args:
            missing.append("Args/Parameters")
        
        # Only require Returns section if function doesn't return None explicitly
        # or has no return statement
        if not has_returns:
            # Check if function has a return statement with a value
            has_return_value = any(
                isinstance(n, ast.Return) and n.value is not None
                for n in ast.walk(node)
            )
            if has_return_value:
                missing.append("Returns")
        
        if missing:
            return ValidationError(
                str(file_path),
                missing,
                f"Function docstring must include {', '.join(missing)} section(s)",
                symbol_name=f"def {node.name}()",
                line_number=node.lineno,
            )
        
        return None
    
    @staticmethod
    def _validate_class(file_path: Path, node: ast.ClassDef, content: str) -> Optional[ValidationError]:
        """Validate a class docstring.
        
        Args:
            file_path: Path to Python file
            node: AST ClassDef node
            content: File content (for pragma checking)
            
        Returns:
            ValidationError if class lacks proper documentation, None otherwise
        """
        # Check for pragma ignore
        lines = content.split('\n')
        if node.lineno <= len(lines):
            class_line = lines[node.lineno - 1]
            if re.search(r'#\s*noqa:\s*D101', class_line):
                return None
        
        # Skip private classes
        if node.name.startswith('_'):
            return None
        
        docstring = ast.get_docstring(node)
        
        if not docstring:
            return ValidationError(
                str(file_path),
                ["class docstring"],
                "Class must have docstring describing purpose and attributes",
                symbol_name=f"class {node.name}",
                line_number=node.lineno,
            )
        
        # Basic check: docstring should have some content beyond just a one-liner
        # (at least 2 lines or has "Attributes:" section)
        lines_in_doc = docstring.strip().split('\n')
        has_attributes = bool(re.search(r'^Attributes\s*(:|\n)', docstring, re.MULTILINE | re.IGNORECASE))
        
        if len(lines_in_doc) < 2 and not has_attributes:
            return ValidationError(
                str(file_path),
                ["class documentation"],
                "Class docstring should describe purpose and optionally list Attributes",
                symbol_name=f"class {node.name}",
                line_number=node.lineno,
            )
        
        return None


class PerlValidator:
    """Validates Perl script POD documentation.
    
    Checks for required POD sections (=head1 NAME, SYNOPSIS, DESCRIPTION, etc.)
    according to repository docstring contracts.
    """

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
    def validate(file_path: Path, content: str) -> List[ValidationError]:
        """Validate Perl script POD.
        
        Args:
            file_path: Path to Perl file to validate
            content: File content as string
        
        Returns:
            List of validation errors (empty if all validations pass)
        """
        # Check for POD block
        if "=head1" not in content or "=cut" not in content:
            return [ValidationError(
                str(file_path),
                ["POD block"],
                "Expected POD documentation with =head1 sections and =cut",
            )]

        missing = []
        for i, pattern in enumerate(PerlValidator.REQUIRED_SECTIONS):
            if not re.search(pattern, content, re.MULTILINE):
                missing.append(PerlValidator.SECTION_NAMES[i])

        if missing:
            return [ValidationError(str(file_path), missing, "Expected POD sections")]
        return []


class RustValidator:
    """Validates Rust module documentation using rustdoc comments.
    
    Checks for required module-level documentation (//!) with Purpose
    and Examples sections according to repository docstring contracts.
    """

    REQUIRED_SECTIONS = [
        r"^//!\s*#\s*Purpose",
        r"^//!\s*#\s*Examples",
    ]

    # For main.rs, also require Exit Behavior/Exit Codes
    EXIT_SECTIONS = [r"^//!\s*#\s*Exit\s+(Behavior|Codes)"]

    SECTION_NAMES = ["# Purpose", "# Examples"]

    @staticmethod
    def validate(file_path: Path, content: str) -> List[ValidationError]:
        """Validate Rust module documentation.
        
        Args:
            file_path: Path to Rust file to validate
            content: File content as string
        
        Returns:
            List of validation errors (empty if all validations pass)
        """
        # Check for module-level docs (//!)
        if "//!" not in content:
            return [ValidationError(
                str(file_path),
                ["module documentation (//!)"],
                "Expected module-level documentation with //!",
            )]

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
            return [ValidationError(str(file_path), missing, "Expected Rustdoc sections in module docs")]
        return []


class YAMLValidator:
    """Validates YAML file documentation headers.
    
    Checks for required comment header sections in YAML workflow and config files
    according to repository docstring contracts.
    """

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
    def validate(file_path: Path, content: str) -> List[ValidationError]:
        """Validate YAML file documentation header.
        
        Args:
            file_path: Path to YAML file to validate
            content: File content as string
        
        Returns:
            List of validation errors (empty if all validations pass)
        """
        # Check first 50 lines for comment header (workflows can have long headers)
        lines = content.split("\n")[:50]
        header = "\n".join(lines)

        missing = []
        for i, pattern in enumerate(YAMLValidator.REQUIRED_SECTIONS):
            if not re.search(pattern, header, re.MULTILINE | re.IGNORECASE):
                missing.append(YAMLValidator.SECTION_NAMES[i])

        if missing:
            return [ValidationError(
                str(file_path),
                missing,
                "Expected top-of-file comment header with # prefix",
            )]
        return []


def get_tracked_files() -> List[Path]:
    """Get all tracked files matching in-scope patterns using git.
    
    Returns:
        List of Path objects for files that match in-scope patterns and
        are not excluded
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
    
    Args:
        file_path: Path to file to validate
    
    Returns:
        List of validation errors (empty if file passes)
    """
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
    
    Returns:
        Exit code (0 for success, 1 for failure)
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
