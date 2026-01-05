# Repo Lint Summary

**Workflow Run:** https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/actions/runs/20722322138
**Timestamp:** 2026-01-05 16:44:33 UTC
**Branch:** 226/merge
**Commit:** 3ebd95838fb6d6cfeaa353ab06ed1404ea60540a

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
  rust_runner.py             231   UP007 Use `X | Y` for type annotations                    
  yaml_runner.py              52   UP006 Use `list` instead of `List` for type annotation    
  yaml_runner.py              61   UP006 Use `list` instead of `List` for type annotation    
  yaml_runner.py              77   UP007 Use `X | Y` for type annotations                    
  yaml_runner.py              77   UP006 Use `list` instead of `List` for type annotation    
  test_base_runner.py         23   I001 [*] Import block is un-sorted or un-formatted        
  test_bash_runner.py         23   I001 [*] Import block is un-sorted or un-formatted        
  test_cli_dispatch.py        23   I001 [*] Import block is un-sorted or un-formatted        
  test_exit_codes.py          23   I001 [*] Import block is un-sorted or un-formatted        
  test_install_helpers.py     23   I001 [*] Import block is un-sorted or un-formatted        
  test_integration.py         23   I001 [*] Import block is un-sorted or un-formatted        
  test_output_format.py       23   I001 [*] Import block is un-sorted or un-formatted        
  test_perl_runner.py         23   I001 [*] Import block is un-sorted or un-formatted        
  test_vectors.py             74   UP007 Use `X | Y` for type annotations                    
  test_vectors.py             74   UP006 Use `dict` instead of `Dict` for type annotation    
  test_vectors.py            124   UP006 Use `list` instead of `List` for type annotation    
  test_vectors.py            124   UP006 Use `dict` instead of `Dict` for type annotation    
  test_vectors.py            190   UP006 Use `list` instead of `List` for type annotation    
  test_vectors.py            190   UP006 Use `dict` instead of `Dict` for type annotation    
  test_vectors.py            215   UP006 Use `list` instead of `List` for type annotation    
  test_vectors.py            215   UP006 Use `dict` instead of `Dict` for type annotation    
  test_vectors.py            215   UP006 Use `list` instead of `List` for type annotation    
  test_vectors.py            215   UP006 Use `dict` instead of `Dict` for type annotation    
  console.py                  49   UP006 Use `dict` instead of `Dict` for type annotation    
  console.py                  49   UP006 Use `tuple` instead of `Tuple` for type annotation  
  console.py                  49   UP007 Use `X | Y` for type annotations                    
  console.py                  52   UP007 Use `X | Y` for type annotations                    
  reporter.py                 58   UP007 Use `X | Y` for type annotations                    
  reporter.py                159   UP006 Use `dict` instead of `Dict` for type annotation    
  reporter.py                230   UP006 Use `list` instead of `List` for type annotation    
  reporter.py                282   UP006 Use `list` instead of `List` for type annotation    
  reporter.py                405   UP006 Use `list` instead of `List` for type annotation    
  reporter.py                454   UP006 Use `list` instead of `List` for type annotation    
  reporter.py                600   UP006 Use `list` instead of `List` for type annotation    
  theme.py                   142   UP007 Use `X | Y` for type annotations                    
  theme.py                   210   UP007 Use `X | Y` for type annotations                    
  theme.py                   228   UP007 Use `X | Y` for type annotations                    
  unsafe_fixers.py            71   UP007 Use `X | Y` for type annotations                    
  unsafe_fixers.py            71   UP037 [*] Remove quotes from type annotation              
  unsafe_fixers.py           132   UP007 Use `X | Y` for type annotations                    
  unsafe_fixers.py           221   UP006 Use `list` instead of `List` for type annotation    
  unsafe_fixers.py           226   UP006 Use `list` instead of `List` for type annotation    
  unsafe_fixers.py           234   UP006 Use `list` instead of `List` for type annotation    
  unsafe_fixers.py           234   UP006 Use `list` instead of `List` for type annotation    
  yaml_loader.py              61   UP007 Use `X | Y` for type annotations                    
  yaml_loader.py              64   UP007 Use `X | Y` for type annotations                    
  yaml_loader.py             133   UP006 Use `list` instead of `List` for type annotation    
  yaml_loader.py             133   UP006 Use `dict` instead of `Dict` for type annotation    
  yaml_loader.py             172   UP006 Use `dict` instead of `Dict` for type annotation    
  yaml_loader.py             187   UP006 Use `dict` instead of `Dict` for type annotation    
  yaml_loader.py             202   UP006 Use `dict` instead of `Dict` for type annotation    
  yaml_loader.py             217   UP006 Use `dict` instead of `Dict` for type annotation    
  yaml_loader.py             244   UP006 Use `dict` instead of `Dict` for type annotation    
  yaml_loader.py             277   UP006 Use `list` instead of `List` for type annotation    
  yaml_loader.py             290   UP006 Use `list` instead of `List` for type annotation    
  yaml_loader.py             314   UP006 Use `list` instead of `List` for type annotation    
  yaml_loader.py             326   UP006 Use `dict` instead of `Dict` for type annotation    
  yaml_loader.py             326   UP006 Use `dict` instead of `Dict` for type annotation    
  yaml_loader.py             380   UP006 Use `dict` instead of `Dict` for type annotation    
                                                                                             

  ⚠️  [*] 10 fixable with the `--fix` option (185 hidden fixes can be enabled with the `--unsafe-fixes` option). (Review before applying with --unsafe-fixes)


                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                pylint Failures                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 
  Found 9 violation(s)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                
                                                                                                  
  File                      Line   Message                                                        
 ──────────────────────────────────────────────────────────────────────────────────────────────── 
  cli.py                      75   W0404: Reimport 'annotations' (imported line 71) (reimported)  
  test_base_runner.py         25   W0404: Reimport 'annotations' (imported line 23) (reimported)  
  test_bash_runner.py         25   W0404: Reimport 'annotations' (imported line 23) (reimported)  
  test_cli_dispatch.py        25   W0404: Reimport 'annotations' (imported line 23) (reimported)  
  test_exit_codes.py          25   W0404: Reimport 'annotations' (imported line 23) (reimported)  
  test_install_helpers.py     25   W0404: Reimport 'annotations' (imported line 23) (reimported)  
  test_integration.py         25   W0404: Reimport 'annotations' (imported line 23) (reimported)  
  test_output_format.py       25   W0404: Reimport 'annotations' (imported line 23) (reimported)  
  test_perl_runner.py         25   W0404: Reimport 'annotations' (imported line 23) (reimported)  
                                                                                                  

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          validate_docstrings Failures                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          
  Found 3 violation(s)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                
                                                                                                                                     
  File   Line   Message                                                                                                              
 ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── 
  .         -   ❌ Validation FAILED: 2 violation(s) in 1 file(s)                                                                    
  .         -   ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/scripts/add_future_annotations.py     
  .         -   ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/scripts/add_future_annotations.py:15  
                                                                                                                                     

           Summary           
  Total Runners: 4           
    Passed: 1                
    Failed: 3                
  Total Violations: 207      
                             
  Exit Code: 1 (VIOLATIONS)  
                             
```

