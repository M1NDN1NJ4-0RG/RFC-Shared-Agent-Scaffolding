# Repo Lint Summary

**Workflow Run:** https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/actions/runs/20838984733
**Timestamp:** 2026-01-09 02:23:26 UTC
**Branch:** 305/merge
**Commit:** f5bac8fb9743a7d78c7693abbfc41185ce7f3e6f

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
  scripts/validate_docstrings.py                                107   Variable "scripts_dir" missing type annotation (PEP 526)                  
  scripts/validate_docstrings.py                                108   Variable "repo_root" missing type annotation (PEP 526)                    
  tools/repo_lint/__init__.py                                    52   Variable "__version__" missing type annotation (PEP 526)                  
  tools/repo_lint/checkers/__init__.py                           29   Variable "__all__" missing type annotation (PEP 526)                      
  pep526_config.py                                               49   Variable "tomllib" missing type annotation (PEP 526)                      
  cli.py                                                         86   Variable "CONFIG_TYPE_ALLOWED_KEYS" missing type annotation (PEP 526)     
  tools/repo_lint/common.py                                      87   Variable "SUCCESS" missing type annotation (PEP 526)                      
  tools/repo_lint/common.py                                      88   Variable "VIOLATIONS" missing type annotation (PEP 526)                   
  tools/repo_lint/common.py                                      89   Variable "MISSING_TOOLS" missing type annotation (PEP 526)                
  tools/repo_lint/common.py                                      90   Variable "INTERNAL_ERROR" missing type annotation (PEP 526)               
  tools/repo_lint/common.py                                      91   Variable "UNSAFE_VIOLATION" missing type annotation (PEP 526)             
  tools/repo_lint/config_validator.py                            37   Variable "SEMANTIC_VERSION_PATTERN" missing type annotation (PEP 526)     
  tools/repo_lint/config_validator.py                            40   Variable "DEFAULT_ALLOWED_KEYS" missing type annotation (PEP 526)         
  tools/repo_lint/docstrings/__init__.py                         45   Variable "__all__" missing type annotation (PEP 526)                      
  tools/repo_lint/docstrings/bash_validator.py                   40   Variable "helpers_dir" missing type annotation (PEP 526)                  
  tools/repo_lint/docstrings/bash_validator.py                   46   Variable "TREE_SITTER_AVAILABLE" missing type annotation (PEP 526)        
  tools/repo_lint/docstrings/bash_validator.py                   48   Variable "TREE_SITTER_AVAILABLE" missing type annotation (PEP 526)        
  tools/repo_lint/docstrings/bash_validator.py                   58   Variable "REQUIRED_SECTIONS" missing type annotation (PEP 526)            
  tools/repo_lint/docstrings/bash_validator.py                   66   Variable "SECTION_NAMES" missing type annotation (PEP 526)                
  tools/repo_lint/docstrings/common.py                           33   Variable "SKIP_CONTENT_CHECKS" missing type annotation (PEP 526)          
  tools/repo_lint/docstrings/helpers/bash_treesitter.py          34   Variable "TREE_SITTER_AVAILABLE" missing type annotation (PEP 526)        
  tools/repo_lint/docstrings/helpers/bash_treesitter.py          36   Variable "TREE_SITTER_AVAILABLE" missing type annotation (PEP 526)        
  tools/repo_lint/docstrings/perl_validator.py                   46   Variable "REQUIRED_SECTIONS" missing type annotation (PEP 526)            
  tools/repo_lint/docstrings/perl_validator.py                   55   Variable "SECTION_NAMES" missing type annotation (PEP 526)                
  tools/repo_lint/docstrings/powershell_validator.py             46   Variable "REQUIRED_SECTIONS" missing type annotation (PEP 526)            
  tools/repo_lint/docstrings/powershell_validator.py             54   Variable "SECTION_NAMES" missing type annotation (PEP 526)                
  tools/repo_lint/docstrings/python_validator.py                 43   Variable "REQUIRED_SECTIONS" missing type annotation (PEP 526)            
  tools/repo_lint/docstrings/python_validator.py                 50   Variable "SECTION_NAMES" missing type annotation (PEP 526)                
  tools/repo_lint/docstrings/rust_validator.py                   41   Variable "REQUIRED_SECTIONS" missing type annotation (PEP 526)            
  tools/repo_lint/docstrings/rust_validator.py                   47   Variable "EXIT_SECTIONS" missing type annotation (PEP 526)                
  tools/repo_lint/docstrings/rust_validator.py                   49   Variable "SECTION_NAMES" missing type annotation (PEP 526)                
  tools/repo_lint/docstrings/yaml_validator.py                   41   Variable "REQUIRED_SECTIONS" missing type annotation (PEP 526)            
  tools/repo_lint/docstrings/yaml_validator.py                   50   Variable "SECTION_NAMES" missing type annotation (PEP 526)                
  tools/repo_lint/install/install_helpers.py                     44   Variable "_ALL_VERSIONS" missing type annotation (PEP 526)                
  tools/repo_lint/install/install_helpers.py                     45   Variable "PYTHON_TOOLS" missing type annotation (PEP 526)                 
  tools/repo_lint/install/install_helpers.py                     46   Variable "BASH_TOOLS" missing type annotation (PEP 526)                   
  tools/repo_lint/install/install_helpers.py                     47   Variable "POWERSHELL_TOOLS" missing type annotation (PEP 526)             
  tools/repo_lint/install/install_helpers.py                     48   Variable "PERL_TOOLS" missing type annotation (PEP 526)                   
  version_pins.py                                                41   Variable "PIP_VERSION" missing type annotation (PEP 526)                  
  base.py                                                        49   Variable "logger" missing type annotation (PEP 526)                       
  test_base_runner.py                                            53   Variable "repo_root" missing type annotation (PEP 526)                    
  test_bash_runner.py                                            56   Variable "repo_root" missing type annotation (PEP 526)                    
  test_bash_validator.py                                         54   Variable "repo_root" missing type annotation (PEP 526)                    
  test_cli_dispatch.py                                           60   Variable "repo_root" missing type annotation (PEP 526)                    
  test_exit_codes.py                                             66   Variable "repo_root" missing type annotation (PEP 526)                    
  tools/repo_lint/tests/test_fixture_isolation_matrix.py         72   Variable "REPO_ROOT" missing type annotation (PEP 526)                    
  tools/repo_lint/tests/test_fixture_isolation_matrix.py         73   Variable "FIXTURE_DIR" missing type annotation (PEP 526)                  
  tools/repo_lint/tests/test_fixture_vector_mode.py              43   Variable "REPO_ROOT" missing type annotation (PEP 526)                    
  tools/repo_lint/tests/test_fixture_vector_mode.py              44   Variable "FIXTURES_DIR" missing type annotation (PEP 526)                 
  tools/repo_lint/tests/test_install_helpers.py                  58   Variable "repo_root" missing type annotation (PEP 526)                    
  tools/repo_lint/tests/test_install_helpers.py                  73   Variable "PYTHON_TOOLS" missing type annotation (PEP 526)                 
  test_integration.py                                            59   Variable "repo_root" missing type annotation (PEP 526)                    
  test_json_runner.py                                            58   Variable "repo_root" missing type annotation (PEP 526)                    
  test_markdown_runner.py                                        57   Variable "repo_root" missing type annotation (PEP 526)                    
  test_output_format.py                                          62   Variable "repo_root" missing type annotation (PEP 526)                    
  test_perl_runner.py                                            56   Variable "repo_root" missing type annotation (PEP 526)                    
  test_perl_validator.py                                         54   Variable "repo_root" missing type annotation (PEP 526)                    
  test_phase_2_7_features.py                                     58   Variable "repo_root" missing type annotation (PEP 526)                    
  test_powershell_runner.py                                      57   Variable "repo_root" missing type annotation (PEP 526)                    
  test_powershell_validator.py                                   54   Variable "repo_root" missing type annotation (PEP 526)                    
  test_python_runner.py                                          57   Variable "repo_root" missing type annotation (PEP 526)                    
  test_python_validator.py                                       57   Variable "repo_root" missing type annotation (PEP 526)                    
  test_rust_validator.py                                         54   Variable "repo_root" missing type annotation (PEP 526)                    
  test_toml_runner.py                                            61   Variable "repo_root" missing type annotation (PEP 526)                    
  tools/repo_lint/tests/test_vectors.py                          55   Variable "REPO_ROOT" missing type annotation (PEP 526)                    
  tools/repo_lint/tests/test_vectors.py                          56   Variable "VECTORS_DIR" missing type annotation (PEP 526)                  
  tools/repo_lint/tests/test_vectors.py                          57   Variable "DOCSTRINGS_DIR" missing type annotation (PEP 526)               
  test_yaml_runner.py                                            54   Variable "repo_root" missing type annotation (PEP 526)                    
  test_yaml_validator.py                                         54   Variable "repo_root" missing type annotation (PEP 526)                    
  tools/repo_lint/ui/__init__.py                                 37   Variable "__all__" missing type annotation (PEP 526)                      
  tools/repo_lint/ui/reporter.py                                 44   Variable "MAX_VIOLATIONS_PER_TOOL" missing type annotation (PEP 526)      
  tools/repo_lint/ui/reporter.py                                 47   Variable "MAX_MESSAGE_LENGTH_FOR_CODE" missing type annotation (PEP 526)  
  tools/repo_lint/ui/reporter.py                                 48   Variable "TRUNCATED_CODE_LENGTH" missing type annotation (PEP 526)        
  preflight_automerge_ruleset.py                                139   Variable "API_VERSION_DEFAULT" missing type annotation (PEP 526)          
  wrappers/python3/tests/test_preflight_automerge_ruleset.py     74   Variable "HERE" missing type annotation (PEP 526)                         
  wrappers/python3/tests/test_preflight_automerge_ruleset.py     75   Variable "ROOT" missing type annotation (PEP 526)                         
  wrappers/python3/tests/test_preflight_automerge_ruleset.py     76   Variable "SCRIPTS" missing type annotation (PEP 526)                      
  wrappers/python3/tests/test_preflight_automerge_ruleset.py     77   Variable "MODULE_PATH" missing type annotation (PEP 526)                  
  wrappers/python3/tests/test_safe_archive.py                    74   Variable "HERE" missing type annotation (PEP 526)                         
  wrappers/python3/tests/test_safe_archive.py                    75   Variable "ROOT" missing type annotation (PEP 526)                         
  wrappers/python3/tests/test_safe_archive.py                    76   Variable "SCRIPTS" missing type annotation (PEP 526)                      
  wrappers/python3/tests/test_safe_archive.py                    77   Variable "SAFE_ARCHIVE" missing type annotation (PEP 526)                 
  wrappers/python3/tests/test_safe_check.py                      63   Variable "HERE" missing type annotation (PEP 526)                         
  wrappers/python3/tests/test_safe_check.py                      64   Variable "ROOT" missing type annotation (PEP 526)                         
  wrappers/python3/tests/test_safe_check.py                      65   Variable "SCRIPTS" missing type annotation (PEP 526)                      
  wrappers/python3/tests/test_safe_check.py                      66   Variable "SAFE_CHECK" missing type annotation (PEP 526)                   
  wrappers/python3/tests/test_safe_run.py                        76   Variable "HERE" missing type annotation (PEP 526)                         
  wrappers/python3/tests/test_safe_run.py                        77   Variable "ROOT" missing type annotation (PEP 526)                         
  wrappers/python3/tests/test_safe_run.py                        78   Variable "SCRIPTS" missing type annotation (PEP 526)                      
  wrappers/python3/tests/test_safe_run.py                        79   Variable "SAFE_RUN" missing type annotation (PEP 526)                     
                                                                                                                                                

           Summary           
  Total Runners: 5           
    Passed: 4                
    Failed: 1                
  Total Violations: 146      
                             
  Exit Code: 1 (VIOLATIONS)  
                             
```

