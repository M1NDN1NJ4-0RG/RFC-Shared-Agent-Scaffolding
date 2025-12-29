"""Python test fixtures for repo_lint docstring validation.

Purpose: Test missing docstrings, correct docstrings, pragma exemptions,
and edge cases for Python symbol discovery and validation.
"""


def missing_docstring():
    """This function has a docstring (should pass)."""
    return "ok"


def no_doc():
    return "missing docstring"


class MissingClassDoc:
    def method_with_doc(self):
        """Method has documentation."""
        pass

    def method_without_doc(self):
        pass


class ProperlyDocumented:
    """Class with proper documentation.

    :Purpose:
        Demonstrates a properly documented class with all required sections.
    """

    def __init__(self):
        """Initialize the class.

        :Purpose:
            Constructor documentation.
        """
        pass

    def public_method(self):
        """Public method with documentation.

        :Purpose:
            Demonstrates proper method documentation.
        """
        pass


# noqa: FUNCTION
def exempted_function():
    return "pragma exemption"


def multiline_signature(
    arg1,
    arg2,
    arg3="default",
):
    """Function with multiline signature.

    :Purpose:
        Test multiline parameter lists.
    """
    return arg1 + arg2 + arg3
