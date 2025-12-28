# Exit Codes Contract

**Purpose:** Define canonical exit code meanings for all scripts and tools in this repository.

## Why Exit Codes Matter

Exit codes are a universal language for process success/failure communication. Consistent exit code semantics across all languages ensure:
- Predictable behavior in CI/CD pipelines
- Reliable error detection in automation
- Clear communication between wrapper scripts and canonical tools
- Consistent user experience across language implementations

## Canonical Exit Codes

All scripts and tools in this repository **MUST** use these exit code conventions:

### Exit Code 0: Success
```
Meaning: Operation completed successfully
When to use: Command executed without errors, all validations passed
Example: Test suite passed, file processed successfully, binary executed and completed
```

**Rules:**
- Exit 0 only when operation fully succeeded
- Do not exit 0 if warnings were suppressed
- Do not exit 0 if partial success occurred (use exit 1 instead)

### Exit Code 1: General Failure
```
Meaning: Operation failed, generic error
When to use: 
  - Command execution failed
  - Validation errors detected
  - Business logic errors
  - Runtime errors not covered by more specific codes
Example: Test failures, command returned non-zero, validation contract violations
```

**Rules:**
- Use exit 1 as the default failure code
- Prefer more specific codes (2, 127) when applicable
- Exit 1 for validation failures, assertion failures, unexpected errors

### Exit Code 2: Invalid Usage / Missing Arguments
```
Meaning: Invalid arguments, missing required parameters, usage error
When to use:
  - Required arguments not provided
  - Invalid argument format or values
  - Incompatible argument combinations
  - Help requested (some tools use 0, but 2 is acceptable)
Example: Missing required --file argument, invalid --format value, conflicting flags
```

**Rules:**
- Exit 2 for argument parsing/validation failures
- Print usage/help message to stderr before exiting
- Distinguish from runtime failures (exit 1)

### Exit Code 127: Command Not Found
```
Meaning: Binary, tool, or command not found
When to use:
  - Wrapper script cannot locate canonical binary
  - Binary discovery exhausted all search paths
  - Required external command not available
Example: safe-run wrapper cannot find canonical tool, missing system dependency
```

**Rules:**
- Exit 127 specifically for "not found" scenarios
- Matches POSIX shell convention for command not found
- Print actionable error with installation instructions
- Suggest environment variable overrides (e.g., BINARY_PATH)

### Exit Codes 3-125: Reserved for Future Use
```
Meaning: Reserved for tool-specific error codes
When to use: Only when documented in tool's docstring
Example: Custom error codes for specific failure modes
```

**Rules:**
- Document any custom codes in tool's docstring/contract
- Avoid unless you need fine-grained error distinction
- Prefer exit 1 for most failures

### Exit Code 126: Permission Denied / Not Executable
```
Meaning: Command found but cannot execute (permission denied)
When to use: Binary exists but lacks execute permission
Example: Found tool binary but it's not executable
```

**Rules:**
- Use when binary exists but cannot be executed
- Distinguish from 127 (not found)
- Suggest chmod +x or permission fix

### Exit Codes 128+: Signal-Related Exits
```
Meaning: Process terminated by signal
Convention: 128 + signal_number
Example: 130 = 128 + 2 (SIGINT/Ctrl+C), 137 = 128 + 9 (SIGKILL), 143 = 128 + 15 (SIGTERM)
When to use: Automatically set by shell when process killed by signal
```

**Rules:**
- Do not explicitly use 128+ codes in your code
- These are set automatically by the operating system
- Preserve child process exit codes in this range when wrapping commands

## Language-Specific Guidance

### Bash
```bash
# Success
exit 0

# General failure
exit 1

# Invalid usage
echo "Error: Missing required argument" >&2
echo "Usage: $0 <arg>" >&2
exit 2

# Binary not found
echo "Error: Binary 'tool' not found" >&2
echo "Install: sudo apt install tool" >&2
exit 127

# Preserve child exit code
command
exit $?
```

