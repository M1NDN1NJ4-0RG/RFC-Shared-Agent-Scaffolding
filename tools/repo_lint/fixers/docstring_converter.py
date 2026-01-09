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
import textwrap
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

    @staticmethod
    def _dedent(docstring: str) -> str:
        """Remove common leading whitespace from docstring.

        :param docstring: Raw docstring text
        :rtype: str
        """
        return textwrap.dedent(docstring)


class GoogleParser(DocstringParser):
    """Parser for Google-style docstrings."""

    def parse(self, docstring: str) -> DocstringIR:
        """Parse Google-style docstring.

        :param docstring: Raw docstring text
        :rtype: DocstringIR
        """
        ir = DocstringIR(detected_style=DocstringStyle.GOOGLE, confidence=0.8)

        # Dedent first
        docstring = self._dedent(docstring)
        lines = docstring.split("\n")
        if not lines:
            return ir

        # Parse sections
        current_section = "summary"
        summary_lines = []
        extended_lines = []
        current_indent = 0
        i = 0

        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # Detect section headers
            if stripped.endswith(":") and stripped[:-1] in [
                "Args",
                "Arguments",
                "Parameters",
                "Returns",
                "Return",
                "Yields",
                "Yield",
                "Raises",
                "Raise",
                "Example",
                "Examples",
                "Note",
                "Notes",
                "Warning",
                "Warnings",
                "See Also",
            ]:
                section_name = stripped[:-1].lower()
                current_section = section_name
                i += 1

                if section_name in ["args", "arguments", "parameters"]:
                    # Parse arguments
                    i = self._parse_args_section(lines, i, ir)
                elif section_name in ["returns", "return"]:
                    # Parse returns
                    i = self._parse_returns_section(lines, i, ir)
                elif section_name in ["raises", "raise"]:
                    # Parse raises
                    i = self._parse_raises_section(lines, i, ir)
                else:
                    # Generic section - skip for now
                    while i < len(lines) and (not lines[i].strip() or lines[i].startswith("    ")):
                        i += 1
                continue

            # Summary/extended description
            if current_section == "summary":
                if stripped:
                    summary_lines.append(stripped)
                elif summary_lines:
                    # Empty line after summary - rest is extended
                    current_section = "extended"
                i += 1
            elif current_section == "extended":
                if stripped:
                    extended_lines.append(stripped)
                i += 1
            else:
                i += 1

        ir.summary = " ".join(summary_lines)
        if extended_lines:
            ir.extended = "\n".join(extended_lines)

        return ir

    def _parse_args_section(self, lines: list[str], start: int, ir: DocstringIR) -> int:
        """Parse Args section.

        :param lines: Docstring lines
        :param start: Start line index
        :param ir: IR to populate
        :rtype: int
        """
        i = start
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # End of section
            if not stripped or (stripped.endswith(":") and not line.startswith("    ")):
                break

            # Parse argument line
            if line.startswith("    ") and ":" in stripped:
                # Format: "arg_name (type): description"
                # Or: "arg_name: description"
                parts = stripped.split(":", 1)
                name_type = parts[0].strip()
                desc = parts[1].strip() if len(parts) > 1 else ""

                # Extract name and type
                if "(" in name_type and ")" in name_type:
                    name = name_type[: name_type.index("(")].strip()
                    type_hint = name_type[name_type.index("(") + 1 : name_type.rindex(")")].strip()
                else:
                    name = name_type
                    type_hint = None

                ir.params.append(Param(name=name, type_hint=type_hint, description=desc))

            i += 1

        return i

    def _parse_returns_section(self, lines: list[str], start: int, ir: DocstringIR) -> int:
        """Parse Returns section.

        :param lines: Docstring lines
        :param start: Start line index
        :param ir: IR to populate
        :rtype: int
        """
        i = start
        return_lines = []

        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # End of section
            if not stripped or (stripped.endswith(":") and not line.startswith("    ")):
                break

            if line.startswith("    "):
                return_lines.append(stripped)

            i += 1

        if return_lines:
            # Format: "type: description" or just "description"
            return_text = " ".join(return_lines)
            if ":" in return_text:
                parts = return_text.split(":", 1)
                ir.returns = Return(type_hint=parts[0].strip(), description=parts[1].strip())
            else:
                ir.returns = Return(description=return_text)

        return i

    def _parse_raises_section(self, lines: list[str], start: int, ir: DocstringIR) -> int:
        """Parse Raises section.

        :param lines: Docstring lines
        :param start: Start line index
        :param ir: IR to populate
        :rtype: int
        """
        i = start
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # End of section
            if not stripped or (stripped.endswith(":") and not line.startswith("    ")):
                break

            # Parse exception line
            if line.startswith("    ") and ":" in stripped:
                parts = stripped.split(":", 1)
                exc_type = parts[0].strip()
                desc = parts[1].strip() if len(parts) > 1 else ""
                ir.raises.append(Raise(exc_type=exc_type, description=desc))

            i += 1

        return i


