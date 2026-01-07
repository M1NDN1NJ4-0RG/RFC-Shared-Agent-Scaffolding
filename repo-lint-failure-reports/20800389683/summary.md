# Repo Lint Summary

**Workflow Run:** https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/actions/runs/20800389683
**Timestamp:** 2026-01-07 23:52:51 UTC
**Branch:** 285/merge
**Commit:** 4d7043848b49777f7cf38953a0c6b86a382418c6

## Job Results

| Job | Status |
|-----|--------|
| Auto-Fix: Black | success |
| Detect Changed Files | success |
| Repo Lint: Python | failure |
| Repo Lint: Bash | success |
| Repo Lint: PowerShell | success |
| Repo Lint: Perl | success |
| Repo Lint: YAML | failure |
| Repo Lint: Rust | success |
| Vector Tests: Conformance | success |

## Python Linting Failures

```
🔍 Running repository linters and formatters...


                        Linting Results                        
                                                               
  Runner              Status    Files   Violations   Duration  
 ───────────────────────────────────────────────────────────── 
  black               ✅ PASS       -            0          -  
  ruff                ❌ FAIL       -            1          -  
  pylint              ✅ PASS       -            0          -  
  python-docstrings   ✅ PASS       -            0          -  
                                                               

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 ruff Failures                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  
  Found 1 violation(s)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                
                                                                                             
  File              Line   Message                                                           
 ─────────────────────────────────────────────────────────────────────────────────────────── 
  cli_argparse.py    557   N806 Variable `MAX_AUTO_WORKERS` in function should be lowercase  
                                                                                             

           Summary           
  Total Runners: 4           
    Passed: 3                
    Failed: 1                
  Total Violations: 1        
                             
  Exit Code: 1 (VIOLATIONS)  
                             
```

## YAML Linting Failures

```
🔍 Running repository linters and formatters...


                       Linting Results                       
                                                             
  Runner            Status    Files   Violations   Duration  
 ─────────────────────────────────────────────────────────── 
  yamllint          ✅ PASS       -            0          -  
  yaml-docstrings   ❌ FAIL       -            2          -  
                                                             

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            yaml-docstrings Failures                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            
  Found 2 violation(s)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                
                                                                                                                                          
  File   Line   Message                                                                                                                   
 ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── 
  .         -   ❌ Validation FAILED: 1 violation(s) in 1 file(s)                                                                         
  .         -   ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/.github/workflows/copilot-setup-steps.yml  
                                                                                                                                          

           Summary           
  Total Runners: 2           
    Passed: 1                
    Failed: 1                
  Total Violations: 2        
                             
  Exit Code: 1 (VIOLATIONS)  
                             
```

