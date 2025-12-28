# Bash Docstring Contract

**Language:** Bash (`.sh`, `.bash`, `.zsh`)  
**Canonical style:** Top-of-file comment block using `#` prefix

## Purpose

Bash scripts in this repository use a **top-of-file comment header** to document their purpose, usage, and behavior. This contract defines the required sections and formatting rules.

## Required Semantic Sections

Every Bash script must include these sections (case-insensitive, but conventionally UPPERCASE):

1. **Script name and summary** - First line after shebang: `# script-name.sh - One-line summary`
2. **DESCRIPTION:** - What the script does and does NOT do
3. **USAGE:** - Invocation pattern with examples
4. **INPUTS:** - Arguments and environment variables (if applicable)
5. **OUTPUTS:** - Exit codes, stdout/stderr behavior, side effects
6. **EXAMPLES:** - Minimum 1 concrete usage example
7. **NOTES:** - Maintainer notes, constraints, sharp edges (if applicable)

### Optional Sections

- **PLATFORM COMPATIBILITY:** - Tested platforms, version requirements - **Recommended**
- **CONTRACT REFERENCES:** - Links to design docs, RFCs
- **BINARY DISCOVERY ORDER:** - For wrapper scripts that discover tools

## Formatting Rules

### Structure

```bash
#!/usr/bin/env bash
#
# script-name.sh - One-line summary
#
# DESCRIPTION:
#   Detailed description of what the script does.
#   Multiple paragraphs are allowed.
#   State what it does NOT do if relevant.
#
# USAGE:
#   script-name.sh [options] <args>
#   script-name.sh --help
#
# INPUTS:
#   Arguments:
#     arg1        Description of positional argument
#     --option    Description of option flag
#
#   Environment Variables:
#     VAR_NAME    Description and default value
#
# OUTPUTS:
#   Exit Codes:
#     0    Success
#     1    General failure
#     127  Command not found
#
#   Stdout/Stderr:
#     Success: Output description
#     Failure: Error message description
#
#   Side Effects:
#     Files created, modified, or deleted
#
# EXAMPLES:
#   # Example 1: Basic usage
#   script-name.sh arg1
#
#   # Example 2: With environment override
#   VAR_NAME=value script-name.sh arg1
#
# NOTES:
#   - Constraint or invariant 1
#   - Constraint or invariant 2
```

### Key Rules

1. **Shebang first**: Always start with `#!/usr/bin/env bash`
2. **Blank line separator**: One blank comment line (`#`) after shebang
3. **Section headers**: All-caps followed by colon (e.g., `DESCRIPTION:`)
4. **Indentation**: Two spaces for subsections and content
5. **Examples prefix**: Use `#` for example commands (shell comment style)
6. **Line length**: Aim for 80 characters per line for readability (soft limit)
7. **Exit codes**: Always document at least codes 0 and 1 in OUTPUTS section (see [exit-codes-contract.md](./exit-codes-contract.md))

## Templates

### Minimal Template

```bash
#!/usr/bin/env bash
#
# script-name.sh - One-line summary of what this script does
#
# DESCRIPTION:
#   Detailed description of behavior.
#
# USAGE:
#   script-name.sh <command> [args...]
#
# INPUTS:
#   Arguments:
#     command    The command to execute
#
#   Environment Variables:
#     ENV_VAR    Description (default: value)
#
# OUTPUTS:
#   Exit Codes:
#     0    Success
#     1    Failure
#
#   Side Effects:
#     Describe any files created or modified
#
# EXAMPLES:
#   # Basic usage
#   script-name.sh echo "hello"
#
# NOTES:
#   - Important constraint or note for maintainers

set -euo pipefail

# Script implementation follows...
```

### Full Template (with optional sections)

