# Repo Lint Summary

**Workflow Run:** https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/actions/runs/20761000303
**Timestamp:** 2026-01-06 20:24:28 UTC
**Branch:** 245/merge
**Commit:** 18b9292ad2f7a77d609aa8ac63d2966559bdcfaa

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
                                                             
  Runner            Status    Files   Violations   Duration  
 ─────────────────────────────────────────────────────────── 
  shellcheck        ✅ PASS       -            0          -  
  shfmt             ✅ PASS       -            0          -  
  bash-docstrings   ❌ FAIL       -            3          -  
                                                             

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            bash-docstrings Failures                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            
  Found 3 violation(s)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                
                                                                                                                                   
  File   Line   Message                                                                                                            
 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── 
  .         -   ❌ Validation FAILED: 2 violation(s) in 1 file(s)                                                                  
  .         -   ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/scripts/benchmark-bootstrap.sh:161  
  .         -   ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/scripts/benchmark-bootstrap.sh:179  
                                                                                                                                   

           Summary           
  Total Runners: 3           
    Passed: 2                
    Failed: 1                
  Total Violations: 3        
                             
  Exit Code: 1 (VIOLATIONS)  
                             
```

