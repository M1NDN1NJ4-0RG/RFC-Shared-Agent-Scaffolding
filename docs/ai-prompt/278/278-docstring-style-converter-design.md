# Docstring Style Converter: Design Document

## Overview

Build a bidirectional docstring style converter that can transform between:
1. **reST/Sphinx** (current repo standard)
2. **Google Style**
3. **NumPy Style**

This tool will parse docstrings, extract semantic structure, and reformat to target style.

## Motivation

**Use cases:**
1. **Repo migration**: Convert legacy Google/NumPy docstrings to reST
2. **Auto-format**: Standardize mixed-style codebases
3. **Developer preference**: Some developers prefer Google style, others reST
4. **Tool compatibility**: Some tools expect specific styles

## Docstring Styles Comparison

### Example: Same Function, Three Styles

**reST/Sphinx Style (current repo standard):**
```python
def find_user(user_id: int, include_deleted: bool = False) -> User | None:
    """Find user by ID in the database.
    
    Searches the database for a user with the given ID. Can optionally
    include deleted users in the search.
    
    :param user_id: Unique identifier for the user
    :param include_deleted: Whether to include deleted users in search
    :returns: User object if found, None otherwise
    :rtype: User | None
    :raises ValueError: If user_id is negative
    :raises DatabaseError: If database connection fails
    
    :Example:
        >>> user = find_user(123)
        >>> if user:
        ...     print(user.name)
    """
    ...
```

**Google Style:**
```python
def find_user(user_id: int, include_deleted: bool = False) -> User | None:
    """Find user by ID in the database.
    
    Searches the database for a user with the given ID. Can optionally
    include deleted users in the search.
    
    Args:
        user_id: Unique identifier for the user
        include_deleted: Whether to include deleted users in search
    
    Returns:
        User object if found, None otherwise
    
    Raises:
        ValueError: If user_id is negative
        DatabaseError: If database connection fails
    
    Example:
        >>> user = find_user(123)
        >>> if user:
        ...     print(user.name)
    """
    ...
```

**NumPy Style:**
```python
def find_user(user_id: int, include_deleted: bool = False) -> User | None:
    """Find user by ID in the database.
    
    Searches the database for a user with the given ID. Can optionally
    include deleted users in the search.
    
    Parameters
    ----------
    user_id : int
        Unique identifier for the user
    include_deleted : bool, optional
        Whether to include deleted users in search (default is False)
    
    Returns
    -------
    User | None
        User object if found, None otherwise
    
    Raises
    ------
    ValueError
        If user_id is negative
    DatabaseError
        If database connection fails
    
    Examples
    --------
    >>> user = find_user(123)
    >>> if user:
    ...     print(user.name)
    """
    ...
```

## Architecture

### High-Level Flow

```
Input docstring (any style)
    ↓
Parse → Extract semantic structure (DocstringModel)
    ↓
Validate → Check completeness
    ↓
Format → Render to target style
    ↓
Output docstring (target style)
```

### Core Components

#### 1. Semantic Docstring Model

**Internal representation (style-agnostic):**

```python
@dataclass
class DocstringModel:
    """Style-agnostic docstring representation."""
    
    summary: str
    """Single-line summary (first line)."""
    
    description: str | None
    """Extended description (can be multi-paragraph)."""
    
    parameters: list[Parameter]
    """Function/method parameters."""
    
    returns: Return | None
    """Return value description."""
    
    raises: list[Exception]
    """Exceptions that can be raised."""
    
    examples: list[Example]
    """Usage examples."""
    
    attributes: list[Attribute]
    """Class attributes (for class docstrings)."""
    
    notes: list[str]
    """Additional notes."""
    
    warnings: list[str]
    """Warnings for users."""
    
    see_also: list[str]
    """Related functions/classes."""
    
    references: list[str]
    """Bibliography/citations."""

@dataclass
class Parameter:
    """Parameter documentation."""
    name: str
    type_hint: str | None
    description: str
    optional: bool = False
    default: str | None = None

@dataclass
class Return:
    """Return value documentation."""
    type_hint: str | None
    description: str

@dataclass
class Exception:
    """Exception documentation."""
    type_name: str
    description: str

@dataclass
class Example:
    """Usage example."""
    code: str
    description: str | None = None
```

#### 2. Style Parsers

**One parser per style:**

