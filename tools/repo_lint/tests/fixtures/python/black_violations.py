"""Test fixture for black formatter violations.

This file intentionally contains formatting violations to test black detection.
"""
from __future__ import annotations

# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
# Black violation: line too long
x = "this is a very long string that exceeds the maximum line length configured for black and should trigger a violation"

# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
# Black violation: inconsistent quotes
y = "single quotes when double are preferred"

# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
# Black violation: missing whitespace around operators
z = 1 + 2 + 3 + 4 + 5

# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
# Black violation: trailing comma missing in multiline structure
data = {"key1": "value1", "key2": "value2", "key3": "value3"}


# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
# Black violation: improper spacing
# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
def badly_formatted(a, b, c):
    return a + b + c


# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
# Black violation: multiple statements on one line
if True:
    x = 1
    y = 2


# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
# Black violation: inconsistent indentation style
# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
class BadClass:
    # INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
    def method1(self):
        pass

    # INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
    def method2(self):
        pass


# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
# Black violation: extra blank lines
# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
def function_with_extra_blanks():

    pass


# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
# Black violation: no space after comma
list_items = [1, 2, 3, 4, 5]

# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
# Black violation: dictionary formatting
bad_dict = {"a": 1, "b": 2, "c": 3}

# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
# Black violation: function call formatting
result = function_call(arg1, arg2, arg3)
