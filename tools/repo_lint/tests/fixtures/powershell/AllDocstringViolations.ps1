# Missing module docstring

# Function without help
function Invoke-NoHelp {
    param([string]$Name)
    Write-Output $Name
}

# Function with incomplete help
function Get-PartialHelp {
    <#
    .SYNOPSIS
    Just a synopsis
    #>
    param(
        [string]$Path,
        [int]$Count
    )
    Write-Output $Path
}

# Missing parameter descriptions
function Test-MissingParams {
    <#
    .SYNOPSIS
    Tests something
    .DESCRIPTION
    Does testing
    #>
    param(
        [string]$Param1,
        [int]$Param2,
        [switch]$Enable
    )
}

# Missing examples
function Invoke-NoExamples {
    <#
    .SYNOPSIS
    Invokes operation
    .PARAMETER Operation
    The operation to invoke
    #>
    param([string]$Operation)
}

# Missing outputs documentation
function Get-NoOutputs {
    <#
    .SYNOPSIS
    Gets something
    #>
    return @{Key="Value"}
}

# Class without documentation
class NoDocClass {
    [string]$Property
    
    NoDocClass() {
        $this.Property = "value"
    }
    
    [void]Method() {
        Write-Output "test"
    }
}

# Method without help
class PartialClass {
    <#
    .SYNOPSIS
    Class with some docs
    #>
    
    [string]$Name
    
    [void]NoDocMethod() {
        Write-Output $this.Name
    }
}

# Missing notes section
function Invoke-Complex {
    <#
    .SYNOPSIS
    Complex operation
    .PARAMETER Data
    Input data
    #>
    param([object]$Data)
    # Complex logic without explanation
    $Data | ForEach-Object { $_ * 2 }
}

# Missing link references
function Get-RelatedInfo {
    <#
    .SYNOPSIS
    Gets related information
    .DESCRIPTION
    Retrieves data from related sources
    #>
}

# Missing inputs documentation
function Process-PipelineInput {
    <#
    .SYNOPSIS
    Processes pipeline input
    #>
    param(
        [Parameter(ValueFromPipeline=$true)]
        [object]$InputObject
    )
    process {
        Write-Output $InputObject
    }
}

# Wrong help format
function Bad-HelpFormat {
    # This is a comment, not proper help
    # Parameters: $Name
    # Returns: string
    param([string]$Name)
    return $Name
}

# Missing component/role/functionality metadata
function Install-CustomComponent {
    <#
    .SYNOPSIS
    Installs a component
    #>
    param([string]$Path)
}
