# Issue #265 - Next Steps

## NEXT

- [ ] Explore the current Rust project structure to understand:
  - Current `rust/Cargo.toml` configuration
  - Location of `safe-run` binary source
  - Location of `bootstrap-repo-cli` binary source
  - Location of the current `bootstrap_v2` implementation
  - Location of the "proto" bootstrapper artifacts to be removed
- [ ] Search for proto-rust-bootstrapper remnants using `rg`
- [ ] Create working branch for this epic
- [ ] Execute Phase 0: Preflight/Baseline checks
- [ ] Execute Phase 1: Remove proto-rust-bootstrapper artifacts
- [ ] Execute Phase 2: Convert to Cargo workspace with separate packages
- [ ] Execute Phase 3: Update CI/workflows/scripts
- [ ] Execute Phase 4: Final cleanup and verification

## Resume Pointers

**Branch:** TBD (will create after exploration)

**Key Files:**
- `rust/Cargo.toml` - Current single-package manifest
- `rust/src/main.rs` - safe-run binary entrypoint
- `rust/src/bootstrap_v2/` - Current bootstrapper implementation (presumed)
- Proto bootstrapper files - TBD (need to locate)

**Key Commands:**
- `cd rust && cargo build --release` - Current build
- `cd rust && cargo test` - Current test
- `rg -n "rust/src/bootstrap\.rs|\bbootstrap\.rs\b"` - Search for proto artifacts
- `repo-lint check --ci` - Pre-commit gate

**Session State:** Starting fresh - need to explore repository structure first.
