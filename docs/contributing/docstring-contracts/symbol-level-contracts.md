# Symbol-Level Documentation Contracts

**Version:** 1.0
**Last Updated:** 2025-12-29
**Purpose:** Define documentation requirements for functions, classes, methods, and other code symbols across all supported languages.

## Overview

This document extends the file/module-level docstring contracts to cover **symbol-level documentation** - the documentation of individual functions, classes, methods, and language equivalents.

**Scope:** This contract applies to all symbols in:

- Production code (all public/exported symbols)
- Test code (all test functions/methods)
- Wrapper scripts (all functions)
- Utility scripts (all functions)

**Goal:** Ensure every function, class, and method is self-documenting with clear purpose, parameters, return values, and examples where appropriate.

---

## Enforcement Scope

### Minimum Enforcement (Phase 5.5)

Document all **public/exported symbols**:

- Public functions/methods (exposed API)
- Exported wrapper entrypoints
- Test functions/methods

### Recommended Enforcement (Future)

Document all symbols including private helpers for maximum clarity.

---

## Python Symbol Documentation

### Required for All Functions and Methods

Every function and method must have a docstring with:

1. **Summary line** - One-line description of what it does
2. **:param** - All parameters with types and descriptions
3. **:returns** or **:rtype** - Return type and description
4. **:raises** (if applicable) - Exceptions that may be raised

**Format:** reST/Sphinx-style docstrings per PEP 287

#### reST/Sphinx-Style Template

```python
def function_name(arg1: str, arg2: int = 0) -> bool:
    """Brief summary of what this function does.
    
    More detailed description if needed. Can span multiple lines
    and paragraphs.
    
    :param arg1: Description of first argument
    :type arg1: str
    :param arg2: Description of second argument. Defaults to 0.
    :type arg2: int
    :returns: True if successful, False otherwise
    :rtype: bool
    :raises ValueError: If arg1 is empty
    :raises IOError: If file cannot be read
    
    Example::
    
        >>> function_name("test", 5)
        True
    """
    pass
```

#### Compact reST/Sphinx-Style (Preferred)

When types are in annotations, you can use the compact form:

```python
def function_name(arg1: str, arg2: int = 0) -> bool:
    """Brief summary of what this function does.
    
    :param arg1: Description of first argument
    :param arg2: Description of second argument. Defaults to 0.
    :returns: True if successful, False otherwise
    :raises ValueError: If arg1 is empty
    
    Example::
    
        >>> function_name("test", 5)
        True
    """
    pass
```

### Required for All Classes

```python
class ClassName:
    """Brief summary of what this class represents.
    
    More detailed description of the class purpose, behavior,
    and usage patterns.
    
    :ivar attribute1: Description of public attribute
    :ivar attribute2: Description of another attribute
    
    Example::
    
        >>> obj = ClassName()
        >>> obj.method()
        result
    """
    
    def __init__(self, param: str):
        """Initialize ClassName.
        
        :param param: Description of initialization parameter
        """
        pass
```

---

## Bash Symbol Documentation

### Required for All Functions

Every bash function must have a comment block immediately above it with:

1. **Description** - What the function does
2. **Arguments** - Positional parameters and their meaning
3. **Returns** - Exit code meaning
4. **Globals** - Global variables read or modified (if any)

**Format:** Comment block using `#` prefix

```bash
# Find the repository root directory
#
# Walks up from the current directory until it finds .git/
#
# Arguments:
#   None
#
# Returns:
#   0 on success (prints path to stdout)
#   1 if repository root not found
#
# Globals:
#   None
#
# Outputs:
#   Absolute path to repository root
find_repo_root() {
    local dir="$PWD"
    while [[ "$dir" != "/" ]]; do
        if [[ -d "$dir/.git" ]]; then
            echo "$dir"
            return 0
        fi
        dir="$(dirname "$dir")"
    done
    return 1
}
```

### Minimal Function Documentation

For simple utility functions (1-3 lines), a brief inline comment is acceptable:

```bash
# Check if command exists in PATH
have_cmd() { command -v "$1" >/dev/null 2>&1; }
```

---

## Perl Symbol Documentation

### Required for All Subroutines

Every subroutine should have POD documentation or inline comments:

**Format:** POD sections for exported/public subs, comments for internal helpers

```perl
=head2 find_binary

Find the safe-run binary using the standard discovery order.

B<Arguments:>

=over 4

=item * $env_var - Name of environment variable to check first

=back

B<Returns:>

Path to binary (string) or dies with error message.

B<Example:>

    my $binary = find_binary("SAFE_RUN_BIN");

=cut

sub find_binary {
    my ($env_var) = @_;
    # Implementation...
}
```

### For Private/Internal Subroutines

Inline comment is acceptable:

```perl
# Validate that path exists and is executable
sub _validate_binary {
    my ($path) = @_;
    return -x $path;
}
```

---

## PowerShell Symbol Documentation

### Required for All Functions

Every function must have comment-based help:

```powershell
function Find-RepoRoot {
    <#
    .SYNOPSIS
    Find the repository root directory.
    
    .DESCRIPTION
    Walks up from the current directory until it finds .git/
    Returns the absolute path to repository root.
    
    .OUTPUTS
    String. Absolute path to repository root.
    
    .EXAMPLE
    $root = Find-RepoRoot
    
    .NOTES
    Returns $null if repository root not found.
    #>
    
    $dir = Get-Location
    while ($dir.Path -ne $dir.Root.Path) {
        if (Test-Path (Join-Path $dir ".git")) {
            return $dir.Path
        }
        $dir = $dir.Parent
    }
    return $null
}
```

### Minimal Function Documentation

For simple helper functions:

```powershell
# Test if command exists in PATH
function Test-Command {
    param([string]$Name)
    $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}
```

---

## Rust Symbol Documentation

### Required for All Public Functions

Every public function must have rustdoc comments:

```rust
/// Find the safe-run binary using the standard discovery order.
///
/// Searches for the binary in the following order:
/// 1. Environment variable (if provided)
/// 2. Development binary path
/// 3. Distribution binary path
/// 4. System PATH
///
/// # Arguments
///
/// * `env_var` - Optional environment variable name to check first
///
/// # Returns
///
/// Path to the binary if found
///
/// # Errors
///
/// Returns `BinaryNotFoundError` if binary cannot be located
///
/// # Examples
///
/// ```
/// let binary = find_binary(Some("SAFE_RUN_BIN"))?;
/// println!("Found binary at: {}", binary.display());
/// ```
pub fn find_binary(env_var: Option<&str>) -> Result<PathBuf, BinaryNotFoundError> {
    // Implementation...
}
```

### Required for All Public Structs/Enums

```rust
/// Configuration for safe-run execution.
///
/// Controls logging, archival, and execution behavior.
///
/// # Examples
///
/// ```
/// let config = Config {
///     verbose: true,
///     archive_on_success: false,
/// };
/// ```
pub struct Config {
    /// Enable verbose logging
    pub verbose: bool,
    /// Archive artifacts even on success
    pub archive_on_success: bool,
}
```

---

## Validation Strategy

### Phase 5.5 Implementation

The expanded `scripts/validate_docstrings.py` will:

1. **Parse source files** using language-specific parsers (AST for Python, regex/heuristics for others)
2. **Identify symbols** (functions, classes, methods, subs, etc.)
3. **Check for docstrings/comments** immediately preceding or within the symbol definition
4. **Validate minimum required sections** based on symbol type
5. **Report violations** with file path, symbol name, and missing requirements

### Language-Specific Scanners

- **Python:** Use `ast` module to parse and extract docstrings from functions/classes/methods
- **Bash:** Use regex to detect function definitions and preceding comment blocks
- **Perl:** Detect `sub` declarations and check for POD or inline comments
- **PowerShell:** Detect `function` declarations and check for `<# ... #>` blocks
- **Rust:** Detect `pub fn`/`pub struct`/`pub enum` and check for `///` comments

---

## Exemptions and Pragmas

Symbols can be exempted from documentation requirements using pragma comments:

### Python

```python
def internal_helper():  # noqa: D102
    """This function is exempt from full docstring requirements."""
    pass
```

### Bash

```bash
# docstring-ignore: FUNCTION
_internal_helper() {
    echo "exempt"
}
```

### Perl

```perl
# noqa: POD
sub _internal_helper {
    # exempt
}
```

### PowerShell

```powershell
# noqa: HELP
function Internal-Helper {
    # exempt
}
```

### Rust

```rust
#[doc(hidden)]
pub fn internal_helper() {
    // exempt from doc requirements
}
```

---

## Enforcement Rollout

### Phase 5.5.4 Remediation Order

1. **Rust** - Fix all public items (high visibility, well-defined public API)
2. **Python wrappers** - Fix all wrapper functions
3. **PowerShell wrappers** - Fix all wrapper functions
4. **Perl wrappers** - Fix all subs
5. **Bash wrappers** - Fix all functions
6. **Scripts and tools** - Fix utility functions

After each language batch:

- Run linters for that language
- Run wrapper tests (after Rust binary built)
- Run conformance tests
- Ensure CI remains green before proceeding

---

## References

- [PEP 257 – Docstring Conventions](https://peps.python.org/pep-0257/)
- [PEP 287 – reStructuredText Docstring Format](https://peps.python.org/pep-0287/)
- [Rust Rustdoc Guide](https://doc.rust-lang.org/rustdoc/how-to-write-documentation.html)
- [PowerShell Comment-Based Help](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_comment_based_help)
- [Perl POD Documentation](https://perldoc.perl.org/perlpod)

---

## Document History

- **2025-12-29:** Created as part of Phase 5.5, Item 5.5.1
  - Defined symbol-level documentation requirements for all supported languages
  - Established enforcement scope and validation strategy
  - Created templates and examples for each language
