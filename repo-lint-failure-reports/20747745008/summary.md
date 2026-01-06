# Repo Lint Summary

**Workflow Run:** https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/actions/runs/20747745008
**Timestamp:** 2026-01-06 12:09:15 UTC
**Branch:** 240/merge
**Commit:** 2680b483d1b45af333f757bd7459f1b55a8a1136

## Job Results

| Job | Status |
|-----|--------|
| Auto-Fix: Black | success |
| Detect Changed Files | success |
| Repo Lint: Python | skipped |
| Repo Lint: Bash | skipped |
| Repo Lint: PowerShell | skipped |
| Repo Lint: Perl | skipped |
| Repo Lint: YAML | skipped |
| Repo Lint: Rust | failure |
| Vector Tests: Conformance | skipped |

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
 ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── 
  .         -   Diff in /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/rust/src/bootstrap_main.rs:138:               
  .         -   // 7. Compute execution plan                                                                                                      
  .         -   progress.emit_event_plan_computed();                                                                                              
  .         -   let profile_name = profile.as_deref().unwrap_or("dev");                                                                           
  .         -   -    let plan = ExecutionPlan::compute(&registry, config.as_ref(), ctx.as_ref(), profile_name).await?;                            
  .         -   +    let plan =                                                                                                                   
  .         -   +        ExecutionPlan::compute(&registry, config.as_ref(), ctx.as_ref(), profile_name).await?;                                   
  .         -   // Print plan in appropriate format                                                                                               
  .         -   if json {                                                                                                                         
  .         -   Diff in /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/rust/src/bootstrap_main.rs:260:               
  .         -   for installer in installers {                                                                                                     
  .         -   let result = installer.verify(ctx.as_ref()).await?;                                                                               
  .         -   if result.success {                                                                                                               
  .         -   -            println!("✅ {}: {}", installer.name(), result.version.map(|v| v.to_string()).unwrap_or_else(|| "OK".to_string()));  
  .         -   +            println!(                                                                                                            
  .         -   +                "✅ {}: {}",                                                                                                     
  .         -   +                installer.name(),                                                                                                
  .         -   +                result                                                                                                           
  .         -   +                    .version                                                                                                     
  .         -   +                    .map(|v| v.to_string())                                                                                      
                                                                                                                                                  

           Summary           
  Total Runners: 3           
    Passed: 2                
    Failed: 1                
  Total Violations: 20       
                             
  Exit Code: 1 (VIOLATIONS)  
                             
```

