#requires -Version 5.1
Set-StrictMode -Version Latest

Describe "preflight_automerge_ruleset.ps1" {
  BeforeAll {
    . "$PSScriptRoot/TestHelpers.ps1"
    $script:ScriptUnderTest = Join-Path $PSScriptRoot "..\scripts\powershell\preflight_automerge_ruleset.ps1"
  }

  It "fails when no --repo is provided" {
    & pwsh -NoProfile -File $ScriptUnderTest
    $LASTEXITCODE | Should -Be 3  # M0-P2-I2: Usage/validation error
  }

  It "fails when gh is not available and no token is provided" {
    $td = New-TempDir
    Push-Location $td
    try {
      # Ensure gh is not found by masking PATH (best effort)
      $old = $env:PATH
      $env:PATH = $td
      Remove-Item env:TOKEN -ErrorAction SilentlyContinue
      Remove-Item env:GITHUB_TOKEN -ErrorAction SilentlyContinue

      & pwsh -NoProfile -File $ScriptUnderTest -Repo "o/r" -RulesetName "Main" -Want '["lint"]'
      $LASTEXITCODE | Should -Be 2
    } finally {
      $env:PATH = $old
      Pop-Location
    }
  }

  It "passes when ruleset matches want and enforcement is enabled (gh path)" {
    $td = New-TempDir
    Push-Location $td
    try {
      $fixture = @"
{
  "total_count": 1,
  "rulesets": [
    {
      "id": 123,
      "name": "Main - PR Only + Green CI",
      "target": "branch",
      "enforcement": "active",
      "conditions": {"ref_name": {"include": ["refs/heads/main"]}},
      "rules": [
        {
          "type": "required_status_checks",
          "parameters": {
            "required_status_checks": [
              {"context": "lint"},
              {"context": "test"}
            ],
            "strict_required_status_checks_policy": true
          }
        }
      ]
    }
  ]
}
"@
      Add-FakeGhToPath -FixtureJson $fixture -OutDir $td | Out-Null

      & pwsh -NoProfile -File $ScriptUnderTest -Repo "o/r" -RulesetName "Main - PR Only + Green CI" -Want '["lint","test"]'
      $LASTEXITCODE | Should -Be 0
    } finally {
      Pop-Location
    }
  }

  It "fails when required checks are missing (gh path)" {
    $td = New-TempDir
    Push-Location $td
    try {
      $fixture = @"
{
  "total_count": 1,
  "rulesets": [
    {
      "id": 123,
      "name": "Main - PR Only + Green CI",
      "target": "branch",
      "enforcement": "active",
      "conditions": {"ref_name": {"include": ["refs/heads/main"]}},
      "rules": [
        {
          "type": "required_status_checks",
          "parameters": {
            "required_status_checks": [
              {"context": "lint"}
            ],
            "strict_required_status_checks_policy": true
          }
        }
      ]
    }
  ]
}
"@
      Add-FakeGhToPath -FixtureJson $fixture -OutDir $td | Out-Null

      & pwsh -NoProfile -File $ScriptUnderTest -Repo "o/r" -RulesetName "Main - PR Only + Green CI" -Want '["lint","test"]'
      $LASTEXITCODE | Should -Be 3
    } finally {
      Pop-Location
    }
  }

  It "fails when enforcement is not active" {
    $td = New-TempDir
    Push-Location $td
    try {
      $fixture = @"
{
  "total_count": 1,
  "rulesets": [
    {
      "id": 123,
      "name": "Main - PR Only + Green CI",
      "target": "branch",
      "enforcement": "evaluate",
      "conditions": {"ref_name": {"include": ["refs/heads/main"]}},
      "rules": [
        {
          "type": "required_status_checks",
          "parameters": {
            "required_status_checks": [
              {"context": "lint"},
              {"context": "test"}
            ],
            "strict_required_status_checks_policy": true
          }
        }
      ]
    }
  ]
}
"@
      Add-FakeGhToPath -FixtureJson $fixture -OutDir $td | Out-Null

      & pwsh -NoProfile -File $ScriptUnderTest -Repo "o/r" -RulesetName "Main - PR Only + Green CI" -Want '["lint","test"]'
      $LASTEXITCODE | Should -Be 3
    } finally {
      Pop-Location
    }
  }
}
