# Python Docstring Contract

**Language:** Python 3 (`.py`)  
**Canonical style:** Module docstring using `"""..."""` with reStructuredText-inspired sections

## Purpose

Python scripts in this repository use **module-level docstrings** to document their purpose, usage, and behavior. The style is inspired by reStructuredText (reST) conventions but simplified for readability.

## Required Semantic Sections

Every Python script must include these sections (as reST-style headers in the module docstring):

1. **Module name and summary** - First line: One-line summary of purpose
2. **Purpose** - What the script does (paragraph after summary)
3. **Binary Discovery Order** - For wrapper scripts (optional for others)
4. **Environment Variables** - Variables used and their defaults
5. **Usage** - How to invoke the script (invocation pattern and arguments)
6. **Examples** - Minimum 1 concrete usage example
7. **Exit Codes** - At least: 0 = success, non-zero = failure types
8. **Notes** - Maintainer notes, constraints, sharp edges (optional but recommended)

### Optional Sections

- **Architecture** - High-level design (for complex scripts)
- **Functions** - Brief function descriptions (for library-style modules)
- **Platform** - Platform compatibility notes - **Recommended**
- **References** - Links to related docs

## Formatting Rules

### Docstring Placement

1. **Shebang first**: `#!/usr/bin/env python3`
2. **Module docstring immediately after shebang**: No blank lines between shebang and docstring
3. **Imports after docstring**: Import statements come after the closing `"""`

```python
#!/usr/bin/env python3
"""Module summary.

Detailed description...
"""

import sys
import os
# ... rest of code
```

### Line Length

