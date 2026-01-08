# Mode A Benchmark Plan: End-to-End "Real Dev" (Warm)

**Status:** 📋 **PLANNED - NOT EXECUTED**

**Last Updated:** 2026-01-07

---

## Overview

This document outlines the plan for executing Mode A benchmarks as defined in Issue #248. Mode A benchmarks the complete
developer experience of installing tooling from scratch (after warming caches).

**Current Status:** Mode B (verification-only) benchmarks have been successfully completed. Mode A is deferred due to
Rust bootstrapper limitation requiring pre-existing virtual environment.

---

## Benchmark Goals

Mode A measures the **end-to-end installation performance** of both Bash and Rust bootstrappers, simulating a developer
setting up their environment for the first time (with warm network/package caches).

### What Mode A Tests

1. **Virtual environment creation** (if needed)
2. **Python package installation** (pip, setuptools, wheel, repo-lint)
3. **System tool installation** (ripgrep, actionlint, shellcheck, shfmt, etc.)
4. **Perl toolchain installation** (Perl::Critic, PPI)
5. **PowerShell toolchain installation** (PSScriptAnalyzer)
6. **Verification gate execution** (repo-lint check --ci)

### What Mode A Does NOT Test

- Cold network downloads (caches are warmed)
- Internet speed (we benchmark developer experience, not the network)
- CI/cloud environments (focused on local developer workflow)

---

## Prerequisites

### Current Blocker

**BLOCKER:** The Rust bootstrapper currently requires a pre-existing virtual environment for pip operations. While the actionlint detection issue (exit code 19 during verification) has been fixed, attempting fresh installation after removing `.venv` still fails during the Python toolchain installation phase.

**Issue:** When `.venv` doesn't exist, the Rust bootstrapper fails to create it before attempting pip operations.

**Status of Previous Fix:** The exit code 19 issue related to actionlint detection has been resolved (tools can now be
verified correctly). However, the fresh installation workflow (Mode A) remains blocked by the venv creation issue.

**Required Fix:** The Rust bootstrapper needs to be updated to:

1. Detect if `.venv` exists
2. Create `.venv` if it doesn't exist (using `python3 -m venv .venv` or equivalent)
3. Ensure pip operations run within the venv context even if venv was just created

**Note:** The verification workflow (Mode B) works correctly because it assumes the environment is already set up.

### Required Tools

- ✅ hyperfine v1.20.0 (already installed)
- ✅ Bash bootstrapper (`scripts/bootstrap-repo-lint-toolchain.sh`)
- ⚠️ Rust bootstrapper (`rust/target/release/bootstrap-repo-cli`) - needs fix for fresh installs

### Required Permissions

- Ability to delete and recreate `.venv` directory
- Ability to install system packages (may require sudo for some operations)

---

## Benchmark Methodology

### Preparation Steps

1. **Warm caches (CRITICAL)**

   ```bash
   # Run Bash bootstrapper once to populate all caches
   ./scripts/bootstrap-repo-lint-toolchain.sh
   
   # Run Rust bootstrapper once to populate any Rust-specific caches
   # IMPORTANT: Only run this if the venv creation fix has been implemented
   # Test first: rm -rf .venv && ./rust/target/release/bootstrap-repo-cli install --profile dev
   # If test passes, then:
   # ./rust/target/release/bootstrap-repo-cli install --profile dev
   ```

2. **Verify caches are warm**

   ```bash
   # Check pip cache
   ls ~/.cache/pip/
   
   # Check cargo cache
   ls ~/.cargo/registry/
   
   # Check system package manager cache
   # (varies by OS: apt cache, homebrew cache, etc.)
   ```

### Testing the Fix (Before Running Mode A)

Before executing Mode A benchmarks, verify the Rust bootstrapper can handle fresh installations:

```bash
# Test fresh installation
rm -rf .venv
./rust/target/release/bootstrap-repo-cli install --profile dev

# If successful (exit 0), proceed with Mode A benchmarks
# If fails, the venv creation blocker still exists
```

