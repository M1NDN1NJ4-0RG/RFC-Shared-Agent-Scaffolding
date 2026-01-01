# Missing module docstring

# Missing function docstring
def no_doc():
    pass

# Missing parameter documentation
def missing_params(x, y):
    """Function summary only."""
    return x + y

# Missing return documentation
def missing_return():
    """Function summary only."""
    return 42

# Missing raises documentation
def missing_raises():
    """Function summary only."""
    raise ValueError("error")

# Class without docstring
class NoDoc:
    def method(self):
        pass

# Class with missing method docstrings
class PartialDocs:
    """Class has docstring."""
    
    def no_doc_method(self):
        pass
    
    def another_no_doc(self):
        return 1

# Incomplete docstring - missing sections
def incomplete(x, y):
    """Just a summary line."""
    if x < 0:
        raise ValueError("negative")
    return x + y

# Wrong docstring format
def wrong_format(a, b, c):
    '''
    This uses single quotes instead of triple double quotes
    '''
    return a + b + c

# Missing docstring for class method
class MethodMissing:
    """Class docstring present."""
    
    def __init__(self):
        pass
    
    def compute(self, x):
        return x * 2

# Property without docstring
class PropertyMissing:
    """Class docstring present."""
    
    @property
    def value(self):
        return 42

# Static method without docstring
class StaticMissing:
    """Class docstring present."""
    
    @staticmethod
    def helper():
        return "help"

# Class method without docstring
class ClassMethodMissing:
    """Class docstring present."""
    
    @classmethod
    def create(cls):
        return cls()

# Nested function without docstring
def outer():
    """Outer function."""
    def inner():
        return 1
    return inner()

# Lambda (no docstring possible, but included for completeness)
calc = lambda x: x * 2

# Missing Examples section
def no_examples():
    """Function summary.
    
    :param x: some param
    :returns: some value
    """
    pass

# Missing Notes section when complexity warrants it
def complex_algorithm(data):
    """Perform complex operation."""
    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)
    return result