class NumPyParser(DocstringParser):
    """Parser for NumPy-style docstrings."""

    def parse(self, docstring: str) -> DocstringIR:
        """Parse NumPy-style docstring.

        :param docstring: Raw docstring text
        :rtype: DocstringIR
        """
        ir = DocstringIR(detected_style=DocstringStyle.NUMPY, confidence=0.8)

        # Dedent first
        docstring = self._dedent(docstring)
        lines = docstring.split("\n")
        if not lines:
            return ir

        # Parse sections
        current_section = "summary"
        summary_lines = []
        extended_lines = []
        i = 0

        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # Detect section headers (followed by dashes)
            if i + 1 < len(lines) and lines[i + 1].strip() and all(c == "-" for c in lines[i + 1].strip()):
                section_name = stripped.lower()
                current_section = section_name
                i += 2  # Skip header and dashes

                if section_name in ["parameters", "params"]:
                    i = self._parse_params_section(lines, i, ir)
                elif section_name in ["returns", "return"]:
                    i = self._parse_returns_section(lines, i, ir)
                elif section_name in ["yields", "yield"]:
                    i = self._parse_yields_section(lines, i, ir)
                elif section_name in ["raises", "raise"]:
                    i = self._parse_raises_section(lines, i, ir)
                else:
                    # Skip unknown section
                    while i < len(lines) and lines[i].strip():
                        i += 1
                continue

            # Summary/extended
            if current_section == "summary":
                if stripped:
                    summary_lines.append(stripped)
                elif summary_lines:
                    current_section = "extended"
                i += 1
            elif current_section == "extended":
                if stripped:
                    extended_lines.append(stripped)
                i += 1
            else:
                i += 1

        ir.summary = " ".join(summary_lines)
        if extended_lines:
            ir.extended = "\n".join(extended_lines)

        return ir

    def _parse_params_section(self, lines: list[str], start: int, ir: DocstringIR) -> int:
        """Parse Parameters section.

        :param lines: Docstring lines
        :param start: Start line index
        :param ir: IR to populate
        :rtype: int
        """
        i = start
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # End of section (empty line followed by another empty or new section)
            if not stripped:
                # Peek ahead
                if i + 1 < len(lines) and not lines[i + 1].strip():
                    i += 1
                    break
                i += 1
                continue

            # Check for new section (header with dashes)
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line and all(c == "-" for c in next_line):
                    break

            # Parameter line: "name : type" or just "name"
            if not line.startswith("    "):
                if ":" in stripped:
                    parts = stripped.split(":", 1)
                    name = parts[0].strip()
                    type_hint = parts[1].strip() if len(parts) > 1 else None
                else:
                    name = stripped
                    type_hint = None

                # Description is on following indented lines
                desc_lines = []
                i += 1
                while i < len(lines) and lines[i].strip() and lines[i].startswith("    "):
                    desc_lines.append(lines[i].strip())
                    i += 1

                description = " ".join(desc_lines) if desc_lines else None
                ir.params.append(Param(name=name, type_hint=type_hint, description=description))
            else:
                i += 1

        return i

    def _parse_returns_section(self, lines: list[str], start: int, ir: DocstringIR) -> int:
        """Parse Returns section.

        :param lines: Docstring lines
        :param start: Start line index
        :param ir: IR to populate
        :rtype: int
        """
        i = start
        type_hint = None
        desc_lines = []

        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            if not stripped:
                # Peek ahead
                if i + 1 < len(lines) and not lines[i + 1].strip():
                    i += 1
                    break
                i += 1
                continue

            # Check for new section
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line and all(c == "-" for c in next_line):
                    break

            # First non-indented line is type
            if not line.startswith("    ") and not type_hint:
                type_hint = stripped
                i += 1
            # Indented lines are description
            elif line.startswith("    "):
                desc_lines.append(stripped)
                i += 1
            else:
                i += 1

        description = " ".join(desc_lines) if desc_lines else None
        if type_hint or description:
            ir.returns = Return(type_hint=type_hint, description=description)

        return i

    def _parse_yields_section(self, lines: list[str], start: int, ir: DocstringIR) -> int:
        """Parse Yields section.

        :param lines: Docstring lines
        :param start: Start line index
        :param ir: IR to populate
        :rtype: int
        """
        i = start
        type_hint = None
        desc_lines = []

        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            if not stripped:
                if i + 1 < len(lines) and not lines[i + 1].strip():
                    i += 1
                    break
                i += 1
                continue

            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line and all(c == "-" for c in next_line):
                    break

            if not line.startswith("    ") and not type_hint:
                type_hint = stripped
                i += 1
            elif line.startswith("    "):
                desc_lines.append(stripped)
                i += 1
            else:
                i += 1

        description = " ".join(desc_lines) if desc_lines else None
        if type_hint or description:
            ir.yields = Return(type_hint=type_hint, description=description)

        return i

    def _parse_raises_section(self, lines: list[str], start: int, ir: DocstringIR) -> int:
        """Parse Raises section.

        :param lines: Docstring lines
        :param start: Start line index
        :param ir: IR to populate
        :rtype: int
        """
        i = start
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            if not stripped:
                if i + 1 < len(lines) and not lines[i + 1].strip():
                    i += 1
                    break
                i += 1
                continue

            # Check for new section
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line and all(c == "-" for c in next_line):
                    break

            # Exception type on non-indented line
            if not line.startswith("    "):
                exc_type = stripped
                desc_lines = []
                i += 1

                # Description on indented lines
                while i < len(lines) and lines[i].strip() and lines[i].startswith("    "):
                    desc_lines.append(lines[i].strip())
                    i += 1

                description = " ".join(desc_lines) if desc_lines else None
                ir.raises.append(Raise(exc_type=exc_type, description=description))
            else:
                i += 1

        return i


