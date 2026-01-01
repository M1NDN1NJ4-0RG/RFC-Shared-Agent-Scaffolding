"""Test fixture for ruff linter violations.

This file intentionally contains violations to test ruff detection.
"""

import os
import sys
import json  # F401: imported but unused
from typing import List, Dict  # F401: imported but unused
import subprocess  # F401: imported but unused

# F841: local variable assigned but never used
unused_variable = "this is never used"

# E501: line too long (if configured)
very_long_string = "this is an extremely long string that might exceed the configured line length limit for ruff and should trigger an E501 violation if that rule is enabled"

# F541: f-string without placeholders
message = f"This f-string has no placeholders"

# E711: comparison to None should be 'is' or 'is not'
x = None
if x == None:
    pass

# E712: comparison to True/False should be 'is' or 'is not'
flag = True
if flag == True:
    pass

# F821: undefined name
result = undefined_variable + 10


# E402: module level import not at top of file
def some_function():
    pass


import random  # E402

# F541: f-string without any placeholders
text = f"just a string"


# B006: mutable default argument
def bad_default(items=[]):
    items.append(1)
    return items


# B008: function call in argument defaults
import datetime


def bad_time(when=datetime.datetime.now()):
    return when


# C901: function is too complex (McCabe complexity)
def overly_complex_function(a, b, c):
    if a:
        if b:
            if c:
                if a > 5:
                    if b > 10:
                        if c > 15:
                            return "nested"
    return "default"


# E731: do not assign lambda
calc = lambda x: x * 2

# F523: '.format' call has unused arguments
text = "hello {0}".format("world", "extra")

# E741: ambiguous variable name
l = 1  # noqa: E741 would suppress
O = 2
I = 3

# B007: loop variable not used within loop body
for i in range(10):
    print("not using i")

# UP: outdated typing syntax
from typing import Optional


def old_style(x: Optional[str]) -> Optional[int]:
    pass


# RUF: ruff-specific rules
class MyClass:  # RUF012: mutable class attributes should use typing.ClassVar
    default_list = []
