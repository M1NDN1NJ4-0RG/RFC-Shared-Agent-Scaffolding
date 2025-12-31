# Repo Lint Summary

**Workflow Run:** https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/actions/runs/20624768826
**Timestamp:** 2025-12-31 18:23:46 UTC
**Branch:** 202/merge
**Commit:** 4b48b954dbab2b19b1240e0a4075ca02f42c15ab

## Job Results

| Job | Status |
|-----|--------|
| Auto-Fix: Black | success |
| Detect Changed Files | success |
| Repo Lint: Python | success |
| Repo Lint: Bash | failure |
| Repo Lint: PowerShell | success |
| Repo Lint: Perl | success |
| Repo Lint: YAML | success |
| Repo Lint: Rust | success |
| Vector Tests: Conformance | success |

## Bash Linting Failures

```
🔍 Running repository linters and formatters...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Bash Linting
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                         Linting Results                         
                                                                 
  Runner                Status    Files   Violations   Duration  
 ─────────────────────────────────────────────────────────────── 
  shellcheck            ✅ PASS       -            0          -  
  shfmt                 ✅ PASS       -            0          -  
  validate_docstrings   ❌ FAIL       -           18          -  
                                                                 

                          validate_docstrings Failures                          
  Found 18 violation(s)                                                         
                                                                                
                                                                                
  File   Line   Message                                                         
 ────────────────────────────────────────────────────────────────────────────── 
  .         -   ❌ Validation FAILED: 17 violation(s) in 2 file(s)              
  .         -   ❌                                                              
                /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Age…  
  .         -   ❌                                                              
                /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Age…  
  .         -   ❌                                                              
                /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Age…  
  .         -   ❌                                                              
                /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Age…  
  .         -   ❌                                                              
                /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Age…  
  .         -   ❌                                                              
                /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Age…  
  .         -   ❌                                                              
                /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Age…  
  .         -   ❌                                                              
                /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Age…  
  .         -   ❌                                                              
                /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Age…  
  .         -   ❌                                                              
                /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Age…  
  .         -   ❌                                                              
                /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Age…  
  .         -   ❌                                                              
                /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Age…  
  .         -   ❌                                                              
                /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Age…  
  .         -   ❌                                                              
                /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Age…  
  .         -   ❌                                                              
                /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Age…  
  .         -   ❌                                                              
                /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Age…  
  .         -   ❌                                                              
                /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Age…  
                                                                                

                                    Summary                                     
  Total Runners: 3                                                              
    Passed: 2                                                                   
    Failed: 1                                                                   
  Total Violations: 18                                                          
                                                                                
  Exit Code: 1 (VIOLATIONS)                                                     
                                                                                
```

