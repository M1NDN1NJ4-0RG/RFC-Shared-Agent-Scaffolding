<#
.SYNOPSIS
Intentional naming convention violations for PowerShell.

.DESCRIPTION
This file intentionally violates PowerShell naming conventions.
It uses kebab-case instead of PascalCase to test naming enforcement.
#>

# This file name itself (naming-violations.ps1) violates PascalCase
# Expected: NamingViolations.ps1
# Actual: naming-violations.ps1 (kebab-case - WRONG for PowerShell)

function my-function-name {
    # Function names should be PascalCase with approved verbs (e.g., Get-MyFunction)
    # This uses kebab-case which is wrong
    Write-Host "Wrong naming"
}

$variable_in_snake_case = "wrong"  # Variables should be PascalCase

function Get-NormalFunction {
    # This is correct PascalCase with approved verb
    Write-Host "Correct naming"
}