```python
class ReSTParser:
    """Parse reST/Sphinx style docstrings."""
    
    def parse(self, docstring: str) -> DocstringModel:
        """Parse reST docstring into semantic model.
        
        :param docstring: Raw docstring text
        :rtype: DocstringModel
        """
        # Parse :param:, :returns:, :raises:, etc.
        ...

class GoogleParser:
    """Parse Google style docstrings."""
    
    def parse(self, docstring: str) -> DocstringModel:
        """Parse Google docstring into semantic model.
        
        Args:
            docstring: Raw docstring text
        
        Returns:
            Semantic docstring model
        """
        # Parse Args:, Returns:, Raises:, etc.
        ...

class NumpyParser:
    """Parse NumPy style docstrings."""
    
    def parse(self, docstring: str) -> DocstringModel:
        """Parse NumPy docstring into semantic model.
        
        Parameters
        ----------
        docstring : str
            Raw docstring text
        
        Returns
        -------
        DocstringModel
            Semantic docstring model
        """
        # Parse Parameters, Returns, Raises, etc.
        ...
```

#### 3. Style Formatters

**One formatter per style:**

```python
class ReSTFormatter:
    """Format docstring model to reST/Sphinx style."""
    
    def format(self, model: DocstringModel) -> str:
        """Format semantic model to reST docstring.
        
        :param model: Semantic docstring model
        :rtype: str
        """
        # Generate :param:, :returns:, :rtype:, etc.
        ...

class GoogleFormatter:
    """Format docstring model to Google style."""
    
    def format(self, model: DocstringModel) -> str:
        """Format semantic model to Google docstring.
        
        Args:
            model: Semantic docstring model
        
        Returns:
            Formatted Google-style docstring
        """
        # Generate Args:, Returns:, Raises:, etc.
        ...

class NumpyFormatter:
    """Format docstring model to NumPy style."""
    
    def format(self, model: DocstringModel) -> str:
        """Format semantic model to NumPy docstring.
        
        Parameters
        ----------
        model : DocstringModel
            Semantic docstring model
        
        Returns
        -------
        str
            Formatted NumPy-style docstring
        """
        # Generate Parameters, Returns, Raises, etc.
        ...
```

#### 4. Converter Orchestrator

```python
class DocstringConverter:
    """Convert between docstring styles."""
    
    def __init__(self):
        self.parsers = {
            'rest': ReSTParser(),
            'google': GoogleParser(),
            'numpy': NumpyParser(),
        }
        self.formatters = {
            'rest': ReSTFormatter(),
            'google': GoogleFormatter(),
            'numpy': NumpyFormatter(),
        }
    
    def convert(
        self,
        docstring: str,
        from_style: str,
        to_style: str,
        preserve_type_hints: bool = True
    ) -> str:
        """Convert docstring from one style to another.
        
        :param docstring: Original docstring
        :param from_style: Source style (rest/google/numpy)
        :param to_style: Target style (rest/google/numpy)
        :param preserve_type_hints: Preserve inline type hints
        :rtype: str
        """
        # Parse
        model = self.parsers[from_style].parse(docstring)
        
        # Enhance with function signature if available
        if preserve_type_hints:
            model = self._merge_with_annotations(model)
        
        # Format
        return self.formatters[to_style].format(model)
    
    def auto_detect_style(self, docstring: str) -> str:
        """Auto-detect docstring style.
        
        :param docstring: Docstring to analyze
        :rtype: str
        """
        # Heuristics:
        # - Has ":param:" → reST
        # - Has "Args:" → Google
        # - Has "Parameters\n----------" → NumPy
        ...
```

## Implementation Strategy

### Phase 1: Build Parsers

**Start with reST (highest priority):**

