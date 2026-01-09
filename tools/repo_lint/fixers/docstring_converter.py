#!/usr/bin/env python3
"""Bidirectional Python docstring style converter.

Converts between multiple docstring styles (Google, NumPy, reST, EpyDoc, etc.)
using a Parse → IR → Render architecture for reliability and extensibility.

Architecture:
    1. Parse: Style-specific parser → DocstringIR
    2. IR: Intermediate representation (style-agnostic)
    3. Render: IR → Style-specific output

Supported styles:
    - Google
    - NumPy  
    - reST/Sphinx
    - EpyDoc
    - Plain

Usage:
    python3 docstring_converter.py <input_files> --from-style google --to-style rest [--dry-run]
"""

import ast
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class DocstringStyle(Enum):
    """Supported docstring styles."""

    GOOGLE = "google"
    NUMPY = "numpy"
    REST = "rest"
    EPYDOC = "epydoc"
    PLAIN = "plain"
    UNKNOWN = "unknown"


@dataclass
class Param:
    """Parameter documentation."""

    name: str
    type_hint: Optional[str] = None
    default: Optional[str] = None
    description: Optional[str] = None
    kind: str = "positional"  # positional, kwonly, varargs, varkw


@dataclass
class Return:
    """Return value documentation."""

    type_hint: Optional[str] = None
    description: Optional[str] = None


@dataclass
class Raise:
    """Exception documentation."""

    exc_type: str
    description: Optional[str] = None


@dataclass
class Example:
    """Example block."""

    text: str
    verbatim: bool = True


@dataclass
class Section:
    """Generic section (Notes, Warnings, See Also, etc.)."""

    title: str
    content: str


@dataclass
class DocstringIR:
    """Intermediate representation of a docstring.
    
    Style-agnostic representation that captures docstring intent.
    Can be rendered to any supported style.
    """

    summary: str = ""
    extended: Optional[str] = None
    params: list[Param] = field(default_factory=list)
    returns: Optional[Return] = None
    yields: Optional[Return] = None
    raises: list[Raise] = field(default_factory=list)
    examples: list[Example] = field(default_factory=list)
    sections: list[Section] = field(default_factory=list)
    
    # Metadata
    detected_style: DocstringStyle = DocstringStyle.UNKNOWN
    confidence: float = 0.0
    raw_blocks: dict[str, Any] = field(default_factory=dict)


class DocstringParser:
    """Base class for style-specific parsers."""

    def parse(self, docstring: str) -> DocstringIR:
        """Parse a docstring into IR.
        
        :param docstring: Raw docstring text
        :rtype: DocstringIR
        """
        raise NotImplementedError("Subclasses must implement parse()")


class GoogleParser(DocstringParser):
    """Parser for Google-style docstrings."""

    def parse(self, docstring: str) -> DocstringIR:
        """Parse Google-style docstring.
        
        :param docstring: Raw docstring text
        :rtype: DocstringIR
        """
        ir = DocstringIR(detected_style=DocstringStyle.GOOGLE, confidence=0.8)
        
        lines = docstring.split("\n")
        if not lines:
            return ir
        
        # Simple implementation: extract summary (first non-empty line)
        for line in lines:
            stripped = line.strip()
            if stripped:
                ir.summary = stripped
                break
        
        # TODO: Parse Args, Returns, Raises sections
        # This is a minimal skeleton - full implementation required
        
        return ir


class NumPyParser(DocstringParser):
    """Parser for NumPy-style docstrings."""

    def parse(self, docstring: str) -> DocstringIR:
        """Parse NumPy-style docstring.
        
        :param docstring: Raw docstring text
        :rtype: DocstringIR
        """
        ir = DocstringIR(detected_style=DocstringStyle.NUMPY, confidence=0.8)
        
        lines = docstring.split("\n")
        if not lines:
            return ir
        
        # Extract summary
        for line in lines:
            stripped = line.strip()
            if stripped:
                ir.summary = stripped
                break
        
        # TODO: Parse Parameters, Returns, Raises sections
        
        return ir


