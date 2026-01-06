# Repo Lint Summary

**Workflow Run:** https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/actions/runs/20753433299
**Timestamp:** 2026-01-06 15:46:48 UTC
**Branch:** 240/merge
**Commit:** 732e9bcd1a97bb34c73dffd625dbf601a4467666

## Job Results

| Job | Status |
|-----|--------|
| Auto-Fix: Black | success |
| Detect Changed Files | success |
| Repo Lint: Python | failure |
| Repo Lint: Bash | failure |
| Repo Lint: PowerShell | skipped |
| Repo Lint: Perl | skipped |
| Repo Lint: YAML | skipped |
| Repo Lint: Rust | success |
| Vector Tests: Conformance | skipped |

## Python Linting Failures

```
🔍 Running repository linters and formatters...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Python Linting
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                        Linting Results                        
                                                               
  Runner              Status    Files   Violations   Duration  
 ───────────────────────────────────────────────────────────── 
  black               ✅ PASS       -            0          -  
  ruff                ✅ PASS       -            0          -  
  pylint              ✅ PASS       -            0          -  
  python-docstrings   ❌ FAIL       -            3          -  
                                                               

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           python-docstrings Failures                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           
  Found 3 violation(s)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                
                                                                                                                              
  File   Line   Message                                                                                                       
 ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── 
  .         -   ❌ Validation FAILED: 2 violation(s) in 1 file(s)                                                             
  .         -   ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/scripts/bootstrap_watch.py     
  .         -   ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/scripts/bootstrap_watch.py:17  
                                                                                                                              

           Summary           
  Total Runners: 4           
    Passed: 3                
    Failed: 1                
  Total Violations: 3        
                             
  Exit Code: 1 (VIOLATIONS)  
                             
```

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
 ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── 
  .         -   ❌ Validation FAILED: 2 violation(s) in 1 file(s)                                                                            
  .         -   ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/scripts/bootstrap-repo-lint-toolchain.sh:196  
  .         -   ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/scripts/bootstrap-repo-lint-toolchain.sh:242  
                                                                                                                                             

           Summary           
  Total Runners: 3           
    Passed: 2                
    Failed: 1                
  Total Violations: 3        
                             
  Exit Code: 1 (VIOLATIONS)  
                             
```