```python
import re
from dataclasses import dataclass, field

class ReSTParser:
    """Parse reST docstrings."""
    
    # Field patterns
    PARAM_PATTERN = r':param\s+(\w+):\s*(.+)'
    TYPE_PATTERN = r':type\s+(\w+):\s*(.+)'
    RETURNS_PATTERN = r':returns?:\s*(.+)'
    RTYPE_PATTERN = r':rtype:\s*(.+)'
    RAISES_PATTERN = r':raises?\s+(\w+):\s*(.+)'
    
    def parse(self, docstring: str) -> DocstringModel:
        """Parse reST docstring."""
        lines = docstring.split('\n')
        
        model = DocstringModel(
            summary='',
            description=None,
            parameters=[],
            returns=None,
            raises=[],
            examples=[],
            attributes=[],
            notes=[],
            warnings=[],
            see_also=[],
            references=[]
        )
        
        # Extract summary (first line)
        model.summary = lines[0].strip() if lines else ''
        
        # Extract description (lines before first field)
        desc_lines = []
        i = 1
        while i < len(lines):
            line = lines[i]
            if line.strip().startswith(':'):
                break
            desc_lines.append(line)
            i += 1
        model.description = '\n'.join(desc_lines).strip() or None
        
        # Extract fields
        while i < len(lines):
            line = lines[i].strip()
            
            # :param name: description
            if match := re.match(self.PARAM_PATTERN, line):
                param_name, param_desc = match.groups()
                model.parameters.append(Parameter(
                    name=param_name,
                    type_hint=None,  # Will be filled from :type:
                    description=param_desc.strip()
                ))
            
            # :type name: type_hint
            elif match := re.match(self.TYPE_PATTERN, line):
                param_name, type_hint = match.groups()
                # Find matching parameter and add type
                for param in model.parameters:
                    if param.name == param_name:
                        param.type_hint = type_hint.strip()
                        break
            
            # :returns: description
            elif match := re.match(self.RETURNS_PATTERN, line):
                model.returns = Return(
                    type_hint=None,  # Will be filled from :rtype:
                    description=match.group(1).strip()
                )
            
            # :rtype: type_hint
            elif match := re.match(self.RTYPE_PATTERN, line):
                if model.returns:
                    model.returns.type_hint = match.group(1).strip()
                else:
                    # Create returns with only type
                    model.returns = Return(
                        type_hint=match.group(1).strip(),
                        description=''
                    )
            
            # :raises ExceptionType: description
            elif match := re.match(self.RAISES_PATTERN, line):
                exc_type, exc_desc = match.groups()
                model.raises.append(Exception(
                    type_name=exc_type.strip(),
                    description=exc_desc.strip()
                ))
            
            i += 1
        
        return model
```

### Phase 2: Build Formatters

**Start with Google (complement to reST):**

```python
class GoogleFormatter:
    """Format to Google style."""
    
    def format(self, model: DocstringModel) -> str:
        """Format model to Google docstring."""
        lines = []
        
        # Summary
        lines.append(model.summary)
        
        # Description
        if model.description:
            lines.append('')
            lines.append(model.description)
        
        # Args
        if model.parameters:
            lines.append('')
            lines.append('Args:')
            for param in model.parameters:
                if param.type_hint:
                    lines.append(f'    {param.name} ({param.type_hint}): {param.description}')
                else:
                    lines.append(f'    {param.name}: {param.description}')
        
        # Returns
        if model.returns:
            lines.append('')
            lines.append('Returns:')
            if model.returns.type_hint:
                lines.append(f'    {model.returns.type_hint}: {model.returns.description}')
            else:
                lines.append(f'    {model.returns.description}')
        
        # Raises
        if model.raises:
            lines.append('')
            lines.append('Raises:')
            for exc in model.raises:
                lines.append(f'    {exc.type_name}: {exc.description}')
        
        # Examples
        if model.examples:
            lines.append('')
            lines.append('Example:')
            for ex in model.examples:
                if ex.description:
                    lines.append(f'    {ex.description}')
                for code_line in ex.code.split('\n'):
                    lines.append(f'    {code_line}')
        
        return '\n'.join(lines)
```

### Phase 3: AST Integration

**Enhance with function signature information:**

```python
import ast

class DocstringEnhancer:
    """Enhance docstring model with AST function info."""
    
    def enhance_from_function(
        self,
        model: DocstringModel,
        func_node: ast.FunctionDef
    ) -> DocstringModel:
        """Add type hints from function signature.
        
        :param model: Parsed docstring model
        :param func_node: AST function definition node
        :rtype: DocstringModel
        """
        # Add parameter type hints from annotations
        for i, arg in enumerate(func_node.args.args):
            if arg.annotation:
                type_str = ast.unparse(arg.annotation)
                # Find matching parameter in model
                for param in model.parameters:
                    if param.name == arg.arg and not param.type_hint:
                        param.type_hint = type_str
        
        # Add return type hint from annotation
        if func_node.returns and model.returns:
            if not model.returns.type_hint:
                model.returns.type_hint = ast.unparse(func_node.returns)
        
        return model
```

### Phase 4: CLI Integration