class ReSTParser(DocstringParser):
    """Parser for reST/Sphinx-style docstrings."""

    def parse(self, docstring: str) -> DocstringIR:
        """Parse reST-style docstring.
        
        :param docstring: Raw docstring text
        :rtype: DocstringIR
        """
        ir = DocstringIR(detected_style=DocstringStyle.REST, confidence=0.9)
        
        lines = docstring.split("\n")
        if not lines:
            return ir
        
        # Extract summary
        summary_lines = []
        in_summary = True
        
        for line in lines:
            stripped = line.strip()
            
            # Stop at first field marker
            if stripped.startswith(":"):
                in_summary = False
                # Parse field
                # TODO: Full field parsing
                continue
            
            if in_summary and stripped:
                summary_lines.append(stripped)
            elif in_summary and not stripped and summary_lines:
                # End of summary
                in_summary = False
        
        ir.summary = " ".join(summary_lines)
        
        return ir


class DocstringRenderer:
    """Base class for style-specific renderers."""

    def render(self, ir: DocstringIR) -> str:
        """Render IR to docstring text.
        
        :param ir: Docstring intermediate representation
        :rtype: str
        """
        raise NotImplementedError("Subclasses must implement render()")


class GoogleRenderer(DocstringRenderer):
    """Renderer for Google-style docstrings."""

    def render(self, ir: DocstringIR) -> str:
        """Render IR to Google-style docstring.
        
        :param ir: Docstring intermediate representation
        :rtype: str
        """
        lines = []
        
        # Summary
        if ir.summary:
            lines.append(ir.summary)
            lines.append("")
        
        # Extended description
        if ir.extended:
            lines.append(ir.extended)
            lines.append("")
        
        # Args
        if ir.params:
            lines.append("Args:")
            for param in ir.params:
                if param.type_hint:
                    lines.append(f"    {param.name} ({param.type_hint}): {param.description or ''}")
                else:
                    lines.append(f"    {param.name}: {param.description or ''}")
            lines.append("")
        
        # Returns
        if ir.returns:
            lines.append("Returns:")
            if ir.returns.type_hint:
                lines.append(f"    {ir.returns.type_hint}: {ir.returns.description or ''}")
            else:
                lines.append(f"    {ir.returns.description or ''}")
            lines.append("")
        
        # Raises
        if ir.raises:
            lines.append("Raises:")
            for raise_item in ir.raises:
                lines.append(f"    {raise_item.exc_type}: {raise_item.description or ''}")
            lines.append("")
        
        return "\n".join(lines).rstrip()


class NumPyRenderer(DocstringRenderer):
    """Renderer for NumPy-style docstrings."""

    def render(self, ir: DocstringIR) -> str:
        """Render IR to NumPy-style docstring.
        
        :param ir: Docstring intermediate representation
        :rtype: str
        """
        lines = []
        
        # Summary
        if ir.summary:
            lines.append(ir.summary)
            lines.append("")
        
        # Extended description
        if ir.extended:
            lines.append(ir.extended)
            lines.append("")
        
        # Parameters
        if ir.params:
            lines.append("Parameters")
            lines.append("----------")
            for param in ir.params:
                if param.type_hint:
                    lines.append(f"{param.name} : {param.type_hint}")
                else:
                    lines.append(param.name)
                if param.description:
                    lines.append(f"    {param.description}")
            lines.append("")
        
        # Returns
        if ir.returns:
            lines.append("Returns")
            lines.append("-------")
            if ir.returns.type_hint:
                lines.append(ir.returns.type_hint)
            if ir.returns.description:
                lines.append(f"    {ir.returns.description}")
            lines.append("")
        
        # Raises
        if ir.raises:
            lines.append("Raises")
            lines.append("------")
            for raise_item in ir.raises:
                lines.append(raise_item.exc_type)
                if raise_item.description:
                    lines.append(f"    {raise_item.description}")
            lines.append("")
        
        return "\n".join(lines).rstrip()


