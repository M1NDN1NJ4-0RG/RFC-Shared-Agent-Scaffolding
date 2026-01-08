# Python Exception Handling Policy

**Document Purpose:** This document defines the repository's policy for exception handling in Python code, establishing
when broad exception handlers are acceptable and what patterns to follow when catching exceptions.

**Authority:** This is a canonical contract document. All Python code in this repository MUST comply with these rules
unless explicitly exempted with documented justification.

**Last Updated:** 2026-01-08

______________________________________________________________________

## Core Principles

1. 1. 1. **Narrow exception types** when the failure mode is known and specific 2. **Preserve exception context** via
   exception chaining (`raise ... from e`) 3. 3. **Fail fast** in library code - don't swallow exceptions that callers
   need to see 4. **Convert cleanly** at CLI boundaries - turn exceptions into user-friendly messages + exit codes 5.
   **Document intentional broad catches** with inline comments explaining why

______________________________________________________________________

## Acceptable vs Unacceptable Broad Exception Usage

### ACCEPTABLE: CLI Boundary Pattern

Broad exception handlers (`except Exception as e:`) are **ACCEPTABLE** at CLI boundaries where the goal is to convert
any unexpected error into a clean user-facing message and non-zero exit code.

**Requirements:**

- - - MUST be at top-level CLI entry points (main functions, command handlers) - MUST produce a clear error message for
  the user - MUST exit with a non-zero exit code - SHOULD include `--verbose` or `--debug` mode that shows full
  traceback - - SHOULD include the exception type/message in the error output

**Example (GOOD):**

```python
 def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    try:
        args = parse_args(argv)
        result = execute_command(args)
        return 0 if result.success else 1
    except Exception as e:
        # CLI boundary exception handler (acceptable pattern)
        print(f"❌ Error: {e}", file=sys.stderr)
        # Note: args may not be defined if parse_args() failed
        # Use getattr with default to avoid NameError
        if getattr(args if 'args' in locals() else None, 'verbose', False):
            import traceback
            traceback.print_exc()
        return 1
```

**Counter-example (BAD - library code):**

```python
def process_file(path: Path) -> dict:
    """Process a file."""
    try:
        return json.loads(path.read_text())
    except Exception:  # BAD: Swallows all errors, caller can't distinguish failures
        return {}
```

### ACCEPTABLE: Diagnostic/Doctor Tools

Broad exception handlers are **ACCEPTABLE** in diagnostic tools (like `repo-lint doctor`) where the goal is to report on
system state without failing.

**Requirements:**

- - - MUST return structured error status (success/failure + message) - MUST NOT silently swallow exceptions - log or
  return error details - SHOULD use a tuple return pattern: `(success: bool, message: str, detail: str)`

**Example (GOOD):**

```python
def check_tool_availability(tool: str) -> tuple[bool, str, str]:
    """Check if a tool is available.

    :returns: (success, message, detail)
    """
    try:
        result = subprocess.run([tool, "--version"], capture_output=True, check=True)
        return True, f"{tool} is available", result.stdout.decode()
    except Exception as e:
        return False, f"{tool} not found: {e}", ""
```

### ACCEPTABLE: Test Cleanup Code

Broad exception handlers are **ACCEPTABLE** in test cleanup code (finally blocks) where cleanup failures should not mask
the actual test result.

**Requirements:**

- - MUST be in a `finally` block or test teardown - - MUST be cleanup-only operations (closing files, killing processes,
  etc.) - MAY silently swallow exceptions (test cleanup should not fail tests)

**Example (GOOD):**

```python
def test_subprocess_handling():
    """Test subprocess behavior."""
    p = subprocess.Popen(...)
    try:
        # ... test logic ...
        assert ...
    finally:
        try:
            p.kill()
        except Exception:
            pass  # Process may already be dead
```

### UNACCEPTABLE: Library Code

Broad exception handlers are **UNACCEPTABLE** in library code unless you are explicitly designing a "fail-safe" API
where any error returns a safe fallback.

**Why:** Library code callers need to distinguish between failure modes (file not found vs permission denied vs corrupt
data) to make appropriate recovery decisions.

**What to do instead:** Narrow to specific exception types, or let exceptions propagate.

**Counter-example (BAD):**

```python
def read_config(path: Path) -> dict:
    """Read configuration file."""
    try:
        return json.loads(path.read_text())
    except Exception:  # BAD: File not found? JSON parse error? Permission denied? Caller can't tell
        return {}
```

**Fixed (GOOD):**

