# PowerShell test fixtures for repo_lint docstring validation
#
# Purpose: Test missing docstrings, correct docstrings, pragma exemptions,
# and edge cases for PowerShell symbol discovery via AST.

<#
.SYNOPSIS
    Function with proper documentation.
.DESCRIPTION
    This function has a proper PowerShell comment-based help block.
#>
function FunctionWithDoc {
    Write-Output "ok"
}

function FunctionWithoutDoc {
    # Missing docstring - should be detected
    Write-Output "missing"
}

<#
.SYNOPSIS
    Multiline parameter function.
.DESCRIPTION
    Function with properly documented parameters.
.PARAMETER Arg1
    First argument.
.PARAMETER Arg2
    Second argument.
#>
function MultilineFunction {
    param(
        [string]$Arg1,
        [string]$Arg2
    )
    Write-Output "$Arg1 $Arg2"
}

# noqa: FUNCTION
function ExemptedFunction {
    Write-Output "pragma exemption"
}
