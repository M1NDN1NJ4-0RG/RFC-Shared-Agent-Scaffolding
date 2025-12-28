# PowerShell Docstring Contract

**Language:** PowerShell (`.ps1`)  
**Canonical style:** Comment-based help using `<# ... #>` blocks

## Purpose

PowerShell scripts in this repository use **comment-based help** to document their purpose, usage, and behavior. This follows PowerShell's built-in help system conventions.

## Required Semantic Sections

Every PowerShell script must include these sections (using PowerShell help keywords):

1. **.SYNOPSIS** - One-line summary
2. **.DESCRIPTION** - What the script does and does NOT do (include exit codes here)
3. **.PARAMETER** - Document each parameter (if applicable)
4. **.ENVIRONMENT** - Environment variables used (custom keyword for this repo)
5. **.EXAMPLE** - Minimum 1 concrete usage example
6. **.NOTES** - Maintainer notes, constraints, sharp edges

### Optional but Recommended Sections

- **.INPUTS** - Input types (required if script accepts pipeline input via `ValueFromPipeline`)
- **.OUTPUTS** - Output types (required if script produces pipeline output)
- **.LINK** - Links to related docs or URLs
- **.EXITCODES** - Dedicated exit codes section (not standard PowerShell, but recommended for clarity)
- **Platform note in .NOTES** - Platform compatibility (Windows/Linux/macOS, PowerShell version) - **Recommended**

### Exit Code Documentation

**Preferred approach:** Use a dedicated `.EXITCODES` section for clarity:

```powershell
.EXITCODES
  0
    Success - operation completed
  1
    Failure - general error
  2
    Invalid arguments
  127
    Command not found
```

**Alternative approach:** Document exit codes in `.DESCRIPTION` or `.NOTES`:

```powershell
.DESCRIPTION
  Does something useful.
  
  Exit Codes:
    0    Success
    1    Failure
```

See [exit-codes-contract.md](./exit-codes-contract.md) for canonical exit code meanings.

## Formatting Rules

### Structure

```powershell
#!/usr/bin/env pwsh
<#
.SYNOPSIS
  script-name.ps1 - One-line summary

.DESCRIPTION
  Detailed description of what the script does.
  Multiple paragraphs are allowed.
  State what it does NOT do if relevant.

  Exit Codes:
    0    Success
    1    General failure
    127  Command not found

.PARAMETER args
  Description of the parameter.
  Type, default value, and constraints.

.ENVIRONMENT
  VAR_NAME
    Description of environment variable and default value.
    Example: SAFE_RUN_BIN overrides binary discovery path.

.EXAMPLE
  PS> .\script-name.ps1 -Param1 value
  Description of what this example does.

.EXAMPLE
  PS> $env:VAR_NAME = "value"; .\script-name.ps1
  Example with environment variable override.

.NOTES
  - Constraint or invariant 1
  - Constraint or invariant 2
  
  Author: <if applicable>
  Version: <if applicable>

.LINK
  https://docs.example.com/reference
#>

param(
    [Parameter()]
    [string[]]$args
)

# Script implementation follows...
```

### Key Rules

1. **Shebang first**: Always start with `#!/usr/bin/env pwsh` for cross-platform compatibility
2. **Help block placement**: Immediately after shebang, before `param()` block
3. **Keywords**: Use `.KEYWORD` format (period prefix, uppercase)
4. **Indentation**: Two spaces for content under keywords
5. **Examples prefix**: Use `PS>` for PowerShell prompt (consistent, platform-neutral)
6. **Environment section**: Use custom `.ENVIRONMENT` keyword (not standard PowerShell, but required for this repo)

## Templates

### Minimal Template

```powershell
#!/usr/bin/env pwsh
<#
.SYNOPSIS
  script-name.ps1 - One-line summary of what this script does

.DESCRIPTION
  Detailed description of behavior.
  
  Exit Codes:
    0    Success
    1    Failure

.PARAMETER Command
  The command to execute.

.ENVIRONMENT
  ENV_VAR
    Description of environment variable (default: value)

.EXAMPLE
  PS> .\script-name.ps1 -Command "echo hello"
  Executes the specified command.

.NOTES
  - Important constraint or note for maintainers
#>

param(
    [Parameter(Mandatory=$false)]
    [string[]]$Command
)

# Script implementation follows...
```

### Full Template (with optional sections)