### Benchmark Execution (Bash)

**Command:**

```bash
hyperfine \
    --warmup 1 \
    --runs 5 \
    --export-markdown /tmp/mode-a-bash.md \
    --export-json /tmp/mode-a-bash.json \
    --prepare 'rm -rf .venv' \
    --shell bash \
    './scripts/bootstrap-repo-lint-toolchain.sh'
```

**Parameters:**

- `--warmup 1`: One warmup run (caches already warm from preparation)
- `--runs 5`: Five measured runs (less than Mode B because installation is slower)
- `--prepare 'rm -rf .venv'`: Remove venv before each run to ensure fresh install
- `--shell bash`: Use bash shell for proper environment handling

**Expected Duration:** ~5-10 minutes per run, total ~25-50 minutes

### Benchmark Execution (Rust)

**Command (BLOCKED - for reference):**

```bash
hyperfine \
    --warmup 1 \
    --runs 5 \
    --export-markdown /tmp/mode-a-rust.md \
    --export-json /tmp/mode-a-rust.json \
    --prepare 'rm -rf .venv' \
    './rust/target/release/bootstrap-repo-cli install --profile dev'
```

**Parameters:** Same as Bash

**Expected Duration:** TBD (expected to be faster than Bash due to parallel execution)

---

## Success Criteria

### Minimum Requirements

1. **Both bootstrappers complete successfully** (exit 0)
2. **At least 5 runs each** without failures
3. **Warm cache conditions maintained** throughout all runs
4. **Consistent results** (standard deviation < 10% of mean)

### Data to Capture

For each bootstrapper, capture:

- **Mean time** (average of 5 runs)
- **Standard deviation** (measure of consistency)
- **Min/Max times** (identify outliers)
- **P50 (Median)** and **P90** times
- **Individual run times** (for detailed analysis)
- **User/System time** (CPU vs I/O)

### Comparison Metrics

- **Absolute speedup:** Rust time vs Bash time
- **Percentage improvement:** (Bash - Rust) / Bash * 100%
- **Consistency comparison:** Which has lower variance?

---

## Expected Results

### Bash Bootstrapper

**Estimated:** 3-8 minutes per run (varies by system and cache state)

**Components:**

- Venv creation: ~3-5 seconds
- Python packages: ~30-60 seconds
- System tools: ~1-3 minutes (varies by package manager)
- Perl toolchain: ~30-90 seconds
- PowerShell toolchain: ~10-30 seconds
- Verification gate: ~43 seconds (from Mode B data)

### Rust Bootstrapper

**Estimated:** 1-4 minutes per run (parallel execution should be faster)

**Potential Advantages:**

- Parallel installation of independent tools
- Better progress tracking
- Optimized dependency resolution

**Potential Disadvantages:**

- Requires pre-existing venv (current blocker)
- May have different caching behavior

---

## Risks and Mitigations

### Risk: Cache Invalidation

**Problem:** Caches may be invalidated between runs

**Mitigation:**

1. Run all warmup steps before starting benchmarks
2. Monitor cache directories during benchmark
3. If cache invalidation detected, restart benchmark suite

### Risk: System Load Variation

**Problem:** Background processes may affect timing

**Mitigation:**

1. Close unnecessary applications before benchmarking
2. Run benchmarks during low-activity periods
3. Use `nice` or `ionice` to deprioritize other processes if needed
4. Monitor system load (`top`, `htop`) during benchmarks

### Risk: Network Flakiness

**Problem:** Even with warm caches, some operations may hit network

**Mitigation:**

1. Ensure all packages are fully cached before starting
2. Run benchmarks on stable network connection
3. If network errors occur, exclude that run and re-run

### Risk: File System Performance

**Problem:** SSD vs HDD, file system type can affect results

**Mitigation:**

