"""Module with Black formatting violations.

This module intentionally contains code that violates Black formatting rules.
"""
# ruff: noqa
# pylint: skip-file


# Violation 1: Line too long
def function_with_very_long_line(parameter1, parameter2, parameter3, parameter4, parameter5, parameter6, parameter7, parameter8):
    """Function with very long parameter list."""
    return parameter1 + parameter2


# Violation 2: Inconsistent quotes
def mixed_quotes():
    """Function using inconsistent quote styles."""
    x = 'single quotes'
    y = "double quotes"
    return x + y


# Violation 3: Missing whitespace
def bad_spacing():
    """Function with bad spacing."""
    x=1+2+3
    y=[1,2,3,4,5]
    return x,y


# Violation 4: Wrong number of blank lines
class MyClass:
    """Test class."""
    def method1(self):
        """Method one."""
        pass
    def method2(self):
        """Method two."""
        pass
