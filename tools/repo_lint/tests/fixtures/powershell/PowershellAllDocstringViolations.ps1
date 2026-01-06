# Missing .SYNOPSIS - violation 1
# Missing .DESCRIPTION - violation 2

# Missing function help - violation 3
function Test-FunctionNoHelp {
    param($Param1)
    Write-Output $Param1
}

# Incomplete help - violation 4
function Test-IncompleteHelp {
    <#
    .SYNOPSIS
    Only has synopsis
    #>
    param($Value)
    return $Value
}

# No help at all - violation 5
function Get-Something {
    "no help"
}
