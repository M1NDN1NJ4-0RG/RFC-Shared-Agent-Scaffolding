# Repo Lint Summary

**Workflow Run:** https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/actions/runs/20721007923
**Timestamp:** 2026-01-05 16:00:56 UTC
**Branch:** 226/merge
**Commit:** a90c4e7de6a592fc66f76a89311201dde447e631

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
  bash_runner.py            88   UP007 Use `X | Y` for type annotations                    
  bash_runner.py            88   UP006 Use `list` instead of `List` for type annotation    
  bash_runner.py           125   UP006 Use `list` instead of `List` for type annotation    
  naming_runner.py          74   UP006 Use `list` instead of `List` for type annotation    
  naming_runner.py          81   UP006 Use `list` instead of `List` for type annotation    
  naming_runner.py         126   UP007 Use `X | Y` for type annotations                    
  naming_runner.py         126   UP006 Use `list` instead of `List` for type annotation    
  naming_runner.py         142   UP006 Use `list` instead of `List` for type annotation    
  naming_runner.py         154   UP006 Use `list` instead of `List` for type annotation    
  naming_runner.py         154   UP006 Use `list` instead of `List` for type annotation    
  naming_runner.py         188   UP007 Use `X | Y` for type annotations                    
  naming_runner.py         231   UP006 Use `dict` instead of `Dict` for type annotation    
  naming_runner.py         231   UP006 Use `list` instead of `List` for type annotation    
  naming_runner.py         231   UP006 Use `dict` instead of `Dict` for type annotation    
  naming_runner.py         262   UP006 Use `dict` instead of `Dict` for type annotation    
  naming_runner.py         262   UP006 Use `list` instead of `List` for type annotation    
  naming_runner.py         262   UP006 Use `dict` instead of `Dict` for type annotation    
  perl_runner.py            55   UP006 Use `list` instead of `List` for type annotation    
  perl_runner.py            64   UP006 Use `list` instead of `List` for type annotation    
  perl_runner.py            83   UP007 Use `X | Y` for type annotations                    
  perl_runner.py            83   UP006 Use `list` instead of `List` for type annotation    
  perl_runner.py           100   UP006 Use `list` instead of `List` for type annotation    
  powershell_runner.py      55   UP006 Use `list` instead of `List` for type annotation    
  powershell_runner.py      84   UP006 Use `list` instead of `List` for type annotation    
  powershell_runner.py     103   UP007 Use `X | Y` for type annotations                    
  powershell_runner.py     103   UP006 Use `list` instead of `List` for type annotation    
  powershell_runner.py     122   UP006 Use `list` instead of `List` for type annotation    
  python_runner.py          62   UP007 Use `X | Y` for type annotations                    
  python_runner.py         170   UP006 Use `list` instead of `List` for type annotation    
  python_runner.py         179   UP006 Use `list` instead of `List` for type annotation    
  python_runner.py         204   UP007 Use `X | Y` for type annotations                    
  python_runner.py         204   UP006 Use `list` instead of `List` for type annotation    
  python_runner.py         288   UP007 Use `X | Y` for type annotations                    
  python_runner.py         289   UP007 Use `X | Y` for type annotations                    
  python_runner.py         356   UP006 Use `list` instead of `List` for type annotation    
  python_runner.py         356   UP007 Use `X | Y` for type annotations                    
  rust_runner.py            65   UP006 Use `list` instead of `List` for type annotation    
  rust_runner.py            91   UP006 Use `list` instead of `List` for type annotation    
  rust_runner.py           113   UP007 Use `X | Y` for type annotations                    
  rust_runner.py           113   UP006 Use `list` instead of `List` for type annotation    
  rust_runner.py           231   UP007 Use `X | Y` for type annotations                    
  yaml_runner.py            52   UP006 Use `list` instead of `List` for type annotation    
  yaml_runner.py            61   UP006 Use `list` instead of `List` for type annotation    
  yaml_runner.py            77   UP007 Use `X | Y` for type annotations                    
  yaml_runner.py            77   UP006 Use `list` instead of `List` for type annotation    
  test_integration.py       24   I001 [*] Import block is un-sorted or un-formatted        
  test_output_format.py     24   I001 [*] Import block is un-sorted or un-formatted        
  test_perl_runner.py       24   I001 [*] Import block is un-sorted or un-formatted        
  test_vectors.py           74   UP007 Use `X | Y` for type annotations                    
  test_vectors.py           74   UP006 Use `dict` instead of `Dict` for type annotation    
  test_vectors.py          124   UP006 Use `list` instead of `List` for type annotation    
  test_vectors.py          124   UP006 Use `dict` instead of `Dict` for type annotation    
  test_vectors.py          190   UP006 Use `list` instead of `List` for type annotation    
  test_vectors.py          190   UP006 Use `dict` instead of `Dict` for type annotation    
  test_vectors.py          215   UP006 Use `list` instead of `List` for type annotation    
  test_vectors.py          215   UP006 Use `dict` instead of `Dict` for type annotation    
  test_vectors.py          215   UP006 Use `list` instead of `List` for type annotation    
  test_vectors.py          215   UP006 Use `dict` instead of `Dict` for type annotation    
  console.py                49   UP006 Use `dict` instead of `Dict` for type annotation    
  console.py                49   UP006 Use `tuple` instead of `Tuple` for type annotation  
  console.py                49   UP007 Use `X | Y` for type annotations                    
  console.py                52   UP007 Use `X | Y` for type annotations                    
  reporter.py               58   UP007 Use `X | Y` for type annotations                    
  reporter.py              159   UP006 Use `dict` instead of `Dict` for type annotation    
  reporter.py              230   UP006 Use `list` instead of `List` for type annotation    
  reporter.py              282   UP006 Use `list` instead of `List` for type annotation    
  reporter.py              405   UP006 Use `list` instead of `List` for type annotation    
  reporter.py              454   UP006 Use `list` instead of `List` for type annotation    
  reporter.py              600   UP006 Use `list` instead of `List` for type annotation    
  theme.py                 142   UP007 Use `X | Y` for type annotations                    
  theme.py                 210   UP007 Use `X | Y` for type annotations                    
  theme.py                 228   UP007 Use `X | Y` for type annotations                    
  yaml_loader.py            61   UP007 Use `X | Y` for type annotations                    
  yaml_loader.py            64   UP007 Use `X | Y` for type annotations                    
  yaml_loader.py           133   UP006 Use `list` instead of `List` for type annotation    
  yaml_loader.py           133   UP006 Use `dict` instead of `Dict` for type annotation    
  yaml_loader.py           172   UP006 Use `dict` instead of `Dict` for type annotation    
  yaml_loader.py           187   UP006 Use `dict` instead of `Dict` for type annotation    
  yaml_loader.py           202   UP006 Use `dict` instead of `Dict` for type annotation    
  yaml_loader.py           217   UP006 Use `dict` instead of `Dict` for type annotation    
  yaml_loader.py           244   UP006 Use `dict` instead of `Dict` for type annotation    
  yaml_loader.py           277   UP006 Use `list` instead of `List` for type annotation    
  yaml_loader.py           290   UP006 Use `list` instead of `List` for type annotation    
  yaml_loader.py           314   UP006 Use `list` instead of `List` for type annotation    
  yaml_loader.py           326   UP006 Use `dict` instead of `Dict` for type annotation    
  yaml_loader.py           326   UP006 Use `dict` instead of `Dict` for type annotation    
  yaml_loader.py           380   UP006 Use `dict` instead of `Dict` for type annotation    
                                                                                           

  ⚠️  [*] 3 fixable with the `--fix` option (179 hidden fixes can be enabled with the `--unsafe-fixes` option). (Review before applying with --unsafe-fixes)


           Summary           
  Total Runners: 4           
    Passed: 3                
    Failed: 1                
  Total Violations: 182      
                             
  Exit Code: 1 (VIOLATIONS)  
                             
```

