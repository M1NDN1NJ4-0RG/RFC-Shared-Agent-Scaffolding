#!/usr/bin/env python3
"""Tests for docstring_converter.py."""

import unittest
from pathlib import Path

# Add parent directory to path for imports
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from fixers.docstring_converter import (
    DocstringConverter,
    DocstringStyle,
    GoogleParser,
    NumPyParser,
    ReSTParser,
    GoogleRenderer,
    NumPyRenderer,
    ReSTRenderer,
    DocstringIR,
    Param,
    Return,
)


class TestGoogleParser(unittest.TestCase):
    """Test Google-style docstring parser."""

    def test_parse_simple_summary(self) -> None:
        """Test parsing a simple summary."""
        docstring = "This is a simple function."
        parser = GoogleParser()
        ir = parser.parse(docstring)

        self.assertEqual(ir.summary, "This is a simple function.")
        self.assertEqual(ir.detected_style, DocstringStyle.GOOGLE)

    def test_parse_with_args(self) -> None:
        """Test parsing with Args section."""
        docstring = """Calculate the sum of two numbers.
        
        Args:
            a (int): First number
            b (int): Second number
        """
        parser = GoogleParser()
        ir = parser.parse(docstring)

        self.assertEqual(ir.summary, "Calculate the sum of two numbers.")
        self.assertEqual(len(ir.params), 2)
        self.assertEqual(ir.params[0].name, "a")
        self.assertEqual(ir.params[0].type_hint, "int")
        self.assertEqual(ir.params[0].description, "First number")
        self.assertEqual(ir.params[1].name, "b")
        self.assertEqual(ir.params[1].type_hint, "int")

    def test_parse_with_returns(self) -> None:
        """Test parsing with Returns section."""
        docstring = """Get user name.
        
        Returns:
            str: The user's name
        """
        parser = GoogleParser()
        ir = parser.parse(docstring)

        self.assertEqual(ir.summary, "Get user name.")
        self.assertIsNotNone(ir.returns)
        self.assertEqual(ir.returns.type_hint, "str")
        self.assertEqual(ir.returns.description, "The user's name")

    def test_parse_with_raises(self) -> None:
        """Test parsing with Raises section."""
        docstring = """Open a file.
        
        Raises:
            FileNotFoundError: If file doesn't exist
            PermissionError: If no read permission
        """
        parser = GoogleParser()
        ir = parser.parse(docstring)

        self.assertEqual(len(ir.raises), 2)
        self.assertEqual(ir.raises[0].exc_type, "FileNotFoundError")
        self.assertEqual(ir.raises[0].description, "If file doesn't exist")
        self.assertEqual(ir.raises[1].exc_type, "PermissionError")


class TestNumPyParser(unittest.TestCase):
    """Test NumPy-style docstring parser."""

    def test_parse_simple_summary(self) -> None:
        """Test parsing a simple summary."""
        docstring = "This is a NumPy-style docstring."
        parser = NumPyParser()
        ir = parser.parse(docstring)

        self.assertEqual(ir.summary, "This is a NumPy-style docstring.")
        self.assertEqual(ir.detected_style, DocstringStyle.NUMPY)

    def test_parse_with_parameters(self) -> None:
        """Test parsing with Parameters section."""
        docstring = """Calculate sum.

Parameters
----------
x : int
    First value
y : int
    Second value
"""
        parser = NumPyParser()
        ir = parser.parse(docstring)

        self.assertEqual(ir.summary, "Calculate sum.")
        self.assertEqual(len(ir.params), 2)
        self.assertEqual(ir.params[0].name, "x")
        self.assertEqual(ir.params[0].type_hint, "int")
        self.assertEqual(ir.params[0].description, "First value")

    def test_parse_with_returns(self) -> None:
        """Test parsing with Returns section."""
        docstring = """Get value.

Returns
-------
int
    The computed value
"""
        parser = NumPyParser()
        ir = parser.parse(docstring)

        self.assertIsNotNone(ir.returns)
        self.assertEqual(ir.returns.type_hint, "int")
        self.assertEqual(ir.returns.description, "The computed value")

    def test_parse_with_raises(self) -> None:
        """Test parsing with Raises section."""
        docstring = """Process data.

Raises
------
ValueError
    If input is invalid
RuntimeError
    If processing fails
"""
        parser = NumPyParser()
        ir = parser.parse(docstring)

        self.assertEqual(len(ir.raises), 2)
        self.assertEqual(ir.raises[0].exc_type, "ValueError")
        self.assertEqual(ir.raises[0].description, "If input is invalid")


