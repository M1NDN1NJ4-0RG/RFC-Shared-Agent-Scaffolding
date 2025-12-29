<#
.SYNOPSIS
Test fixture with PowerShell edge cases for symbol discovery.

.DESCRIPTION
This script contains various edge cases to test the PowerShell AST parser's
ability to correctly identify and validate function documentation.

Tests include:
- Functions with advanced parameters
- Multiline function signatures
- Functions with various help block formats
- Nested functions
- Functions with special naming patterns

.PARAMETER TestMode
Optional test mode flag for running in test environment

.ENVIRONMENT
PowerShell 5.1 or later (pwsh 7.x recommended)

.EXAMPLE
./edge_cases.ps1
Runs the fixture script

.EXAMPLE
. ./edge_cases.ps1
Sources the script to load functions

.NOTES
This fixture is used for testing the PowerShell validator's symbol discovery.
Exit codes:
0 - Success
1 - Failure
#>

param(
    [Parameter(Mandatory = $false)]
    [switch]$TestMode
)

function Simple-Function {
    <#
    .SYNOPSIS
    Simple function with basic documentation.
    
    .DESCRIPTION
    A straightforward function to test basic symbol discovery.
    
    .PARAMETER InputValue
    The value to process
    
    .EXAMPLE
    Simple-Function -InputValue "test"
    #>
    param(
        [string]$InputValue
    )
    
    Write-Output "Processing: $InputValue"
}

function Multiline-Signature {
    <#
    .SYNOPSIS
    Function with multiline parameter signature.
    
    .DESCRIPTION
    Tests that the parser handles functions with parameters
    spanning multiple lines.
    
    .PARAMETER FirstParam
    First parameter
    
    .PARAMETER SecondParam
    Second parameter
    
    .PARAMETER ThirdParam
    Third parameter with longer name
    
    .EXAMPLE
    Multiline-Signature -FirstParam "a" -SecondParam 42 -ThirdParam $true
    #>
    param(
        [Parameter(Mandatory = $true)]
        [string]$FirstParam,
        
        [Parameter(Mandatory = $true)]
        [int]$SecondParam,
        
        [Parameter(Mandatory = $false)]
        [bool]$ThirdParam = $false
    )
    
    Write-Output "$FirstParam, $SecondParam, $ThirdParam"
}

function Advanced-Parameters {
    <#
    .SYNOPSIS
    Function with advanced parameter features.
    
    .DESCRIPTION
    Demonstrates validation sets, parameter attributes, and
    pipeline input handling.
    
    .PARAMETER ComputerName
    Computer name with validation
    
    .PARAMETER Action
    Action to perform from validation set
    
    .PARAMETER InputObject
    Pipeline input object
    
    .EXAMPLE
    Advanced-Parameters -ComputerName "server01" -Action "Start"
    
    .EXAMPLE
    Get-Item | Advanced-Parameters
    #>
    param(
        [Parameter(Mandatory = $true)]
        [ValidateNotNullOrEmpty()]
        [string]$ComputerName,
        
        [Parameter(Mandatory = $true)]
        [ValidateSet("Start", "Stop", "Restart")]
        [string]$Action,
        
        [Parameter(ValueFromPipeline = $true)]
        [object]$InputObject
    )
    
    process {
        Write-Output "Action: $Action on $ComputerName"
    }
}

function Outer-Function {
    <#
    .SYNOPSIS
    Outer function containing nested function.
    
    .DESCRIPTION
    Tests that the validator correctly identifies and validates
    nested function documentation.
    
    .PARAMETER OuterValue
    Value for outer function
    
    .EXAMPLE
    Outer-Function -OuterValue 42
    #>
    param(
        [int]$OuterValue
    )
    
    function Inner-Function {
        <#
        .SYNOPSIS
        Inner nested function.
        
        .DESCRIPTION
        Nested function inside another function.
        
        .PARAMETER InnerValue
        Value for inner function
        
        .EXAMPLE
        Inner-Function -InnerValue 10
        #>
        param(
            [int]$InnerValue
        )
        
        return $OuterValue + $InnerValue
    }
    
    return Inner-Function -InnerValue 10
}