1. Document hardware specs in results
2. Run benchmarks on same hardware for both bootstrappers
3. Note file system type (ext4, apfs, ntfs, etc.) in results

---

## Reporting Requirements

### Report Location

Create/update: `docs/ai-prompt/235/235-dev-benchmark-mode-a-results.md`

### Report Contents

1. **Executive Summary**
   - Which bootstrapper is faster?
   - By how much?
   - Key takeaways

2. **Test Environment**
   - OS and version
   - CPU model and core count
   - RAM amount
   - Disk type (SSD/HDD)
   - File system type
   - Python version
   - Go version
   - Rust version

3. **Methodology**
   - Exact commands used
   - Cache warming procedure
   - Number of runs
   - Any issues encountered

4. **Results Tables**
   - Summary statistics (mean, stddev, min, max, P50, P90)
   - Individual run times
   - Comparison table (Bash vs Rust)

5. **Analysis**
   - Performance comparison
   - Bottleneck identification
   - Consistency analysis
   - Recommendations

6. **Raw Data**
   - Links to JSON files
   - Markdown tables from hyperfine

---

## Implementation Checklist

### Before Starting

- [ ] Fix Rust bootstrapper to support fresh venv creation
- [ ] Verify fix works: `rm -rf .venv && ./rust/target/release/bootstrap-repo-cli install --profile dev`
- [ ] Warm all caches by running both bootstrappers once
- [ ] Install hyperfine if not present: `cargo install hyperfine`
- [ ] Close unnecessary applications
- [ ] Ensure stable network connection

### Execution

- [ ] Run Bash benchmark (5 runs)
- [ ] Save Bash results to `/tmp/mode-a-bash.{md,json}`
- [ ] Run Rust benchmark (5 runs)
- [ ] Save Rust results to `/tmp/mode-a-rust.{md,json}`
- [ ] Verify both result files exist and contain valid data

### Analysis

- [ ] Calculate summary statistics for both bootstrappers
- [ ] Compare mean times and identify speedup
- [ ] Analyze variance and consistency
- [ ] Identify any outliers and investigate causes
- [ ] Create comparison table

### Documentation

- [ ] Create `docs/ai-prompt/235/235-dev-benchmark-mode-a-results.md`
- [ ] Include all required sections (see Reporting Requirements)
- [ ] Update `docs/ai-prompt/248/248-summary.md` with Mode A completion
- [ ] Update `docs/ai-prompt/248/248-next-steps.md` to reflect completion

### Validation

- [ ] Run `repo-lint check --ci` to verify documentation
- [ ] Commit all changes
- [ ] Update PR description with Mode A results

---

## Future Enhancements

### Multi-Platform Testing

Run Mode A benchmarks on:

- [ ] Linux x86_64 (Ubuntu, Debian, Fedora)
- [ ] Linux ARM64 (Raspberry Pi, cloud ARM instances)
- [ ] macOS x86_64 (Intel Macs)
- [ ] macOS ARM64 (Apple Silicon)

### Multi-Profile Testing

Run Mode A benchmarks for all profiles:

- [ ] `--profile dev` (default)
- [ ] `--profile ci` (minimal)
- [ ] `--profile full` (everything)

### Cold vs Warm Comparison

Run Mode A benchmarks with:

- [ ] Cold caches (first install ever)
- [ ] Warm caches (subsequent installs)
- [ ] Compare the difference to understand cache impact

---

## References

- Issue #248: Bootstrapper parity + Dev benchmarks
- `docs/ai-prompt/235/235-dev-benchmark-results.md`: Mode B results
- `scripts/benchmarks/benchmark-bootstrappers.sh`: Current benchmark script
- `scripts/benchmarks/README.md`: Benchmark documentation

---

## Notes

- Mode A is the most comprehensive benchmark but also the slowest to run
- Results will vary significantly based on hardware and network
- Document everything: hardware, software versions, commands used
- Keep raw data files for future reference
- Consider running benchmarks multiple times on different days to account for variability
