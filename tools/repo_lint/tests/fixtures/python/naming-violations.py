"""
Intentional naming convention violations for Python.

This file intentionally violates Python PEP 8 naming conventions.
It uses kebab-case instead of snake_case to test naming enforcement.
"""

from __future__ import annotations

# This file name itself (naming-violations.py) violates snake_case
# Expected: naming_violations.py
# Actual: naming-violations.py (kebab-case - WRONG for Python)


def ThisFunctionShouldBeSnakeCase():
    """Function names should be snake_case, not PascalCase."""
    pass


class lowercase_class:
    """Class names should be PascalCase, not snake_case."""

    pass


CONSTANT_value = 42  # Constants should be ALL_CAPS


def normal_function():
    """This is correct snake_case naming."""
    pass
