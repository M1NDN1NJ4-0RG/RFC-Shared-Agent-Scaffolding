"""Test fixture for pylint violations.

This file intentionally contains violations to test pylint detection.
"""

# C0103: invalid variable name (should be lowercase_with_underscores)
InvalidVariableName = "bad"


# C0111: missing docstring
def no_docstring():
    pass


# R0913: too many arguments
def too_many_args(a, b, c, d, e, f, g):
    return a + b + c + d + e + f + g


# R0914: too many local variables
def too_many_locals():
    var1 = 1
    var2 = 2
    var3 = 3
    var4 = 4
    var5 = 5
    var6 = 6
    var7 = 7
    var8 = 8
    var9 = 9
    var10 = 10
    var11 = 11
    var12 = 12
    var13 = 13
    var14 = 14
    var15 = 15
    var16 = 16
    return var1 + var2 + var3 + var4 + var5 + var6 + var7 + var8 + var9 + var10


# W0612: unused variable
def unused_var():
    """Function with unused variable."""
    x = 10
    y = 20
    return 5


# W0613: unused argument
def unused_arg(x, y, z):
    """Function with unused arguments."""
    return x


# R0915: too many statements
def too_many_statements():
    """Function with too many statements."""
    x = 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    x = x + 1
    return x


# C0200: consider using enumerate
items = [1, 2, 3]
for i in range(len(items)):
    print(items[i])

# W0631: undefined loop variable
for item in items:
    break
print(item)


# R1705: unnecessary else after return
def unnecessary_else(x):
    """Function with unnecessary else."""
    if x > 0:
        return "positive"
    else:
        return "non-positive"


# W0621: redefining name from outer scope
def outer():
    """Outer function."""
    x = 1

    def inner():
        """Inner function."""
        x = 2  # W0621
        return x

    return inner()


# C0413: import should be at top
def function():
    """Function with import inside."""
    pass




# W0107: unnecessary pass
def empty_function():
    """Empty function."""
    pass
    pass


# C0325: unnecessary parens
if True:
    pass


# W0104: statement seems to have no effect
def no_effect():
    """Function with no-effect statement."""
    x = 10
    x + 5  # W0104
    return x