```bash
#!/usr/bin/env bash
#
# script-name.sh - One-line summary of what this script does
#
# DESCRIPTION:
#   Detailed description of what the script does.
#   
#   State what it does NOT do if relevant for clarity.
#
# USAGE:
#   script-name.sh [options] <command> [args...]
#   script-name.sh --help
#
# INPUTS:
#   Arguments:
#     command        The command to execute
#     args           Arguments passed to command
#     --help         Show usage information
#
#   Environment Variables:
#     ENV_VAR_1      Description (default: value)
#     ENV_VAR_2      Another variable description
#
# OUTPUTS:
#   Exit Codes:
#     0      Success
#     1      General failure
#     127    Command not found
#
#   Stdout/Stderr:
#     Success: Command output passed through
#     Failure: Error message with context
#
#   Side Effects:
#     Creates log files in LOG_DIR on failure
#     Format: YYYYMMDDTHHMMSSZ-pid<N>-FAIL.log
#
# BINARY DISCOVERY ORDER:
#   1. BIN_PATH env var (if set)
#   2. ./path/to/dev/binary
#   3. ./dist/<os>/<arch>/binary
#   4. PATH lookup
#   5. Error with instructions (exit 127)
#
# PLATFORM COMPATIBILITY:
#   - Linux: Tested on Ubuntu 20.04+, requires Bash 4.0+
#   - macOS: Compatible with Bash 3.2+ (macOS default)
#   - Windows: Works via Git Bash, WSL, or MSYS2
#
# EXAMPLES:
#   # Example 1: Basic usage
#   script-name.sh echo "hello world"
#
#   # Example 2: With environment override
#   ENV_VAR_1=custom script-name.sh ls -la
#
#   # Example 3: Binary override
#   BIN_PATH=/custom/path script-name.sh test
#
# CONTRACT REFERENCES:
#   - Wrapper discovery: docs/wrapper-discovery.md
#   - Output contract: docs/conformance-contract.md
#
# NOTES:
#   - Do not modify discovery order without updating docs
#   - Exit codes must match canonical tool behavior
#   - Always preserve child process exit codes

set -euo pipefail

# Script implementation follows...
```

## Examples (Existing Files)

### Example 1: Wrapper Script
**File:** `wrappers/scripts/bash/scripts/safe-run.sh`

This file demonstrates:
- Full docstring with all required sections
- BINARY DISCOVERY ORDER (wrapper-specific)
- PLATFORM COMPATIBILITY section
- CONTRACT REFERENCES
- Multiple examples with environment overrides

### Example 2: Test Script
**File:** `wrappers/scripts/bash/tests/test-safe-run.sh`

This file demonstrates:
- Minimal docstring for test scripts
- Clear DESCRIPTION of test scope
- Simple USAGE pattern
- Exit code documentation

### Example 3: Utility Script
**File:** `wrappers/scripts/bash/scripts/safe-check.sh`

This file demonstrates:
- DESCRIPTION that states what it does NOT do
- INPUTS with both arguments and environment variables
- OUTPUTS with multiple exit codes documented

## Validation

The validator checks for:
- Presence of comment block starting within first 10 lines
- Presence of section keywords: `DESCRIPTION:`, `USAGE:`, `INPUTS:`, `OUTPUTS:`, `EXAMPLES:`
- At least one `#` example line under EXAMPLES section

The validator does NOT check:
- Content quality or accuracy
- Indentation consistency
- Grammar or spelling

## Common Mistakes

❌ **Wrong:** Missing colon after section name
```bash
# DESCRIPTION
#   This script does something
```

✅ **Correct:** Include colon
```bash
# DESCRIPTION:
#   This script does something
```

❌ **Wrong:** No shebang or wrong shebang
```bash
#!/bin/bash
```

✅ **Correct:** Use `env` for portability
```bash
#!/usr/bin/env bash
```

❌ **Wrong:** Missing Exit Codes in OUTPUTS
```bash
# OUTPUTS:
#   Creates log files
```

✅ **Correct:** Always document exit codes
```bash
# OUTPUTS:
#   Exit Codes:
#     0    Success
#     1    Failure
```

## References

- [README.md](./README.md) - Overview of docstring contracts
- [exit-codes-contract.md](./exit-codes-contract.md) - Canonical exit code meanings
- [Wrapper Discovery](../wrapper-discovery.md) - Binary discovery rules for wrappers
- [Conformance Contract](../conformance-contract.md) - Behavior contract
