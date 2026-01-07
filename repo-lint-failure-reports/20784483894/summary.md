# Repo Lint Summary

**Workflow Run:** https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/actions/runs/20784483894
**Timestamp:** 2026-01-07 14:38:19 UTC
**Branch:** 259/merge
**Commit:** fd95aabdb143ca81f438c7f74ac645ccb3aeacd4

## Job Results

| Job | Status |
|-----|--------|
| Auto-Fix: Black | success |
| Detect Changed Files | success |
| Repo Lint: Python | success |
| Repo Lint: Bash | success |
| Repo Lint: PowerShell | success |
| Repo Lint: Perl | success |
| Repo Lint: YAML | success |
| Repo Lint: Rust | failure |
| Vector Tests: Conformance | success |

## Rust Linting Failures

```
🔍 Running repository linters and formatters...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Rust Linting
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                       Linting Results                       
                                                             
  Runner            Status    Files   Violations   Duration  
 ─────────────────────────────────────────────────────────── 
  rustfmt           ❌ FAIL       -           20          -  
  clippy            ✅ PASS       -            0          -  
  rust-docstrings   ✅ PASS       -            0          -  
                                                             

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                rustfmt Failures                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                
  Found 20 violation(s)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                
                                                                                                                                     
  File   Line   Message                                                                                                              
 ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── 
  .         -   Diff in /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/rust/src/bootstrap_main.rs:192:  
  .         -   println!("\n🔍 Running verification gate (repo-lint check --ci)...");                                                
  .         -   let repo_lint_bin = ctx.repo_lint_bin();                                                                             
  .         -   -                                                                                                                    
  .         -   +                                                                                                                    
  .         -   // Add .venv/bin to PATH for the subprocess so Python tools are accessible                                           
  .         -   let venv_bin = ctx.venv_path.join("bin");                                                                            
  .         -   let current_path = std::env::var("PATH").unwrap_or_default();                                                        
  .         -   Diff in /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/rust/src/bootstrap_main.rs:199:  
  .         -   -                                                                                                                    
  .         -   +                                                                                                                    
  .         -   // Add Perl environment for Perl tools                                                                               
  .         -   let home = std::env::var("HOME").unwrap_or_else(|_| "/home/runner".to_string());                                     
  .         -   let perl_home = format!("{}/perl5", home);                                                                           
  .         -   Diff in /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/rust/src/bootstrap_main.rs:203:  
  .         -   let perl_bin = format!("{}/bin", perl_home);                                                                         
  .         -   let perl5lib = format!("{}/lib/perl5", perl_home);                                                                   
  .         -   -                                                                                                                    
  .         -   +                                                                                                                    
  .         -   let new_path = format!("{}:{}:{}", perl_bin, venv_bin.display(), current_path);                                      
                                                                                                                                     

           Summary           
  Total Runners: 3           
    Passed: 2                
    Failed: 1                
  Total Violations: 20       
                             
  Exit Code: 1 (VIOLATIONS)  
                             
```

