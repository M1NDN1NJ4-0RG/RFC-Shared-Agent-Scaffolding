# Benchmark Scripts

This directory contains benchmark scripts for measuring performance of various repository tools and workflows.

## Available Benchmarks

### `benchmark-bootstrappers.sh`

Compares the performance of the Bash bootstrapper (`scripts/bootstrap-repo-lint-toolchain.sh`) against the Rust bootstrapper (`rust/target/release/bootstrap-repo-cli`).

**Prerequisites:**
- `hyperfine` installed (benchmark tool)
- Repository already bootstrapped once (for Mode B verification benchmarks)

**Usage:**
```bash
# Install hyperfine first
cargo install hyperfine

# Run the benchmark
./scripts/benchmarks/benchmark-bootstrappers.sh
```

**Output:**
- Results saved to `/tmp/mode-b-*.md` and `/tmp/mode-b-*.json`
- Markdown tables with timing statistics
- JSON files with detailed run data

**Current Limitations:**
- Mode A (end-to-end fresh install) benchmarks are skipped due to Rust bootstrapper implementation gaps
- Only Mode B (verify-only) benchmarks are executed
- Rust verify command currently fails, so only Bash baseline is measured

**See Also:**
- Full benchmark report: `docs/ai-prompt/235/235-dev-benchmark-results.md`
- Issue #248: Bootstrapper parity + dev benchmarks
