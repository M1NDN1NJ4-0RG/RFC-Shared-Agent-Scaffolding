#!/usr/bin/env python3
"""Test script to trigger linting violations for workflow testing.

This file intentionally contains violations that Black cannot auto-fix.
"""

# Ruff violation: F401 - unused import
import os
import sys
import json

# Pylint violation: Line too long in a string that Black won't touch
VERY_LONG_STRING = "This is an extremely long string that exceeds the 120 character line length limit and Black cannot fix it because it's already a single string literal and there's no good place to break it"

# Ruff violation: E501 - line too long (comment)
# This is a very long comment that exceeds the 120 character line length limit and will trigger a Ruff violation because it's way too long


def test_function():
    """Function without proper docstring format (missing returns/params)."""
    x = 1
    y = 2
    return x + y
