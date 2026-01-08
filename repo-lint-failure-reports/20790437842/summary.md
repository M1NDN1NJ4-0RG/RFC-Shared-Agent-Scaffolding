# Repo Lint Summary

**Workflow Run:** https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/actions/runs/20790437842
**Timestamp:** 2026-01-07 17:32:14 UTC
**Branch:** 259/merge
**Commit:** aaf6a3d264fb2a65698180b7abc9f281c8645526

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
  rustfmt           ❌ FAIL       -           11          -
  clippy            ✅ PASS       -            0          -
  rust-docstrings   ✅ PASS       -            0          -


                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                rustfmt Failures
  Found 11 violation(s)


  File   Line   Message
 ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  .         -   Diff in /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/rust/src/bootstrap_v2/activate.rs:153:
  .         -   println!("source {}/bin/activate", venv_path.display());
  .         -   println!("# Configure Perl environment");
  .         -   println!("export PATH=\"{}:$PATH\"", perl_bin);
  .         -   -    println!("export PERL5LIB=\"{}${{PERL5LIB:+:${{PERL5LIB}}}}\"", perl_lib);
  .         -   +    println!(
  .         -   +        "export PERL5LIB=\"{}${{PERL5LIB:+:${{PERL5LIB}}}}\"",
  .         -   +        perl_lib
  .         -   +    );
  .         -   println!("export BOOTSTRAP_ACTIVATED=1");
  .         -   }


           Summary
  Total Runners: 3
    Passed: 2
    Failed: 1
  Total Violations: 11

  Exit Code: 1 (VIOLATIONS)

```