```python
# In tools/repo_lint/cli.py

@cli.command("convert-docstrings")
@click.option(
    "--from-style",
    type=click.Choice(["rest", "google", "numpy", "auto"]),
    default="auto",
    help="Source docstring style (auto-detect if not specified)"
)
@click.option(
    "--to-style",
    type=click.Choice(["rest", "google", "numpy"]),
    required=True,
    help="Target docstring style"
)
@click.option(
    "--in-place",
    is_flag=True,
    help="Modify files in place"
)
@click.option(
    "--diff",
    is_flag=True,
    help="Show diff instead of modifying"
)
@click.argument("files", nargs=-1, type=click.Path(exists=True))
def convert_docstrings(from_style, to_style, in_place, diff, files):
    """Convert docstring styles.
    
    \b
    Examples:
        # Convert all Python files from Google to reST
        repo-lint convert-docstrings --from-style google --to-style rest --in-place **/*.py
        
        # Preview conversion (diff mode)
        repo-lint convert-docstrings --to-style google --diff src/mymodule.py
    """
    converter = DocstringConverter()
    
    for file_path in files:
        # Read file
        tree = ast.parse(Path(file_path).read_text())
        
        # Convert all docstrings
        modified = False
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
                docstring = ast.get_docstring(node)
                if not docstring:
                    continue
                
                # Auto-detect if needed
                source_style = from_style
                if source_style == "auto":
                    source_style = converter.auto_detect_style(docstring)
                
                # Convert
                new_docstring = converter.convert(
                    docstring,
                    source_style,
                    to_style,
                    preserve_type_hints=True
                )
                
                # Replace in AST
                replace_docstring(node, new_docstring)
                modified = True
        
        if modified:
            if diff:
                show_diff(file_path, tree)
            elif in_place:
                write_file(file_path, ast.unparse(tree))
                console.print(f"[green]✓[/green] Converted {file_path}")
```

## Use Case: Auto-add `:rtype:` via Conversion

**Clever approach:**

1. Parse reST docstring (missing `:rtype:`)
2. Enhance model with function annotation (`-> str`)
3. Re-format back to reST (now includes `:rtype: str`)

**This is basically "convert reST to reST" but with enrichment!**

```python
def auto_add_rtype(file_path: Path) -> bool:
    """Add missing :rtype: fields using conversion trick."""
    converter = DocstringConverter()
    
    # Read and parse file
    tree = ast.parse(file_path.read_text())
    modified = False
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            docstring = ast.get_docstring(node)
            if not docstring or ':rtype:' in docstring:
                continue
            
            if not node.returns or is_none_return(node.returns):
                continue  # Skip None returns
            
            # Parse docstring
            model = converter.parsers['rest'].parse(docstring)
            
            # Enhance with annotation
            enhancer = DocstringEnhancer()
            model = enhancer.enhance_from_function(model, node)
            
            # Re-format (will include :rtype: now)
            new_docstring = converter.formatters['rest'].format(model)
            
            # Replace
            replace_docstring(node, new_docstring)
            modified = True
    
    return modified
```

## Existing Libraries

**Don't reinvent the wheel - leverage existing parsers:**

1. **docstring_parser** (PyPI)
   - Already parses Google, NumPy, reST
   - Returns semantic model
   - We can extend it or use as-is

2. **napoleon** (Sphinx extension)
   - Converts Google/NumPy → reST for Sphinx
   - Can extract conversion logic

3. **pyment** (PyPI)
   - Converts between docstring styles
   - CLI tool (can integrate or learn from)

**Recommendation:** Use `docstring_parser` library as the parsing engine, build formatters on top.

## Timeline Estimate

### Using `docstring_parser` library:

- **Phase 1**: Install and test `docstring_parser` (30 min)
- **Phase 2**: Build ReSTFormatter (2-3 hours)
- **Phase 3**: Build GoogleFormatter (2-3 hours)
- **Phase 4**: AST integration + CLI (2-3 hours)
- **Phase 5**: Testing + edge cases (2-3 hours)
- **Phase 6**: Auto-add `:rtype:` feature (1-2 hours)

**Total: 10-15 hours**

### Building from scratch:

**Total: 25-35 hours**

## Next Steps

1. Research `docstring_parser` library capabilities
2. Prototype reST → Google conversion
3. Add AST enhancement layer
4. Integrate into `repo-lint convert-docstrings` command
5. Use for auto-adding `:rtype:` fields

---

## Benefits

1. **Standardize codebase**: Convert all to reST (repo standard)
2. **Auto-complete docstrings**: Add `:rtype:` from annotations
3. **Developer flexibility**: Let devs write in preferred style, auto-convert
4. **Migration tool**: Help repos adopt new standards
5. **Validation**: Ensure docstrings match function signatures

This would be a **major productivity boost** for the repo!
