<#
.SYNOPSIS
    Test script with PSScriptAnalyzer violations

.DESCRIPTION
    This script intentionally contains PSScriptAnalyzer rule violations

.NOTES
    For testing purposes only
#>

# Violation 1: PSUseDeclaredVarsMoreThanAssignments - variable assigned but never used
$UnusedVariable = "never used"

# Violation 2: PSAvoidUsingCmdletAliases - using alias instead of full cmdlet name
function Test-Aliases {
    <#
    .SYNOPSIS
        Test function with aliases
    #>
    gci C:\  # Should use Get-ChildItem
}

# Violation 3: PSAvoidUsingPositionalParameters - should use named parameters
function Test-PositionalParams {
    <#
    .SYNOPSIS
        Test function with positional parameter usage
    #>
    Get-ChildItem C:\ *.txt  # Should use -Path and -Filter
}

# Violation 4: PSUseShouldProcessForStateChangingFunctions - Remove-* should support ShouldProcess
function Remove-TestItem {
    <#
    .SYNOPSIS
        Remove function without ShouldProcess support
    #>
    param($Path)
    Remove-Item $Path
}
