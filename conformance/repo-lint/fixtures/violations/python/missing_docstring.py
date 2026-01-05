"""Test fixture: intentionally bad Python code with missing docstrings."""

from __future__ import annotations


def function_without_docstring(param1, param2):
    return param1 + param2


class ClassWithoutDocstring:
    def method_without_docstring(self):
        pass


# Unused import (Ruff F401 - not auto-fixable as it might be intentional)
import os  # noqa: F401 - Remove this noqa to trigger violation
import sys


# Line too long (Ruff E501 - not auto-fixable as Black won't break it)
VERY_LONG_STRING_THAT_EXCEEDS_THE_LINE_LENGTH_LIMIT_OF_ONE_HUNDRED_TWENTY_CHARACTERS_AND_CANNOT_BE_AUTO_FIXED_BY_BLACK = (
    "value"
)


def _private_function_with_docs(x):
    """Example of a private function that IS documented (not a violation)."""
    return x * 2
