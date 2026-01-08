# Repo Lint Summary

**Workflow Run:** https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/actions/runs/20833808235
**Timestamp:** 2026-01-08 22:36:36 UTC
**Branch:** 301/merge
**Commit:** 9d4ee178cefaedf647f36ece4462914d04434408

## Job Results

| Job | Status |
|-----|--------|
| Auto-Fix: Black | success |
| Detect Changed Files | success |
| Repo Lint: Python | failure |
| Repo Lint: Bash | success |
| Repo Lint: PowerShell | success |
| Repo Lint: Perl | success |
| Repo Lint: YAML | success |
| Repo Lint: Rust | success |
| Vector Tests: Conformance | success |

## Python Linting Failures

```
🔍 Running repository linters and formatters...


                        Linting Results                        
                                                               
  Runner              Status    Files   Violations   Duration  
 ───────────────────────────────────────────────────────────── 
  black               ✅ PASS       -            0          -  
  ruff                ✅ PASS       -            0          -  
  pylint              ❌ FAIL       -            8          -  
  python-docstrings   ✅ PASS       -            0          -  
                                                               

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                pylint Failures                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 
  Found 8 violation(s)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                
                                                                                                                                
  File                  Line   Message                                                                                          
 ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── 
  test_json_runner.py    135   W0212: Access to a protected member _run_prettier of a client class (protected-access)           
  test_json_runner.py    158   W0212: Access to a protected member _run_prettier of a client class (protected-access)           
  test_json_runner.py    186   W0212: Access to a protected member _run_prettier of a client class (protected-access)           
  test_json_runner.py    203   W0212: Access to a protected member _parse_prettier_output of a client class (protected-access)  
  test_json_runner.py    222   W0212: Access to a protected member _parse_prettier_output of a client class (protected-access)  
  test_json_runner.py    239   W0212: Access to a protected member _parse_prettier_output of a client class (protected-access)  
  test_json_runner.py    257   W0212: Access to a protected member _parse_prettier_output of a client class (protected-access)  
  test_json_runner.py    279   W0212: Access to a protected member _run_prettier of a client class (protected-access)           
                                                                                                                                

           Summary           
  Total Runners: 4           
    Passed: 3                
    Failed: 1                
  Total Violations: 8        
                             
  Exit Code: 1 (VIOLATIONS)  
                             
```

