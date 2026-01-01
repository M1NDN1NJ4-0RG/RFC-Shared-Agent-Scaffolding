# Missing module docstring


# Missing function docstring
# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
def no_doc():
    pass


# Missing parameter documentation
# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
def missing_params(x, y):
    """Function summary only."""
    return x + y


# Missing return documentation
# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
def missing_return():
    """Function summary only."""
    return 42


# Missing raises documentation
# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
def missing_raises():
    """Function summary only."""
    raise ValueError("error")


# Class without docstring
# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
class NoDoc:
# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
    def method(self):
        pass


# Class with missing method docstrings
# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
class PartialDocs:
    """Class has docstring."""

# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
    def no_doc_method(self):
        pass

# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
    def another_no_doc(self):
        return 1


# Incomplete docstring - missing sections
# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
def incomplete(x, y):
    """Just a summary line."""
    if x < 0:
        raise ValueError("negative")
    return x + y


# Wrong docstring format
# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
def wrong_format(a, b, c):
    """
    This uses single quotes instead of triple double quotes
    """
    return a + b + c


# Missing docstring for class method
# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
class MethodMissing:
    """Class docstring present."""

# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
    def __init__(self):
        pass

# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
    def compute(self, x):
        return x * 2


# Property without docstring
# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
class PropertyMissing:
    """Class docstring present."""

    @property
# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
    def value(self):
        return 42


# Static method without docstring
# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
class StaticMissing:
    """Class docstring present."""

    @staticmethod
# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
    def helper():
        return "help"


# Class method without docstring
# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
class ClassMethodMissing:
    """Class docstring present."""

    @classmethod
# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
    def create(cls):
        return cls()


# Nested function without docstring
# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
def outer():
    """Outer function."""

# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
    def inner():
        return 1

    return inner()


# Lambda (no docstring possible, but included for completeness)
calc = lambda x: x * 2


# Missing Examples section
# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
def no_examples():
    """Function summary.

    :param x: some param
    :returns: some value
    """
    pass


# Missing Notes section when complexity warrants it
# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
def complex_algorithm(data):
    """Perform complex operation."""
    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)
    return result