class ReSTParser(DocstringParser):
    """Parser for reST/Sphinx-style docstrings."""

    def parse(self, docstring: str) -> DocstringIR:
        """Parse reST-style docstring.

        :param docstring: Raw docstring text
        :rtype: DocstringIR
        """
        ir = DocstringIR(detected_style=DocstringStyle.REST, confidence=0.9)

        # Dedent first
        docstring = self._dedent(docstring)
        lines = docstring.split("\n")
        if not lines:
            return ir

        # Extract summary and fields
        summary_lines = []
        extended_lines = []
        in_summary = True
        in_extended = False

        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # Field markers
            if stripped.startswith(":"):
                in_summary = False
                in_extended = False

                # Parse field
                if stripped.startswith(":param"):
                    self._parse_param_field(stripped, ir)
                elif stripped.startswith(":type"):
                    # :type param_name: type_hint
                    self._parse_type_field(stripped, ir)
                elif stripped.startswith(":returns:") or stripped.startswith(":return:"):
                    desc = stripped.split(":", 2)[2].strip() if stripped.count(":") >= 2 else ""
                    ir.returns = Return(description=desc if desc else None)
                elif stripped.startswith(":rtype:"):
                    type_hint = stripped.split(":", 2)[2].strip() if stripped.count(":") >= 2 else ""
                    if ir.returns:
                        ir.returns.type_hint = type_hint
                    else:
                        ir.returns = Return(type_hint=type_hint)
                elif stripped.startswith(":raises") or stripped.startswith(":raise"):
                    # :raises ExceptionType: description
                    parts = stripped.split(":", 2)
                    if len(parts) >= 3:
                        exc_type = parts[1].replace("raises", "").replace("raise", "").strip()
                        desc = parts[2].strip()
                        ir.raises.append(Raise(exc_type=exc_type, description=desc if desc else None))

                i += 1
                continue

            # Summary/extended description
            if in_summary:
                if stripped:
                    summary_lines.append(stripped)
                elif summary_lines:
                    # Empty line after summary
                    in_summary = False
                    in_extended = True
                i += 1
            elif in_extended:
                if stripped:
                    extended_lines.append(stripped)
                i += 1
            else:
                i += 1

        ir.summary = " ".join(summary_lines)
        if extended_lines:
            ir.extended = "\n".join(extended_lines)

        return ir

    def _parse_param_field(self, field: str, ir: DocstringIR) -> None:
        """Parse :param: field.

        :param field: Field line
        :param ir: IR to populate
        :rtype: None
        """
        # Format: ":param type name: description" or ":param name: description"
        parts = field.split(":", 2)
        if len(parts) < 3:
            return

        param_part = parts[1].replace("param", "").strip()
        description = parts[2].strip() if parts[2] else None

        # Check if type is included
        words = param_part.split()
        if len(words) >= 2:
            # Assume first word is type, rest is name
            type_hint = words[0]
            name = " ".join(words[1:])
        else:
            type_hint = None
            name = param_part

        ir.params.append(Param(name=name, type_hint=type_hint, description=description))

    def _parse_type_field(self, field: str, ir: DocstringIR) -> None:
        """Parse :type: field.

        :param field: Field line
        :param ir: IR to populate
        :rtype: None
        """
        # Format: ":type param_name: type_hint"
        parts = field.split(":", 2)
        if len(parts) < 3:
            return

        param_name = parts[1].replace("type", "").strip()
        type_hint = parts[2].strip() if parts[2] else None

        # Find matching parameter and add type
        for param in ir.params:
            if param.name == param_name:
                param.type_hint = type_hint
                break


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
