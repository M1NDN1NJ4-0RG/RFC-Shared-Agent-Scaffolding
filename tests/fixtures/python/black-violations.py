"""Test fixture for black formatter violations.

This file intentionally contains formatting violations to test black detection.
"""

# Black violation: line too long
x = "this is a very long string that exceeds the maximum line length configured for black and should trigger a violation"

# Black violation: inconsistent quotes
y = "single quotes when double are preferred"

# Black violation: missing whitespace around operators
z = 1 + 2 + 3 + 4 + 5

# Black violation: trailing comma missing in multiline structure
data = {"key1": "value1", "key2": "value2", "key3": "value3"}


# Black violation: improper spacing
def badly_formatted(a, b, c):
    return a + b + c


# Black violation: multiple statements on one line
if True:
    x = 1
    y = 2


# Black violation: inconsistent indentation style
class BadClass:
    def method1(self):
        pass

    def method2(self):
        pass


# Black violation: extra blank lines
def function_with_extra_blanks():

    pass


# Black violation: no space after comma
list_items = [1, 2, 3, 4, 5]

# Black violation: dictionary formatting
bad_dict = {"a": 1, "b": 2, "c": 3}

# Black violation: function call formatting
result = function_call(arg1, arg2, arg3)
