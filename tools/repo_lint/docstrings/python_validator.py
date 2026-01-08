#!/usr/bin/env python3
# noqa: EXITCODES
"""Python module docstring validator.

This module validates Python module documentation, including module-level
docstrings and symbol-level documentation (functions, classes, methods).

:Purpose:
    Enforce Python docstring contracts as defined in
    docs/contributing/docstring-contracts/python.md

:Environment Variables:
    None

:Examples:
    Validate a Python module::

        from docstring_validators.python_validator import PythonValidator
        errors = PythonValidator.validate(file_path, content)

:Exit Codes:
    N/A - This is a library module, not an executable script
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import List

from .common import ValidationError, check_pragma_ignore, validate_exit_codes_content


class PythonValidator:
    """Validates Python module docstrings and symbol-level documentation.

    Uses AST parsing to validate both module-level docstrings and function/class
    docstrings according to repository docstring contracts.
    """

    REQUIRED_SECTIONS = [
        r"^:Purpose:\s*$",
        r"^:Environment Variables:\s*$",
        r"^:Examples:\s*$",
        r"^:Exit Codes:\s*$",
    ]

    SECTION_NAMES = ["Purpose", "Environment Variables", "Examples", "Exit Codes"]

    @staticmethod
    def validate(file_path: Path, content: str) -> List[ValidationError]:
        """Validate Python module and symbol docstrings.

        :param file_path: Path to Python file to validate
        :param content: File content as string

        :returns: List of validation errors (empty if all validations pass)
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
    def _validate_module_docstring(file_path: Path, content: str) -> ValidationError | None:
        """Validate module-level docstring.

        :param file_path: Path to Python file
        :param content: File content as string

        :returns: ValidationError if module docstring is missing required sections, None otherwise
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
            # Try reST field format first (:Exit Codes:)
            exit_codes_match = re.search(
                r"^:Exit Codes:\s*\n+(.+?)(?:\n^:|\Z)",
                docstring,
                re.MULTILINE | re.DOTALL,
            )
            # Fallback to underline format (Exit Codes\n---)
            if not exit_codes_match:
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

        :param file_path: Path to Python file
        :param content: File content

        :returns: List of validation errors for symbols
        """
        errors = []

        try:
            tree = ast.parse(content, filename=str(file_path))
        except SyntaxError:
            # If file has syntax errors, skip symbol validation
            # (file won't work anyway, so focus on that first)
            return errors

        # Walk the entire AST and validate ALL functions and classes
        # This includes nested functions, helper functions, everything
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
    def _validate_function(file_path: Path, node: ast.FunctionDef, content: str) -> ValidationError | None:
        """Validate a function or method docstring.

        :param file_path: Path to Python file
        :param node: AST FunctionDef node
        :param content: File content (for pragma checking)

        :returns: ValidationError if function lacks proper documentation, None otherwise
        """
        # Check for pragma ignore on this specific function
        # Look for # noqa: D102 or # noqa: D103 on the function definition line
        lines = content.split("\n")
        if node.lineno <= len(lines):
            func_line = lines[node.lineno - 1]
            if re.search(r"#\s*noqa:\s*D10[23]", func_line):
                return None

        # Phase 5.5 policy: Do NOT skip private/internal functions automatically
        # All functions must have documentation unless explicitly exempted via pragma

        docstring = ast.get_docstring(node)

        if not docstring:
            return ValidationError(
                str(file_path),
                ["function docstring"],
                "Function must have a docstring",
                symbol_name=f"def {node.name}()",
                line_number=node.lineno,
            )

        # Check for required sections (:param and :returns in reST/Sphinx style)
        # Accept :param, :type, :returns, :rtype per PEP 287
        has_param = bool(re.search(r":param\s+\w+:", docstring, re.MULTILINE))
        has_returns = bool(re.search(r":(returns?|rtype):", docstring, re.MULTILINE))

        missing = []

        # Only require :param if function has parameters (excluding self/cls)
        params = [arg.arg for arg in node.args.args if arg.arg not in ("self", "cls")]
        # Include *args
        if node.args.vararg is not None:
            params.append(node.args.vararg.arg)
        # Include keyword-only args
        if getattr(node.args, "kwonlyargs", None):
            params.extend(arg.arg for arg in node.args.kwonlyargs)
        # Include **kwargs
        if node.args.kwarg is not None:
            params.append(node.args.kwarg.arg)

        if params and not has_param:
            missing.append(":param")

        # Only require :returns if function has a return statement with a value
        # Check only direct body, exclude nested function definitions completely
        if not has_returns:
            has_return_value = False

            def has_return_in_node(node_to_check):
                """Recursively check if node has return with value, excluding nested functions.

                :param node_to_check: AST node to check
                :returns: True if node contains a return statement with a value, False otherwise
                """
                for child in ast.iter_child_nodes(node_to_check):
                    # Skip nested function/class definitions entirely
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        continue
                    # Check if this node is a Return with a value
                    if isinstance(child, ast.Return) and child.value is not None:
                        return True
                    # Recursively check children (but nested functions are already skipped)
                    if has_return_in_node(child):
                        return True
                return False

            has_return_value = has_return_in_node(node)

            if has_return_value:
                missing.append(":returns")

        if missing:
            return ValidationError(
                str(file_path),
                missing,
                f"Function docstring must include {', '.join(missing)} field(s) per PEP 287 reST style",
                symbol_name=f"def {node.name}()",
                line_number=node.lineno,
            )

        return None

    @staticmethod
    def _validate_class(file_path: Path, node: ast.ClassDef, content: str) -> ValidationError | None:
        """Validate a class docstring.

        :param file_path: Path to Python file
        :param node: AST ClassDef node
        :param content: File content (for pragma checking)
        :returns: ValidationError if class lacks proper documentation, None otherwise
        """
        # Check for pragma ignore
        lines = content.split("\n")
        if node.lineno <= len(lines):
            class_line = lines[node.lineno - 1]
            if re.search(r"#\s*noqa:\s*D101", class_line):
                return None

        # Phase 5.5 policy: Do NOT skip private classes automatically
        # All classes must have documentation unless explicitly exempted via pragma

        docstring = ast.get_docstring(node)

        if not docstring:
            return ValidationError(
                str(file_path),
                ["class docstring"],
                "Class must have docstring describing purpose and attributes",
                symbol_name=f"class {node.name}",
                line_number=node.lineno,
            )

        # Allow concise one-line docstrings for simple classes
        # No need to enforce minimum line count or :ivar requirements
        # A clear description is sufficient

        return None