```python
def read_config(path: Path) -> dict:
    """Read configuration file.

    :raises FileNotFoundError: Config file does not exist
    :raises json.JSONDecodeError: Config file is not valid JSON
    :raises OSError: Config file cannot be read
    """
    try:
        content = path.read_text()
    except OSError as e:
        # Re-raise with context
        raise OSError(f"Failed to read config from {path}") from e

    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Invalid JSON in {path}", e.doc, e.pos
        ) from e
```

______________________________________________________________________

## Required Behaviors When Catching Exceptions

### 1. Use Specific Exception Types

**Prefer specific built-in exceptions:**

- - `FileNotFoundError`, `PermissionError`, `IsADirectoryError` instead of `OSError` when you know the failure mode -
  `json.JSONDecodeError` instead of `Exception` for JSON parsing - `subprocess.CalledProcessError` instead of
  `Exception` for subprocess failures - `ValueError`, `TypeError`, `KeyError` for data validation - `UnicodeDecodeError`
  instead of `Exception` for encoding issues

**When to use broader types:**

- - `OSError` is acceptable when catching any file I/O error (it covers `FileNotFoundError`, `PermissionError`, etc.) -
  `Exception` is acceptable **only** at CLI boundaries or in diagnostic tools (see above)

### 2. Preserve Exception Context via Chaining

When re-raising or raising a new exception, **ALWAYS** preserve the original exception via `raise ... from e`.

**Example (GOOD):**

```python
try:
    data = json.loads(content)
except json.JSONDecodeError as e:
    raise ValueError(f"Invalid config format in {path}") from e
```

**Counter-example (BAD):**

```python
try:
    data = json.loads(content)
except json.JSONDecodeError as e:
    raise ValueError(f"Invalid config format in {path}")  # Lost original exception!
```

### 3. Include Actionable Context in Error Messages

Error messages MUST include enough context for the user to diagnose the problem.

**Good error messages include:**

- - - Which file/resource failed - What operation was being attempted - Relevant values (paths, tool names, etc.)

**Example (GOOD):**

```python
except FileNotFoundError as e:
    raise FileNotFoundError(
        f"Config file not found: {path}. "
        f"Expected location: {path.absolute()}"
    ) from e
```

**Counter-example (BAD):**

```python
except FileNotFoundError:
    raise FileNotFoundError("File not found")  # Which file?!
```

### 4. Document Intentional Broad Catches

If you MUST use a broad exception handler (e.g., wrapping a third-party library with unpredictable exceptions), add an
inline comment explaining:

- - - Why the broad catch is necessary - What failure modes are expected - Whether this is temporary (TODO: narrow when
  possible)

**Example (ACCEPTABLE with documentation):**

```python
try:
    # Third-party library has undocumented exception types
    result = external_library.process(data)
except Exception as e:
    # Broad catch required: external_library raises various undocumented exceptions.
    # TODO: Narrow once we identify the actual exception types from usage/docs.
    logger.error("External library processing failed: %s", e)
    raise RuntimeError(f"Processing failed: {e}") from e
```

______________________________________________________________________

## Custom Exception Types

When appropriate, create custom exception types to clarify domain-specific errors.

### When to Create Custom Exceptions

Create custom exceptions when:

1. 1. 1. You need to distinguish this error type from built-in exceptions 2. You want callers to be able to catch this
   specific error type 3. The error represents a domain-specific failure mode

### Custom Exception Location

Custom exceptions MUST be defined in a canonical module:

- - `tools/repo_lint/exceptions.py` for repo-lint exceptions - Module-level `exceptions.py` for other packages

### Custom Exception Template

```python
class RepoLintError(Exception):
    """Base exception for all repo-lint errors."""
    pass

class MissingToolError(RepoLintError):
    """Raised when a required tool is not installed."""

    def __init__(self, tool: str, message: str = "") -> None:
        self.tool = tool
        default_msg = f"Required tool not found: {tool}"
        super().__init__(message or default_msg)

class ConfigurationError(RepoLintError):
    """Raised when configuration is invalid."""

    def __init__(self, config_path: Path, issue: str) -> None:
        self.config_path = config_path
        self.issue = issue
        super().__init__(f"Invalid configuration in {config_path}: {issue}")
```

______________________________________________________________________

## Exit Codes

CLI tools MUST use consistent exit codes:

| Exit Code | Meaning |
| ----------- | --------- |
| 0 | Success |
| 1 | Violations found (linting) or general error |
| 2 | Missing required tools |
| 3 | Invalid arguments / configuration |
| Other | Reserved for future use |

**Example:**

```python
class ExitCode(IntEnum):
    """Standard exit codes for repo-lint."""
    SUCCESS = 0
    VIOLATIONS_FOUND = 1
    MISSING_TOOLS = 2
    INVALID_CONFIG = 3
    INTERNAL_ERROR = 99
```

