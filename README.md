# RFC-Shared-Agent-Scaffolding

A restartable, failure-resilient operating model for AI coding agents.

## Overview

This repository implements the RFC-Shared-Agent-Scaffolding contract (v0.1.0), which defines structured command execution, event logging, and artifact generation for AI agent workflows.

## Implementations

### Rust Canonical Tool (Primary)

The **Rust canonical tool** is the single source of truth for the contract behavior. It provides:

- ✅ Cross-platform consistency (Linux, macOS, Windows)
- ✅ Type-safe implementation
- ✅ Event ledger and merged view modes
- ✅ Exit code forwarding and signal handling
- ✅ Artifact generation with no-clobber semantics

**Build and run:**

```bash
cd rust/
cargo build --release
./target/release/safe-run --help
```

**Documentation:**

- [Rust Canonical Tool](./docs/rust-canonical-tool.md)
- [Wrapper Discovery](./docs/wrapper-discovery.md)
- [Conformance Contract](./docs/conformance-contract.md)
- [Safe-Archive Guide](./docs/safe-archive.md)

### Language-Specific Wrappers (Compatibility)

Thin wrapper scripts that discover and invoke the Rust canonical tool:

- **Bash:** `wrappers/scripts/bash/scripts/safe-run.sh`
- **Perl:** `wrappers/scripts/perl/scripts/safe-run.pl`
- **Python3:** `wrappers/scripts/python3/scripts/safe-run.py`
- **PowerShell:** `wrappers/scripts/powershell/scripts/safe-run.ps1`

Wrappers act as **invokers**, not independent implementations. They:

1. Discover the Rust binary (environment override, dev mode, CI artifacts, PATH)
2. Pass through all arguments
3. Forward exit codes
4. Provide actionable error messages if Rust binary is missing

## Documentation

📚 **[Documentation Index](./docs/README.md)** - Complete documentation guide

Quick links:
- [RFC v0.1.0](./rfc-shared-agent-scaffolding-v0.1.0.md) - Contract specification
- [Canonical Structure](./docs/architecture/canonical-structure.md) - Directory layout
- [Pre-flight Validation](./docs/history/pr0-preflight-complete.md) - Baseline conformance report
- [Docstring Contracts](./docs/docstrings/README.md) - Documentation standards for all languages

### Docstring Contracts

**ALL scripts in this repository MUST conform to their language-specific docstring contract**, regardless of location. The validator checks every script file repository-wide to ensure consistent documentation.

Contracts define required documentation sections (purpose, usage, examples, exit codes, etc.) for:

- **Bash** (`.sh`, `.bash`, `.zsh`)
- **PowerShell** (`.ps1`)
- **Python 3** (`.py`)
- **Perl** (`.pl`, `.pm`)
- **Rust** (`.rs`)
- **YAML** (`.yml`, `.yaml` - workflows and configs)

**Any new script added anywhere in the repository** will be validated against its language contract. Conformance is enforced by CI via `scripts/validate-docstrings.py`. See [docs/docstrings/README.md](./docs/docstrings/README.md) for details and templates.

## Contributing

See [EPIC #33: Rust Canonical Tool](https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/issues/33) for the implementation roadmap.

## License

[Unlicense](./LICENSE)