### Python
```python
import sys

# Success
sys.exit(0)

# General failure
sys.exit(1)

# Invalid usage
print("Error: Missing required argument", file=sys.stderr)
print("Usage: script.py <arg>", file=sys.stderr)
sys.exit(2)

# Binary not found
print("Error: Binary 'tool' not found", file=sys.stderr)
print("Set TOOL_PATH or install tool", file=sys.stderr)
sys.exit(127)

# Preserve child exit code
result = subprocess.run(command)
sys.exit(result.returncode)
```

### Perl
```perl
# Success
exit 0;

# General failure
exit 1;

# Invalid usage
warn "Error: Missing required argument\n";
warn "Usage: $0 <arg>\n";
exit 2;

# Binary not found
warn "Error: Binary 'tool' not found\n";
warn "Set TOOL_PATH or install tool\n";
exit 127;

# Preserve child exit code
system(@command);
exit $? >> 8;
```

### PowerShell
```powershell
# Success
exit 0

# General failure
exit 1

# Invalid usage
Write-Error "Missing required argument"
Write-Host "Usage: script.ps1 <arg>"
exit 2

# Binary not found
Write-Error "Binary 'tool' not found"
Write-Host "Set `$env:TOOL_PATH or install tool"
exit 127

# Preserve child exit code
& command
exit $LASTEXITCODE
```

### Rust
```rust
use std::process;

// Success
process::exit(0);

// General failure
process::exit(1);

// Invalid usage
eprintln!("Error: Missing required argument");
eprintln!("Usage: tool <arg>");
process::exit(2);

// Binary not found
eprintln!("Error: Binary 'tool' not found");
eprintln!("Set TOOL_PATH or install tool");
process::exit(127);

// Preserve child exit code
let status = Command::new("tool").status()?;
process::exit(status.code().unwrap_or(1));
```

## Documentation Requirements

Every script **MUST** document its exit codes in its docstring/documentation:

### Minimum Documentation
At minimum, document:
- Exit code 0 (success)
- Exit code 1 (general failure)

### Recommended Documentation
Additionally document:
- Exit code 2 (if argument parsing can fail)
- Exit code 127 (if binary discovery can fail)
- Any custom exit codes (3-125)

### Example (Bash)
```bash
# OUTPUTS:
#   Exit Codes:
#     0    Success - command completed without errors
#     1    Failure - command execution failed
#     127  Binary not found - cannot locate tool
```

### Example (Python)
```python
"""
Exit Codes
----------
0
    Success - operation completed successfully
1
    General failure - validation errors or runtime failures
2
    Invalid arguments - missing required args or invalid usage
127
    Binary not found - canonical tool not discoverable
"""
```

## Wrapper Script Requirements

Wrapper scripts that invoke canonical tools **MUST**:

1. **Preserve child exit codes**: Exit with the same code as the wrapped command
2. **Use 127 for "not found"**: When binary discovery fails
3. **Use 2 for usage errors**: When wrapper argument parsing fails
4. **Propagate all codes 0-255**: Do not transform or map exit codes from child process

### Example Pattern
```bash
# Find binary
binary=$(find_binary) || exit 127

# Validate arguments
[[ $# -gt 0 ]] || { echo "Usage: $0 <command>" >&2; exit 2; }

# Execute and preserve exit code
"$binary" "$@"
exit $?
```

## Testing Exit Codes

When writing tests for scripts, verify exit codes explicitly:

```bash
# Test success
./script.sh valid-input
assert_exit_code 0

# Test failure
./script.sh invalid-input
assert_exit_code 1

# Test missing argument
./script.sh
assert_exit_code 2

# Test binary not found
BINARY_PATH=/nonexistent ./wrapper.sh command
assert_exit_code 127
```

## References

- POSIX Exit Codes: <https://pubs.opengroup.org/onlinepubs/9699919799/utilities/V3_chap02.html#tag_18_08_02>
- Bash Exit Codes: <https://www.gnu.org/software/bash/manual/html_node/Exit-Status.html>
- Advanced Bash-Scripting Guide: <https://tldp.org/LDP/abs/html/exitcodes.html>
- `docs/docstrings/README.md` - Docstring contract overview
- Individual language contracts in `docs/docstrings/`