class TestReSTParser(unittest.TestCase):
    """Test reST/Sphinx-style docstring parser."""

    def test_parse_simple_summary(self) -> None:
        """Test parsing a simple summary."""
        docstring = "This is a reST docstring."
        parser = ReSTParser()
        ir = parser.parse(docstring)

        self.assertEqual(ir.summary, "This is a reST docstring.")
        self.assertEqual(ir.detected_style, DocstringStyle.REST)

    def test_parse_with_params(self) -> None:
        """Test parsing with :param: fields."""
        docstring = """Calculate sum.
        
        :param int x: First number
        :param int y: Second number
        """
        parser = ReSTParser()
        ir = parser.parse(docstring)

        self.assertEqual(ir.summary, "Calculate sum.")
        self.assertEqual(len(ir.params), 2)
        self.assertEqual(ir.params[0].name, "x")
        self.assertEqual(ir.params[0].type_hint, "int")
        self.assertEqual(ir.params[0].description, "First number")

    def test_parse_with_returns_and_rtype(self) -> None:
        """Test parsing with :returns: and :rtype: fields."""
        docstring = """Get value.
        
        :returns: The computed result
        :rtype: int
        """
        parser = ReSTParser()
        ir = parser.parse(docstring)

        self.assertIsNotNone(ir.returns)
        self.assertEqual(ir.returns.description, "The computed result")
        self.assertEqual(ir.returns.type_hint, "int")

    def test_parse_with_raises(self) -> None:
        """Test parsing with :raises: fields."""
        docstring = """Process file.
        
        :raises FileNotFoundError: If file missing
        :raises IOError: If read fails
        """
        parser = ReSTParser()
        ir = parser.parse(docstring)

        self.assertEqual(len(ir.raises), 2)
        self.assertEqual(ir.raises[0].exc_type, "FileNotFoundError")
        self.assertEqual(ir.raises[0].description, "If file missing")


class TestGoogleRenderer(unittest.TestCase):
    """Test Google-style docstring renderer."""

    def test_render_simple(self) -> None:
        """Test rendering a simple docstring."""
        ir = DocstringIR(summary="Simple function")
        renderer = GoogleRenderer()
        result = renderer.render(ir)

        self.assertEqual(result, "Simple function")

    def test_render_with_args(self) -> None:
        """Test rendering with arguments."""
        ir = DocstringIR(
            summary="Calculate sum",
            params=[
                Param(name="x", type_hint="int", description="First value"),
                Param(name="y", type_hint="int", description="Second value"),
            ],
        )
        renderer = GoogleRenderer()
        result = renderer.render(ir)

        self.assertIn("Args:", result)
        self.assertIn("x (int): First value", result)
        self.assertIn("y (int): Second value", result)

    def test_render_with_returns(self) -> None:
        """Test rendering with return value."""
        ir = DocstringIR(summary="Get value", returns=Return(type_hint="str", description="The result"))
        renderer = GoogleRenderer()
        result = renderer.render(ir)

        self.assertIn("Returns:", result)
        self.assertIn("str: The result", result)


