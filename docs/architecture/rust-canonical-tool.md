# Rust Canonical Tool

## Overview

The Rust Canonical Tool is the **single source of truth** for the behavior contract defined in RFC-Shared-Agent-Scaffolding v0.1.0. It implements the core functionality for `safe-run`, `safe-check`, `safe-archive`, and related commands.

## Purpose

Prior to this implementation, four independent language wrappers (Bash, Perl, Python3, PowerShell) each maintained their own implementation of the contract. This led to:

- **Drift risk:** Different regex dialects, buffering semantics, exit code handling
- **Maintenance burden:** N implementations to update for each behavior change
- **Testing complexity:** Cross-platform conformance required complex test matrices
- **Escaping hell:** YAML + Bash + JavaScript escaping in CI workflows

The Rust Canonical Tool solves these problems by:

1. **Centralizing behavior:** One implementation defines the contract
2. **Thin wrappers:** Language-specific wrappers become invoker scripts, not reimplementations
3. **Cross-platform consistency:** Rust's stdlib provides uniform behavior across OS targets
4. **Type safety:** Compile-time guarantees for data structures and contracts

## Architecture

### Core Modules

```
rust/
├── Cargo.toml              # Project metadata and dependencies
├── src/
│   ├── main.rs             # CLI entry point
│   ├── cli.rs              # Argument parsing (clap)
│   ├── contract/           # Contract behavior implementations
│   │   ├── mod.rs
│   │   ├── events.rs       # Event ledger logic
│   │   ├── format.rs       # Output formatting
│   │   ├── merged_view.rs  # Human-friendly merged output
│   │   └── exit_behavior.rs # Exit code normalization
│   ├── platform/           # OS-specific handling
│   │   ├── mod.rs
│   │   ├── unix.rs         # Unix/Linux/macOS signal forwarding
│   │   └── windows.rs      # Windows process/signal handling
│   └── util/               # Shared utilities
│       └── mod.rs
└── tests/                  # Integration tests
    ├── fixtures/
    ├── snapshots/
    └── conformance.rs
```

### Contract Implementation

The canonical tool implements the following behaviors as defined in the RFC:

1. **Event Ledger Mode** (default)
   - Monotonic sequence numbers
   - META events (START, END, EXIT)
   - Stream-tagged output (STDOUT, STDERR)
   - Per-line emission

2. **Merged View Mode** (`SAFE_RUN_VIEW=merged`)
   - Human-friendly interleaved output
   - Preserves temporal ordering
   - Optional colorization

3. **Exit Code Forwarding**
   - Preserves child process exit codes
   - Signal-to-exit-code translation (128 + signal number)
   - Platform-specific signal handling

4. **Artifact Generation**
   - Timestamped log files
   - No-clobber semantics
   - Custom output directories

## Binary Distribution

The canonical tool is built for multiple platforms:

- **Linux:** `x86_64-unknown-linux-gnu`
- **macOS:** `x86_64-apple-darwin`, `aarch64-apple-darwin` (Apple Silicon)
- **Windows:** `x86_64-pc-windows-msvc`

Binaries are distributed via:

1. **CI Artifacts:** Build artifacts uploaded to GitHub Actions
2. **Releases:** Tagged releases with pre-built binaries (future)
3. **Local Build:** `cargo build --release` for development

## Integration with Wrappers

Language-specific wrappers (Bash, Perl, Python3, PowerShell) discover and invoke the Rust binary following these rules:

1. **Environment override:** `SAFE_RUN_BIN` env var (if set)
2. **Dev mode:** `./target/release/<tool>` (local builds)
3. **CI artifacts:** `./dist/<os>/<arch>/<tool>` (CI builds)
4. **PATH lookup:** System-wide installation
5. **Error fallback:** Actionable error message with install instructions

See [wrapper-discovery.md](./wrapper-discovery.md) for full details.

## Development

### Prerequisites

- Rust 1.70+ (MSRV - Minimum Supported Rust Version)
- Cargo (comes with Rust)

### Building

```bash
# Debug build
cargo build

# Release build (optimized)
cargo build --release

# Run tests
cargo test

# Run with arguments
cargo run -- --help
cargo run -- --version
```

### Testing Strategy

1. **Unit tests:** Module-level behavior (inline tests)
2. **Integration tests:** Full command execution (`tests/`)
3. **Conformance tests:** Validate against contract fixtures
4. **Cross-platform CI:** Linux, macOS, Windows matrix

See [conformance-contract.md](../usage/conformance-contract.md) for test specifications.

## Performance and Memory Characteristics

### Memory Usage on Failure

When a command fails, `safe-run` captures and stores all stdout/stderr output in memory
before writing the failure log. This design ensures complete output capture but has
implications for commands that produce very large output volumes:

- **Normal usage**: Memory overhead is minimal for typical command output (< 10MB)
- **Large output**: Commands producing hundreds of MB or more of output will temporarily
  consume that memory until the failure log is written
- **Mitigation**: For extremely high-throughput scenarios, consider:
  - Using `SAFE_SNIPPET_LINES` sparingly (higher values print more to stderr)
  - Monitoring memory usage in resource-constrained environments
  - Redirecting bulk output to files before piping to `safe-run`

### Future Improvements

The following enhancements are under consideration for future releases:

- **Streaming-to-file mode**: Write output directly to log files instead of buffering
  entirely in memory, reducing peak memory usage for high-volume commands
- **Bounded buffering**: Implement a ring buffer with configurable size limits to cap
  memory usage while preserving recent output
- **Snippet size limits**: Add warnings or automatic capping of `SAFE_SNIPPET_LINES`
  values to prevent accidentally printing extremely large outputs to stderr

These improvements are tracked as future work and will be evaluated based on real-world
usage patterns and community feedback.

## Future Enhancements

- **Performance:** Optimize buffering and I/O for high-throughput logs
- **Binary size:** Strip debug symbols, optimize for size
- **Additional commands:** Extend beyond safe-run/safe-check/safe-archive
- **Plugin architecture:** Allow custom event handlers
- **Telemetry:** Optional structured logging for debugging

## References

- [rfc-shared-agent-scaffolding-v0.1.0.md](../rfc-shared-agent-scaffolding-v0.1.0.md)
- [Wrapper Discovery](./wrapper-discovery.md)
- [Conformance Contract](../usage/conformance-contract.md)
- [EPIC #33: Rust Canonical Tool](https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/issues/33)
