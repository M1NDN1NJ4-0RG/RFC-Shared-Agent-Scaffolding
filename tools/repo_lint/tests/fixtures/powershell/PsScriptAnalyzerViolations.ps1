# Test fixture for PSScriptAnalyzer violations

# PSAvoidUsingCmdletAliases: use full cmdlet names
gci | % { Write-Output $_ }

# PSAvoidUsingPositionalParameters: use named parameters
Get-ChildItem C:\temp -Recurse

# PSAvoidUsingPlainTextForPassword: don't use plain text passwords
$password = "MyPassword123"
$securePassword = ConvertTo-SecureString $password -AsPlainText -Force

# PSUseDeclaredVarsMoreThanAssignments: variable assigned but never used
$unusedVar = "not used"

# PSUseShouldProcessForStateChangingFunctions: missing ShouldProcess
# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
function Remove-CustomItem {
    param([string]$Path)
    Remove-Item $Path
}

# PSAvoidGlobalVars: avoid global variables
$global:MyGlobal = "value"

# PSUseSingularNouns: cmdlet nouns should be singular
# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
function Get-Items {
    param()
    Get-ChildItem
}

# PSProvideCommentHelp: missing comment-based help
# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
function Invoke-Something {
    param([string]$Name)
    Write-Output "Hello $Name"
}

# PSAvoidDefaultValueForMandatoryParameter: mandatory param with default
# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
function Test-Function {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Required = "default"
    )
}

# PSReservedCmdletChar: invalid characters in cmdlet name
# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
function Get-My_Item {
    param()
}

# PSAvoidUsingWriteHost: use Write-Output instead
# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
function Show-Message {
    Write-Host "This is a message"
}

# PSAvoidUsingInvokeExpression: dangerous use of Invoke-Expression
$cmd = "Get-Process"
Invoke-Expression $cmd

# PSUsePSCredentialType: use PSCredential instead of string
# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
function Connect-System {
    param(
        [string]$Username,
        [string]$Password
    )
}

# PSAvoidTrailingWhitespace: lines with trailing spaces
$text = "line with spaces"   

# PSAvoidUsingComputerNameHardcoded: hardcoded computer names
$server = "SERVER01"
Invoke-Command -ComputerName "PROD-SERVER" -ScriptBlock {}

# PSPossibleIncorrectComparisonWithNull: null check on wrong side
if ($null -eq $variable) { }

# PSUseApprovedVerbs: use approved verbs only
# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
function Do-Something {
    param()
}

# PSUseCmdletCorrectly: incorrect usage
Get-Process | Out-Null | Where-Object {$_.Name -eq "test"}

# PSAvoidUsingDeprecatedManifestFields: deprecated keys
# (would be in .psd1 module manifest)

# PSUseBOMForUnicodeEncodedFile: missing BOM for Unicode
# (encoding issue)

# PSMissingModuleManifestField: missing required fields
# (would be in .psd1)

# PSAvoidLongLines: lines exceeding recommended length
$veryLongVariable = "This is an extremely long line that exceeds the recommended maximum line length and should trigger a PSScriptAnalyzer warning about line length"

# PSAvoidDefaultValueSwitchParameter: switch param should not have default
# INTENTIONAL VIOLATION - FOR TESTING ONLY - NOT FOR REVIEW
function Test-Switch {
    param(
        [switch]$Enable = $true
    )
}