class TestNumPyRenderer(unittest.TestCase):
    """Test NumPy-style docstring renderer."""

    def test_render_simple(self) -> None:
        """Test rendering a simple docstring."""
        ir = DocstringIR(summary="Simple function")
        renderer = NumPyRenderer()
        result = renderer.render(ir)

        self.assertEqual(result, "Simple function")

    def test_render_with_params(self) -> None:
        """Test rendering with parameters."""
        ir = DocstringIR(
            summary="Process data",
            params=[
                Param(name="data", type_hint="list", description="Input data"),
            ],
        )
        renderer = NumPyRenderer()
        result = renderer.render(ir)

        self.assertIn("Parameters", result)
        self.assertIn("----------", result)
        self.assertIn("data : list", result)
        self.assertIn("Input data", result)

    def test_render_with_returns(self) -> None:
        """Test rendering with return value."""
        ir = DocstringIR(summary="Compute", returns=Return(type_hint="int", description="Result value"))
        renderer = NumPyRenderer()
        result = renderer.render(ir)

        self.assertIn("Returns", result)
        self.assertIn("-------", result)
        self.assertIn("int", result)
        self.assertIn("Result value", result)


class TestReSTRenderer(unittest.TestCase):
    """Test reST/Sphinx-style docstring renderer."""

    def test_render_simple(self) -> None:
        """Test rendering a simple docstring."""
        ir = DocstringIR(summary="Simple function")
        renderer = ReSTRenderer()
        result = renderer.render(ir)

        self.assertEqual(result, "Simple function")

    def test_render_with_params(self) -> None:
        """Test rendering with parameters."""
        ir = DocstringIR(
            summary="Process",
            params=[
                Param(name="value", type_hint="str", description="Input value"),
            ],
        )
        renderer = ReSTRenderer()
        result = renderer.render(ir)

        self.assertIn(":param str value: Input value", result)

    def test_render_with_returns(self) -> None:
        """Test rendering with return value."""
        ir = DocstringIR(summary="Get data", returns=Return(type_hint="dict", description="Result dict"))
        renderer = ReSTRenderer()
        result = renderer.render(ir)

        self.assertIn(":returns: Result dict", result)
        self.assertIn(":rtype: dict", result)


class TestDocstringConverter(unittest.TestCase):
    """Test end-to-end conversion."""

    def test_convert_google_to_rest(self) -> None:
        """Test converting Google to reST style."""
        google_doc = """Calculate sum of two numbers.
        
        Args:
            a (int): First number
            b (int): Second number
        
        Returns:
            int: The sum
        """

        converter = DocstringConverter()
        result = converter.convert(google_doc, DocstringStyle.GOOGLE, DocstringStyle.REST)

        self.assertIn(":param int a: First number", result)
        self.assertIn(":param int b: Second number", result)
        self.assertIn(":returns:", result)
        self.assertIn(":rtype: int", result)

    def test_convert_numpy_to_google(self) -> None:
        """Test converting NumPy to Google style."""
        numpy_doc = """Process data.

Parameters
----------
data : list
    Input data list

Returns
-------
int
    Count of items
"""

        converter = DocstringConverter()
        result = converter.convert(numpy_doc, DocstringStyle.NUMPY, DocstringStyle.GOOGLE)

        self.assertIn("Args:", result)
        self.assertIn("data (list): Input data list", result)
        self.assertIn("Returns:", result)
        self.assertIn("int: Count of items", result)

    def test_convert_rest_to_numpy(self) -> None:
        """Test converting reST to NumPy style."""
        rest_doc = """Fetch resource.
        
        :param str url: Resource URL
        :returns: Resource content
        :rtype: str
        """

        converter = DocstringConverter()
        result = converter.convert(rest_doc, DocstringStyle.REST, DocstringStyle.NUMPY)

        self.assertIn("Parameters", result)
        self.assertIn("----------", result)
        self.assertIn("url : str", result)
        self.assertIn("Returns", result)
        self.assertIn("-------", result)


if __name__ == "__main__":
    unittest.main()
