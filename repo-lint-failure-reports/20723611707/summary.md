# Repo Lint Summary

**Workflow Run:** https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/actions/runs/20723611707
**Timestamp:** 2026-01-05 17:31:13 UTC
**Branch:** 228/merge
**Commit:** 46037fe8e08d521d04d8ae7062d0850b225e3b5e

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
| Vector Tests: Conformance | failure |

## Python Linting Failures

```
  naming_runner.py                  231   UP006 Use `list` instead of `List` for type annotation    
  naming_runner.py                  231   UP006 Use `dict` instead of `Dict` for type annotation    
  naming_runner.py                  262   UP006 Use `dict` instead of `Dict` for type annotation    
  naming_runner.py                  262   UP006 Use `list` instead of `List` for type annotation    
  naming_runner.py                  262   UP006 Use `dict` instead of `Dict` for type annotation    
  perl_runner.py                     55   UP006 Use `list` instead of `List` for type annotation    
  perl_runner.py                     64   UP006 Use `list` instead of `List` for type annotation    
  perl_runner.py                     83   UP007 Use `X | Y` for type annotations                    
  perl_runner.py                     83   UP006 Use `list` instead of `List` for type annotation    
  perl_runner.py                    100   UP006 Use `list` instead of `List` for type annotation    
  powershell_runner.py               55   UP006 Use `list` instead of `List` for type annotation    
  powershell_runner.py               84   UP006 Use `list` instead of `List` for type annotation    
  powershell_runner.py              103   UP007 Use `X | Y` for type annotations                    
  powershell_runner.py              103   UP006 Use `list` instead of `List` for type annotation    
  powershell_runner.py              122   UP006 Use `list` instead of `List` for type annotation    
  python_runner.py                  131   UP006 Use `list` instead of `List` for type annotation    
  python_runner.py                  140   UP006 Use `list` instead of `List` for type annotation    
  python_runner.py                  165   UP007 Use `X | Y` for type annotations                    
  python_runner.py                  165   UP006 Use `list` instead of `List` for type annotation    
  python_runner.py                  263   UP006 Use `list` instead of `List` for type annotation    
  python_runner.py                  263   UP007 Use `X | Y` for type annotations                    
  rust_runner.py                     65   UP006 Use `list` instead of `List` for type annotation    
  rust_runner.py                     91   UP006 Use `list` instead of `List` for type annotation    
  rust_runner.py                    113   UP007 Use `X | Y` for type annotations                    
  rust_runner.py                    113   UP006 Use `list` instead of `List` for type annotation    
  rust_runner.py                    231   UP007 Use `X | Y` for type annotations                    
  yaml_runner.py                     52   UP006 Use `list` instead of `List` for type annotation    
  yaml_runner.py                     61   UP006 Use `list` instead of `List` for type annotation    
  yaml_runner.py                     77   UP007 Use `X | Y` for type annotations                    
  yaml_runner.py                     77   UP006 Use `list` instead of `List` for type annotation    
  test_vectors.py                    74   UP007 Use `X | Y` for type annotations                    
  test_vectors.py                    74   UP006 Use `dict` instead of `Dict` for type annotation    
  test_vectors.py                   124   UP006 Use `list` instead of `List` for type annotation    
  test_vectors.py                   124   UP006 Use `dict` instead of `Dict` for type annotation    
  test_vectors.py                   190   UP006 Use `list` instead of `List` for type annotation    
  test_vectors.py                   190   UP006 Use `dict` instead of `Dict` for type annotation    
  test_vectors.py                   215   UP006 Use `list` instead of `List` for type annotation    
  test_vectors.py                   215   UP006 Use `dict` instead of `Dict` for type annotation    
  test_vectors.py                   215   UP006 Use `list` instead of `List` for type annotation    
  test_vectors.py                   215   UP006 Use `dict` instead of `Dict` for type annotation    
  console.py                         49   UP006 Use `dict` instead of `Dict` for type annotation    
  console.py                         49   UP006 Use `tuple` instead of `Tuple` for type annotation  
  console.py                         49   UP007 Use `X | Y` for type annotations                    
  console.py                         52   UP007 Use `X | Y` for type annotations                    
  reporter.py                        58   UP007 Use `X | Y` for type annotations                    
  reporter.py                       159   UP006 Use `dict` instead of `Dict` for type annotation    
  reporter.py                       230   UP006 Use `list` instead of `List` for type annotation    
  reporter.py                       282   UP006 Use `list` instead of `List` for type annotation    
  reporter.py                       405   UP006 Use `list` instead of `List` for type annotation    
  reporter.py                       454   UP006 Use `list` instead of `List` for type annotation    
  reporter.py                       600   UP006 Use `list` instead of `List` for type annotation    
  theme.py                          142   UP007 Use `X | Y` for type annotations                    
  theme.py                          210   UP007 Use `X | Y` for type annotations                    
  theme.py                          228   UP007 Use `X | Y` for type annotations                    
  unsafe_fixers.py                   69   UP007 Use `X | Y` for type annotations                    
  unsafe_fixers.py                  130   UP007 Use `X | Y` for type annotations                    
  unsafe_fixers.py                  219   UP006 Use `list` instead of `List` for type annotation    
  unsafe_fixers.py                  224   UP006 Use `list` instead of `List` for type annotation    
  unsafe_fixers.py                  232   UP006 Use `list` instead of `List` for type annotation    
  unsafe_fixers.py                  232   UP006 Use `list` instead of `List` for type annotation    
  yaml_loader.py                     61   UP007 Use `X | Y` for type annotations                    
  yaml_loader.py                     64   UP007 Use `X | Y` for type annotations                    
  yaml_loader.py                    133   UP006 Use `list` instead of `List` for type annotation    
  yaml_loader.py                    133   UP006 Use `dict` instead of `Dict` for type annotation    
  yaml_loader.py                    172   UP006 Use `dict` instead of `Dict` for type annotation    
  yaml_loader.py                    187   UP006 Use `dict` instead of `Dict` for type annotation    
  yaml_loader.py                    202   UP006 Use `dict` instead of `Dict` for type annotation    
  yaml_loader.py                    217   UP006 Use `dict` instead of `Dict` for type annotation    
  yaml_loader.py                    244   UP006 Use `dict` instead of `Dict` for type annotation    
  yaml_loader.py                    277   UP006 Use `list` instead of `List` for type annotation    
  yaml_loader.py                    290   UP006 Use `list` instead of `List` for type annotation    
  yaml_loader.py                    314   UP006 Use `list` instead of `List` for type annotation    
  yaml_loader.py                    326   UP006 Use `dict` instead of `Dict` for type annotation    
  yaml_loader.py                    326   UP006 Use `dict` instead of `Dict` for type annotation    
  yaml_loader.py                    380   UP006 Use `dict` instead of `Dict` for type annotation    
  preflight_automerge_ruleset.py    229   UP007 Use `X | Y` for type annotations                    
  preflight_automerge_ruleset.py    269   UP006 Use `tuple` instead of `Tuple` for type annotation  
  preflight_automerge_ruleset.py    331   UP006 Use `list` instead of `List` for type annotation    
  preflight_automerge_ruleset.py    332   UP007 Use `X | Y` for type annotations                    
  preflight_automerge_ruleset.py    332   UP006 Use `tuple` instead of `Tuple` for type annotation  
  preflight_automerge_ruleset.py    332   UP007 Use `X | Y` for type annotations                    
  preflight_automerge_ruleset.py    332   UP007 Use `X | Y` for type annotations                    
  preflight_automerge_ruleset.py    414   UP006 Use `list` instead of `List` for type annotation    
  safe_archive.py                   267   UP006 Use `list` instead of `List` for type annotation    
  safe_check.py                     136   UP006 Use `list` instead of `List` for type annotation    
  safe_run.py                       104   UP007 Use `X | Y` for type annotations                    
  safe_run.py                       195   UP007 Use `X | Y` for type annotations                    
                                                                                                    

  ⚠️  No fixes available (222 hidden fixes can be enabled with the `--unsafe-fixes` option). (Review before applying with --unsafe-fixes)


           Summary           
  Total Runners: 4           
    Passed: 3                
    Failed: 1                
  Total Violations: 222      
                             
  Exit Code: 1 (VIOLATIONS)  
                             
```

## Vector Test Failures

Vector tests failed. See job logs for details.