function Function-With-Special-Chars123 {
    <#
    .SYNOPSIS
    Function with numbers and special characters in name.
    
    .DESCRIPTION
    Tests handling of function names with numbers and hyphens.
    
    .EXAMPLE
    Function-With-Special-Chars123
    #>
    
    Write-Output "Special chars in name"
}

function Private-Helper {
    <#
    .SYNOPSIS
    Private/helper function (private by convention).
    
    .DESCRIPTION
    Per Phase 5.5 policy, private functions must still be documented
    unless explicitly exempted via pragma.
    
    .PARAMETER Value
    Value to process
    
    .EXAMPLE
    Private-Helper -Value "test"
    #>
    param([string]$Value)
    
    return "$Value-processed"
}

function Get-ComplexObject {
    <#
    .SYNOPSIS
    Function returning complex object.
    
    .DESCRIPTION
    Demonstrates function returning hashtable/PSCustomObject.
    
    .PARAMETER Name
    Object name
    
    .PARAMETER Count
    Object count
    
    .OUTPUTS
    System.Collections.Hashtable
    
    .EXAMPLE
    $obj = Get-ComplexObject -Name "test" -Count 5
    #>
    param(
        [string]$Name,
        [int]$Count
    )
    
    return @{
        Name  = $Name
        Count = $Count
        Timestamp = Get-Date
    }
}

function Should-ProcessExample {
    <#
    .SYNOPSIS
    Function with ShouldProcess support.
    
    .DESCRIPTION
    Demonstrates WhatIf and Confirm support.
    
    .PARAMETER Path
    Path to process
    
    .EXAMPLE
    Should-ProcessExample -Path "C:\temp" -WhatIf
    
    .EXAMPLE
    Should-ProcessExample -Path "C:\temp" -Confirm
    #>
    [CmdletBinding(SupportsShouldProcess = $true)]
    param(
        [string]$Path
    )
    
    if ($PSCmdlet.ShouldProcess($Path, "Process")) {
        Write-Output "Processing: $Path"
    }
}

function Begin-Process-End-Blocks {
    <#
    .SYNOPSIS
    Function with begin/process/end blocks.
    
    .DESCRIPTION
    Demonstrates pipeline processing with all three blocks.
    
    .PARAMETER Item
    Item from pipeline
    
    .EXAMPLE
    1..10 | Begin-Process-End-Blocks
    #>
    param(
        [Parameter(ValueFromPipeline = $true)]
        [object]$Item
    )
    
    begin {
        $count = 0
    }
    
    process {
        $count++
        Write-Output "Item $($count): $Item"
    }
    
    end {
        Write-Output "Processed $count items"
    }
}

# Note: PowerShell doesn't have the same noqa pragma syntax
# This function intentionally has no help block for testing
function Undocumented-Function {
    param([string]$Value)
    Write-Output "No docs: $Value"
}

function Dynamic-Parameters {
    <#
    .SYNOPSIS
    Function with dynamic parameters.
    
    .DESCRIPTION
    Demonstrates dynamic parameter creation.
    
    .PARAMETER BaseParam
    Base parameter always present
    
    .EXAMPLE
    Dynamic-Parameters -BaseParam "test"
    #>
    [CmdletBinding()]
    param(
        [string]$BaseParam
    )
    
    dynamicparam {
        $paramDictionary = New-Object System.Management.Automation.RuntimeDefinedParameterDictionary
        
        $attributeCollection = New-Object System.Collections.ObjectModel.Collection[System.Attribute]
        $paramAttribute = New-Object System.Management.Automation.ParameterAttribute
        $paramAttribute.Mandatory = $false
        $attributeCollection.Add($paramAttribute)
        
        $dynamicParam = New-Object System.Management.Automation.RuntimeDefinedParameter(
            'DynamicParam',
            [string],
            $attributeCollection
        )
        
        $paramDictionary.Add('DynamicParam', $dynamicParam)
        return $paramDictionary
    }
    
    process {
        Write-Output "Base: $BaseParam"
    }
}

# Main execution
if ($MyInvocation.InvocationName -ne '.') {
    Write-Output "Running PowerShell edge cases fixture"
    Simple-Function -InputValue "test"
    Get-ComplexObject -Name "example" -Count 5
}