- **PEP 8 docstring width**: Limit docstring lines to **72 characters** per [PEP 8](https://peps.python.org/pep-0008/#maximum-line-length)
- Use line breaks and indentation to keep lines readable
- Code examples can be wider if necessary

### Structure

```python
#!/usr/bin/env python3
"""One-line summary of what this script does.

Detailed description of behavior. Multiple paragraphs are allowed.
State what it does NOT do if relevant for clarity.

Purpose
-------
Acts as a <role> that <action>. More detailed purpose statement.

Binary Discovery Order
----------------------
Per docs/wrapper-discovery.md (for wrapper scripts only):

1. **ENV_VAR** environment variable (if set, used without validation)
2. **./path/to/dev/binary** (dev mode, relative to repo root)
3. **./dist/<os>/<arch>/binary** (CI artifacts, platform-specific)
4. **PATH lookup** (system-wide installation)
5. **Error with instructions** (exit 127 if not found)

Environment Variables
---------------------
VAR_NAME : str, optional
    Description of environment variable.
    Default: value
    Example: Override binary path.

Usage
-----
The script accepts the same arguments as the underlying tool::

    python3 script-name.py [--] <command> [args...]

The optional "--" separator is stripped before forwarding.

Examples
--------
Basic usage with argument forwarding::

    python3 script-name.py echo "hello"
    python3 script-name.py -- bash -c "exit 42"

Using environment override::

    VAR_NAME=/custom/path python3 script-name.py command

Exit Codes
----------
0
    Success
1
    General failure
127
    Binary not found

Notes
-----
- Important constraint or note 1
- Important constraint or note 2

See Also
--------
- docs/wrapper-discovery.md
- docs/conformance-contract.md
"""

import sys
import os

# Script implementation follows...
```

### Key Rules

1. **Shebang first**: Always start with `#!/usr/bin/env python3`
2. **Triple quotes**: Use `"""..."""` for module docstring (not `'''...'''`)
3. **Summary line**: First line is a standalone summary (no blank line before it)
4. **Blank line after summary**: One blank line separates summary from body
5. **Section headers**: Title case or capitalized words, underlined with dashes
6. **Subsection format**: Use reST-style field lists (e.g., `VAR_NAME : type`)
7. **Code blocks**: Use `::` followed by indented block for code examples
8. **Bold/emphasis**: Use `**bold**` for emphasis in descriptions

## Templates

### Minimal Template

```python
#!/usr/bin/env python3
"""One-line summary of what this script does.

Detailed description of behavior.

Purpose
-------
Acts as a thin wrapper that discovers and executes the canonical tool.

Environment Variables
---------------------
ENV_VAR : str, optional
    Description (default: value)

Usage
-----
The script accepts arguments::

    python3 script-name.py <command> [args...]

Examples
--------
Basic usage::

    python3 script-name.py echo "hello"

Exit Codes
----------
0
    Success
1
    Failure

Notes
-----
- Important constraint or note for maintainers
"""

import sys

# Script implementation follows...


def main():
    """Main entry point."""
    pass


if __name__ == "__main__":
    main()
```

### Full Template (with optional sections)

```python
#!/usr/bin/env python3
"""One-line summary of what this script does.

This module provides a thin invoker that discovers and executes the canonical
implementation. It does NOT reimplement any contract logic or business rules -
all functionality is delegated to the canonical binary.

Purpose
-------
Acts as a language-specific entry point while maintaining contract conformance
through the canonical implementation. Handles binary discovery, platform
detection, and transparent argument forwarding.

Binary Discovery Order
----------------------
Per docs/wrapper-discovery.md, searches for the binary in this order:

1. **BINARY_PATH** environment variable (if set, used without validation)
2. **./rust/target/release/binary** (dev mode, relative to repo root)
3. **./dist/<os>/<arch>/binary** (CI artifacts, platform-specific)
4. **PATH lookup** (system-wide installation via which/shutil.which)
5. **Error with instructions** (exit 127 if not found)

Environment Variables
---------------------
BINARY_PATH : str, optional
    Override binary path. If set, this path is used without validation.
    The wrapper will attempt to execute it and report errors if it fails.

LOG_DIR : str, optional
    Directory for failure logs (default: .agent/FAIL-LOGS)
    Passed through to the canonical tool.

SNIPPET_LINES : int, optional
    Number of tail lines to print on failure (default: 0)
    Set to 0 to disable snippet output.
    Note: Extremely large values may produce noisy stderr.

VIEW_MODE : str, optional
    Output view format: 'split' (default) or 'merged'
    Passed through to the canonical tool.

Usage
-----
The wrapper accepts the same arguments as the canonical tool::

    python3 script-name.py [--] <command> [args...]

The optional "--" separator is stripped before forwarding to the canonical
tool, which expects: binary run <command> [args...]

Examples
--------
Basic usage with argument forwarding::

    python3 script-name.py python3 -c "print('hello')"
    python3 script-name.py -- bash -c "exit 42"

Using environment override::

    BINARY_PATH=/custom/path python3 script-name.py test-command

With multiple environment variables::

    LOG_DIR=/tmp/logs SNIPPET_LINES=10 python3 script-name.py command

Exit Codes
----------
0
    Success - command executed and completed
1
    General failure - command failed or error during execution
2
    Invalid arguments - missing required args or invalid usage
127
    Binary not found - canonical tool is not installed or discoverable

Platform Support
----------------
- Linux: Tested on Ubuntu 20.04+ with Python 3.8+
- macOS: Compatible with Python 3.8+ (Intel and Apple Silicon)
- Windows: Works with Python 3.8+ via native or WSL

Notes
-----
- Do not modify discovery order without updating docs/wrapper-discovery.md
- Exit codes must match canonical tool behavior per conformance contract
- Always preserve child process exit codes (0-255 range)
- This wrapper does NOT implement business logic; all behavior is delegated

See Also
--------
- rfc-shared-agent-scaffolding-v0.1.0.md : Contract specification
- docs/wrapper-discovery.md : Binary discovery rules
- docs/conformance-contract.md : Behavior contract
"""

import sys
import os
import shutil
from pathlib import Path

# Script implementation follows...


def find_binary():
    """Find the canonical binary using the discovery order.
    
    Returns
    -------
    Path or None
        Path to the binary if found, None otherwise.
    """
    pass


def main():
    """Main entry point.
    
    Returns
    -------
    int
        Exit code (0 for success, non-zero for failure)
    """
    pass


if __name__ == "__main__":
    sys.exit(main())
```

## Examples (Existing Files)

### Example 1: Wrapper Script
**File:** `wrappers/scripts/python3/scripts/safe-run.py`

This file demonstrates:
- Full module docstring with all required sections
- Binary Discovery Order section
- Multiple environment variables documented
- Code examples with `::` and indentation
- Exit codes clearly listed
- "See Also" references

### Example 2: Test Script
**File:** `wrappers/scripts/python3/tests/test-safe-run.py`

This file demonstrates:
- Minimal docstring for test modules
- Purpose section focused on testing scope
- Examples of running tests
- Notes about test dependencies

### Example 3: Utility Script
**File:** `wrappers/scripts/python3/scripts/safe-check.py`

This file demonstrates:
- Description that states what it does NOT do
- Usage section with multiple invocation patterns
- Environment Variables with type annotations
- Platform Support section

## Validation

The validator checks for:
- Presence of module docstring (triple-quoted string after shebang/comments)
- Presence of section headers: `Purpose`, `Environment Variables`, `Examples`, `Exit Codes`
- At least one code example with `::` or indented block

The validator does NOT check:
- Docstring formatting perfection
- Function/class docstrings
- Type annotation accuracy
- Grammar or spelling

## Common Mistakes

❌ **Wrong:** No blank line after summary
```python
"""One-line summary.
Detailed description starts immediately.
```

✅ **Correct:** Blank line separates summary from body
```python
"""One-line summary.

Detailed description starts after blank line.
```

❌ **Wrong:** Single quotes for docstring
```python
'''Module docstring'''
```

✅ **Correct:** Use double quotes
```python
"""Module docstring"""
```

❌ **Wrong:** No section headers
```python
"""Script does something.

This is just one big paragraph with no structure.
"""
```

✅ **Correct:** Use section headers
```python
"""Script does something.

Purpose
-------
Detailed purpose description.

Examples
--------
Code example here::

    python3 script.py
"""
```

❌ **Wrong:** Missing Exit Codes section
```python
"""Script summary.

Purpose
-------
Does something useful.

Examples
--------
Usage example.
"""
```

✅ **Correct:** Always document exit codes
```python
"""Script summary.

Purpose
-------
Does something useful.

Examples
--------
Usage example.

Exit Codes
----------
0
    Success
1
    Failure
"""
```

## PEP 257 Compatibility

This contract aligns with [PEP 257](https://peps.python.org/pep-0257/) (Docstring Conventions):
- One-line summary on first line
- Multi-line docstrings have summary, blank line, then body
- Triple double quotes (`"""`)
- Ends on a line by itself

The section structure (reST-style headers) goes beyond PEP 257's minimal requirements but follows common Python documentation conventions.

## References

- [README.md](./README.md) - Overview of docstring contracts
- [exit-codes-contract.md](./exit-codes-contract.md) - Canonical exit code meanings
- [PEP 257 – Docstring Conventions](https://peps.python.org/pep-0257/)
- [reStructuredText Primer](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html)
- [Wrapper Discovery](../wrapper-discovery.md) - Binary discovery rules for wrappers
- [Conformance Contract](../conformance-contract.md) - Behavior contract
