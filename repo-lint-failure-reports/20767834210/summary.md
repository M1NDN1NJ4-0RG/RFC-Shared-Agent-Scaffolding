# Repo Lint Summary

**Workflow Run:** https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/actions/runs/20767834210
**Timestamp:** 2026-01-07 01:44:17 UTC
**Branch:** 252/merge
**Commit:** 33264dcf18ec213a7e2a904f912918fdbd5b3fe4

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
  .         -   Diff in /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/rust/src/bootstrap_main.rs:164:  
  .         -   // 11. Run automatic verification gate (repo-lint check --ci)                                                        
  .         -   // This runs if repo-lint was in the plan (profile includes it)                                                      
  .         -   -    let repo_lint_in_plan = plan.phases.iter().any(|phase| {                                                        
  .         -   -        phase                                                                                                       
  .         -   -            .steps                                                                                                  
  .         -   -            .iter()                                                                                                 
  .         -   -            .any(|step| step.installer == "repo-lint")                                                              
  .         -   -    });                                                                                                             
  .         -   +    let repo_lint_in_plan = plan                                                                                    
  .         -   +        .phases                                                                                                     
  .         -   +        .iter()                                                                                                     
  .         -   +        .any(|phase| phase.steps.iter().any(|step| step.installer == "repo-lint"));                                 
  .         -   if repo_lint_in_plan && !dry_run {                                                                                   
  .         -   println!("\n🔍 Running verification gate (repo-lint check --ci)...");                                                
  .         -   Diff in /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/rust/src/bootstrap_main.rs:188:  
  .         -   println!("  ✓ Verification gate passed (no violations)");                                                            
  .         -   }                                                                                                                    
  .         -   1 => {                                                                                                               
  .         -   -                        println!("  ✓ Verification gate passed (tools functional, violations found)");              
                                                                                                                                     

           Summary           
  Total Runners: 3           
    Passed: 2                
    Failed: 1                
  Total Violations: 20       
                             
  Exit Code: 1 (VIOLATIONS)  
                             
```

