<#
.SYNOPSIS
Parse PowerShell script and extract function/symbol information using native AST.

.DESCRIPTION
This script uses PowerShell's native AST parser ([System.Management.Automation.Language.Parser]::ParseFile)
to extract symbol information from PowerShell scripts WITHOUT executing them.

Outputs JSON with function/command definitions and their locations for docstring validation.

.PARAMETER FilePath
Path to PowerShell script file to parse

.ENVIRONMENT
PowerShell 5.1 or later (pwsh 7.x recommended)

.EXAMPLE
pwsh -NoProfile -NonInteractive -File parse_powershell_ast.ps1 -FilePath script.ps1

.NOTES
Per Phase 0 Item 0.9.3: PowerShell symbol discovery MUST use Parser::ParseFile (C1)
Parser::ParseInput (C2) may be used ONLY in unit tests/fixtures

Output format:
{
  "functions": [
    {
      "name": "FunctionName",
      "line": 10,
      "has_help": true,
      "help_sections": [".SYNOPSIS", ".DESCRIPTION"]
    }
  ],
  "errors": []
}

Exit codes:
0 - Success (valid JSON output)
1 - Parse error or file not found
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$FilePath
)

# Ensure file exists
if (-not (Test-Path $FilePath)) {
    $errorObj = @{
        functions = @()
        errors = @("File not found: $FilePath")
    }
    Write-Output ($errorObj | ConvertTo-Json -Depth 10)
    exit 1
}

try {
    # Parse file using Parser::ParseFile (C1 - required by Phase 0 Item 0.9.3)
    # This parses the file WITHOUT executing it
    $tokens = $null
    $errors = $null
    $ast = [System.Management.Automation.Language.Parser]::ParseFile(
        $FilePath,
        [ref]$tokens,
        [ref]$errors
    )

    # Collect parse errors if any
    $parseErrors = @()
    if ($errors) {
        foreach ($err in $errors) {
            $parseErrors += "Line $($err.Extent.StartLineNumber): $($err.Message)"
        }
    }

    # Extract function definitions
    $functions = @()
    $functionDefs = $ast.FindAll({
        param($node)
        $node -is [System.Management.Automation.Language.FunctionDefinitionAst]
    }, $true)

    foreach ($func in $functionDefs) {
        $funcName = $func.Name
        $funcLine = $func.Extent.StartLineNumber

        # Check for comment-based help
        $hasHelp = $false
        $helpSections = @()

        # Look for comment help blocks in the function body
        $helpInfo = $func.GetHelpContent()
        if ($helpInfo) {
            $hasHelp = $true
            # Extract which sections are present
            if ($helpInfo.Synopsis) { $helpSections += ".SYNOPSIS" }
            if ($helpInfo.Description) { $helpSections += ".DESCRIPTION" }
            if ($helpInfo.Parameters) { $helpSections += ".PARAMETER" }
            if ($helpInfo.Examples) { $helpSections += ".EXAMPLE" }
            if ($helpInfo.Inputs) { $helpSections += ".INPUTS" }
            if ($helpInfo.Outputs) { $helpSections += ".OUTPUTS" }
            if ($helpInfo.Notes) { $helpSections += ".NOTES" }
        }

        $functions += @{
            name = $funcName
            line = $funcLine
            has_help = $hasHelp
            help_sections = $helpSections
        }
    }

    # Output result as JSON
    $result = @{
        functions = $functions
        errors = $parseErrors
    }

    Write-Output ($result | ConvertTo-Json -Depth 10)
    exit 0

} catch {
    $errorObj = @{
        functions = @()
        errors = @("Unhandled exception: $_")
    }
    Write-Output ($errorObj | ConvertTo-Json -Depth 10)
    exit 1
}