class ReSTRenderer(DocstringRenderer):
    """Renderer for reST/Sphinx-style docstrings."""

    def render(self, ir: DocstringIR) -> str:
        """Render IR to reST-style docstring.
        
        :param ir: Docstring intermediate representation
        :rtype: str
        """
        lines = []
        
        # Summary
        if ir.summary:
            lines.append(ir.summary)
            lines.append("")
        
        # Extended description
        if ir.extended:
            lines.append(ir.extended)
            lines.append("")
        
        # Parameters
        for param in ir.params:
            if param.type_hint:
                lines.append(f":param {param.type_hint} {param.name}: {param.description or ''}")
            else:
                lines.append(f":param {param.name}: {param.description or ''}")
        
        # Returns
        if ir.returns:
            if ir.returns.type_hint:
                lines.append(f":returns: {ir.returns.description or ''}")
                lines.append(f":rtype: {ir.returns.type_hint}")
            else:
                lines.append(f":returns: {ir.returns.description or ''}")
        
        # Raises
        for raise_item in ir.raises:
            lines.append(f":raises {raise_item.exc_type}: {raise_item.description or ''}")
        
        return "\n".join(lines).rstrip()


class DocstringConverter:
    """Main converter class."""

    def __init__(self) -> None:
        """Initialize converter with parsers and renderers.
        
        :rtype: None
        """
        self.parsers: dict[DocstringStyle, DocstringParser] = {
            DocstringStyle.GOOGLE: GoogleParser(),
            DocstringStyle.NUMPY: NumPyParser(),
            DocstringStyle.REST: ReSTParser(),
        }
        
        self.renderers: dict[DocstringStyle, DocstringRenderer] = {
            DocstringStyle.GOOGLE: GoogleRenderer(),
            DocstringStyle.NUMPY: NumPyRenderer(),
            DocstringStyle.REST: ReSTRenderer(),
        }
    
    def convert(
        self,
        docstring: str,
        from_style: DocstringStyle,
        to_style: DocstringStyle,
    ) -> str:
        """Convert docstring from one style to another.
        
        :param docstring: Input docstring text
        :param from_style: Source style
        :param to_style: Target style
        :rtype: str
        """
        # Parse
        parser = self.parsers.get(from_style)
        if not parser:
            raise ValueError(f"Unsupported source style: {from_style}")
        
        ir = parser.parse(docstring)
        
        # Render
        renderer = self.renderers.get(to_style)
        if not renderer:
            raise ValueError(f"Unsupported target style: {to_style}")
        
        return renderer.render(ir)
    
    def convert_file(
        self,
        filepath: Path,
        from_style: DocstringStyle,
        to_style: DocstringStyle,
        dry_run: bool = False,
    ) -> int:
        """Convert all docstrings in a Python file.
        
        :param filepath: Path to Python file
        :param from_style: Source style
        :param to_style: Target style
        :param dry_run: If True, don't modify file
        :rtype: int
        """
        # Read file
        try:
            source = filepath.read_text()
        except (UnicodeDecodeError, OSError, IOError) as e:
            print(f"Error reading {filepath}: {e}", file=sys.stderr)
            return 0
        
        # Parse AST
        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            print(f"Syntax error in {filepath}: {e}", file=sys.stderr)
            return 0
        
        # TODO: Walk AST, find functions/classes with docstrings, convert them
        # This requires careful line-based modification like rtype_fixer.py
        
        # For now, skeleton implementation
        return 0


def main() -> int:
    """CLI entry point.
    
    :rtype: int
    """
    if len(sys.argv) < 2:
        print("Usage: docstring_converter.py <files> --from-style <style> --to-style <style> [--dry-run]")
        print("Styles: google, numpy, rest")
        return 1
    
    # Basic arg parsing
    files = []
    from_style_str = "google"
    to_style_str = "rest"
    dry_run = False
    
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--from-style":
            from_style_str = sys.argv[i + 1]
            i += 2
        elif arg == "--to-style":
            to_style_str = sys.argv[i + 1]
            i += 2
        elif arg == "--dry-run":
            dry_run = True
            i += 1
        else:
            files.append(arg)
            i += 1
    
    # Parse styles
    try:
        from_style = DocstringStyle(from_style_str)
        to_style = DocstringStyle(to_style_str)
    except ValueError as e:
        print(f"Invalid style: {e}", file=sys.stderr)
        return 1
    
    converter = DocstringConverter()
    
    total_converted = 0
    for filepath_str in files:
        filepath = Path(filepath_str)
        if not filepath.exists():
            print(f"File not found: {filepath}", file=sys.stderr)
            continue
        
        converted = converter.convert_file(filepath, from_style, to_style, dry_run)
        total_converted += converted
    
    print(f"Converted {total_converted} docstrings")
    return 0


if __name__ == "__main__":
    sys.exit(main())