```powershell
#!/usr/bin/env pwsh
<#
.SYNOPSIS
  script-name.ps1 - One-line summary of what this script does

.DESCRIPTION
  Detailed description of what the script does.
  
  State what it does NOT do if relevant for clarity.
  
  Binary Discovery Order (for wrappers):
    1. BIN_PATH environment variable (if set and valid)
    2. ./path/to/dev/binary.exe (dev mode, relative to repo root)
    3. ./dist/<os>/<arch>/binary.exe (CI artifacts)
    4. PATH lookup (system installation)
    5. Error with installation instructions (exit 127)
  
  Exit Codes:
    0      Success
    1      General failure
    2      Invalid arguments
    127    Binary not found

.PARAMETER Command
  The command to execute with optional arguments.
  Type: string[]
  Default: None (required)

.PARAMETER Verbose
  Enable verbose logging output.
  Type: switch
  Default: $false

.ENVIRONMENT
  ENV_VAR_1
    Description of first environment variable.
    Default: value1
    Example: Override binary path for testing.

  ENV_VAR_2
    Description of second environment variable.
    Default: value2

.EXAMPLE
  PS> .\script-name.ps1 -Command "echo", "hello"
  Basic usage with simple command.

.EXAMPLE
  PS> $env:ENV_VAR_1 = "custom"; .\script-name.ps1 -Command "test"
  Usage with environment override.

.EXAMPLE
  PS> .\script-name.ps1 -Command "node", "script.js" -Verbose
  Execute with verbose logging enabled.

.INPUTS
  None. This script does not accept pipeline input.

.OUTPUTS
  None. Output is written to stdout/stderr by the executed command.

.NOTES
  - Do not modify discovery order without updating docs
  - Exit codes must match canonical tool behavior
  - Always preserve child process exit codes
  
  Platform: Windows, Linux, macOS (PowerShell Core 7.0+)
  Version: 1.0.0

.LINK
  https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding
  docs/architecture/wrapper-discovery.md
  docs/usage/conformance-contract.md
#>

param(
    [Parameter(Mandatory=$true, Position=0)]
    [string[]]$Command,
    
    [Parameter(Mandatory=$false)]
    [switch]$Verbose
)

# Script implementation follows...
```

## Examples (Existing Files)

### Example 1: Wrapper Script
**File:** `wrappers/scripts/powershell/scripts/safe-run.ps1`

This file demonstrates:
- Full comment-based help with all required sections
- Custom `.ENVIRONMENT` keyword
- Binary discovery order documentation
- Multiple `.EXAMPLE` blocks with varied scenarios
- `.NOTES` with platform and version info

### Example 2: Test Script
**File:** `wrappers/scripts/powershell/tests/safe-run-tests.ps1`

This file demonstrates:
- Minimal docstring for test scripts
- Clear `.DESCRIPTION` of test scope
- `.EXAMPLE` showing how to run tests
- `.NOTES` with test framework info

### Example 3: Utility Script
**File:** `wrappers/scripts/powershell/scripts/safe-check.ps1`

This file demonstrates:
- `.DESCRIPTION` that states what it does NOT do
- `.PARAMETER` for each accepted parameter
- `.ENVIRONMENT` with multiple variables
- Exit codes documented in `.DESCRIPTION`

## Validation

The validator checks for:
- Presence of `<# ... #>` help block starting within first 10 lines
- Presence of section keywords: `.SYNOPSIS`, `.DESCRIPTION`, `.ENVIRONMENT`, `.EXAMPLE`, `.NOTES`
- At least one `.EXAMPLE` block

The validator does NOT check:
- Content quality or accuracy
- Parameter documentation completeness (though all parameters should be documented)
- `.INPUTS`/`.OUTPUTS` presence (these are optional unless script uses pipeline)
- Help system compatibility with `Get-Help`
- Grammar or spelling
- Exit code completeness (but basic content checks apply if using validator --content-checks)

**Validation Best Practices:**
- Run validator locally before committing: `python3 scripts/validate-docstrings.py --file my-script.ps1`
- Test help system integration: `Get-Help .\my-script.ps1 -Detailed`
- If using pipeline parameters, add `.INPUTS` and `.OUTPUTS` sections
- Document all parameters with `.PARAMETER` blocks
- Use pragma comments for intentional omissions: `# noqa: PARAMETER`

## Common Mistakes

❌ **Wrong:** Missing .ENVIRONMENT section
```powershell
<#
.SYNOPSIS
  Script does something

.DESCRIPTION
  Detailed description

.EXAMPLE
  .\script.ps1
#>
```

✅ **Correct:** Include .ENVIRONMENT even if no env vars used
```powershell
<#
.SYNOPSIS
  Script does something

.DESCRIPTION
  Detailed description

.ENVIRONMENT
  None. This script does not use environment variables.

.EXAMPLE
  .\script.ps1

.NOTES
  - Important note
#>
```

❌ **Wrong:** No exit code documentation
```powershell
.DESCRIPTION
  This script processes files
```

✅ **Correct:** Document exit codes
```powershell
.DESCRIPTION
  This script processes files.
  
  Exit Codes:
    0    Success
    1    Failure
```

❌ **Wrong:** Missing PS> prompt in examples
```powershell
.EXAMPLE
  .\script.ps1 arg
```

✅ **Correct:** Include PS> prompt
```powershell
.EXAMPLE
  PS> .\script.ps1 arg
  Executes with argument.
```

## PowerShell Help System Integration

Scripts following this contract are compatible with PowerShell's built-in help system:

```powershell
# Get help for a script
Get-Help .\script-name.ps1

# Get detailed help
Get-Help .\script-name.ps1 -Detailed

# Get examples only
Get-Help .\script-name.ps1 -Examples

# Get full help including parameter details
Get-Help .\script-name.ps1 -Full
```

## References

- [README.md](./README.md) - Overview of docstring contracts
- [exit-codes-contract.md](./exit-codes-contract.md) - Canonical exit code meanings
- [PowerShell Comment-Based Help](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_comment_based_help)
- [Wrapper Discovery](../../architecture/wrapper-discovery.md) - Binary discovery rules for wrappers
- [Conformance Contract](../../usage/conformance-contract.md) - Behavior contract