______________________________________________________________________

## Migration Strategy

For existing code with overly-broad exception handlers:

1. 1. 1. **Identify the failure modes** by examining the code or running tests 2. **Narrow to specific exception types**
   that cover the actual failure modes 3. **Add exception chaining** (`raise ... from e`) when re-raising 4. 4. **Add
   tests** that verify the correct exception type is raised 5. **Document** any remaining broad catches with inline
   comments

______________________________________________________________________

## Examples

### Example 1: File I/O with Narrow Exception Types

```python
def load_config(path: Path) -> dict:
    """Load configuration from YAML file.

    :param path: Path to configuration file
    :returns: Configuration dictionary
    :raises FileNotFoundError: Config file does not exist
    :raises PermissionError: Config file cannot be read
    :raises yaml.YAMLError: Config file is not valid YAML
    """
    try:
        content = path.read_text(encoding="utf-8")
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Config not found: {path}") from e
    except PermissionError as e:
        raise PermissionError(f"Cannot read config: {path}") from e
    except UnicodeDecodeError as e:
        raise UnicodeDecodeError(
            e.encoding, e.object, e.start, e.end,
            f"Config file {path} is not valid UTF-8"
        ) from e

    try:
        return yaml.safe_load(content)
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Invalid YAML in {path}: {e}") from e
```

### Example 2: Subprocess Execution

```python
def run_tool(tool: str, args: list[str]) -> subprocess.CompletedProcess:
    """Run an external tool.

    :param tool: Tool name
    :param args: Tool arguments
    :returns: Completed process result
    :raises FileNotFoundError: Tool executable not found
    :raises subprocess.CalledProcessError: Tool failed
    :raises OSError: Other execution error (permission, etc.)
    """
    try:
        return subprocess.run(
            [tool] + args,
            capture_output=True,
            check=True,
            text=True
        )
    except FileNotFoundError as e:
        raise FileNotFoundError(
            f"Tool not found: {tool}. Is it installed and in PATH?"
        ) from e
    except subprocess.CalledProcessError as e:
        raise subprocess.CalledProcessError(
            e.returncode, e.cmd,
            output=e.output, stderr=e.stderr
        ) from e
    # OSError propagates naturally (permission denied, etc.)
```

### Example 3: CLI Boundary (Acceptable Broad Catch)

```python
 def main(argv: list[str] | None = None) -> int:
    """CLI entry point.

    :param argv: Command line arguments (or None for sys.argv)
    :returns: Exit code (0 = success, non-zero = error)
    """
    # Initialize verbose flag before try block to avoid NameError in exception handler
    verbose = False
    try:
        args = parse_args(argv)
        verbose = args.verbose  # Capture verbose flag
        result = execute_command(args)
        return 0 if result.success else 1
    except MissingToolError as e:
        # Specific error first
        print(f"❌ Missing tool: {e.tool}", file=sys.stderr)
        print("   Run 'repo-lint install' to install missing tools", file=sys.stderr)
        return ExitCode.MISSING_TOOLS
    except ConfigurationError as e:
        # Specific error second
        print(f"❌ Configuration error: {e}", file=sys.stderr)
        return ExitCode.INVALID_CONFIG
    except Exception as e:
        # Broad catch at CLI boundary (acceptable pattern)
        print(f"❌ Internal error: {e}", file=sys.stderr)
        if verbose:  # Use captured verbose flag to avoid NameError
            import traceback
            traceback.print_exc()
        return ExitCode.INTERNAL_ERROR
```

______________________________________________________________________

## References

- - - PEP 3134 - Exception Chaining and Embedded Tracebacks
- Python Built-in Exceptions: <https://docs.python.org/3/library/exceptions.html>
- Best Practices for Exception Handling: <https://docs.python-guide.org/writing/gotchas/#exceptions>

______________________________________________________________________

## Summary

| Pattern | Acceptable? | Requirements |
| --------- | ------------- | -------------- |
| Broad catch at CLI boundary | ✅ YES | User-friendly message + non-zero exit + verbose mode |
| Broad catch in diagnostic tools | ✅ YES | Structured error return (success, message, detail) |
| Broad catch in test cleanup | ✅ YES | Must be in finally block, cleanup-only |
| Broad catch in library code | ❌ NO | Use narrow exception types instead |
| Custom exceptions | ✅ YES | Define in `exceptions.py`, inherit from base exception |
| Exception chaining | ✅ REQUIRED | Always use `raise ... from e` when re-raising |
| Actionable error messages | ✅ REQUIRED | Include file/resource/operation context |

______________________________________________________________________
