# Test fixture: intentionally bad PowerShell code

# Function without .SYNOPSIS (violates repo docstring contract)
function FunctionWithoutDocstring {
    param(
        [string]$Param1
    )
    
    Write-Output "Hello"
}

# PSScriptAnalyzer: PSUseShouldProcessForStateChangingFunctions
# This is a warning that won't be auto-fixed
function Remove-Something {
    param([string]$Path)
    Remove-Item $Path
}

# Another function missing docstring
function AnotherFunction {
    return $true
}

# Missing parameter documentation
function PartialDocstring {
    <#
    .SYNOPSIS
    Has synopsis but missing parameter docs
    #>
    param(
        [string]$UndocumentedParam
    )
    Write-Output $UndocumentedParam
}
