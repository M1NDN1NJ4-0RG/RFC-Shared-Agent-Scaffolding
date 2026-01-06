# fmt: skip-file
# pylint: skip-file
"""Module with Ruff violations.

This module intentionally contains Ruff rule violations.
"""


# Violation 1: F401 - Unused import
import json
import random


# Violation 2: F841 - Local variable assigned but never used
def test_unused_var():
    """Function with unused variable."""
    x = 42
    y = 100
    return 0


# Violation 3: E501 - Line too long (if Ruff is configured to check this)
def function_with_extremely_long_line_that_exceeds_the_maximum_line_length_limit_set_by_ruff_configuration():
    """Function name that is way too long."""
    pass


# Violation 4: F811 - Redefinition of unused name
def duplicate_function():
    """First definition."""
    pass


def duplicate_function():  # noqa: F811 is NOT present, so Ruff should flag this
    """Second definition - redefinition."""
    pass


# Violation 5: B006 - Mutable default argument
def bad_default(items=[]):
    """Function with mutable default argument."""
    items.append(1)
    return items
