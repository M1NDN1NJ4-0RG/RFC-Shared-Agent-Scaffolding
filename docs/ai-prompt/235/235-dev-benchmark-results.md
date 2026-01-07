# Dev Benchmark Results: Bash vs Rust Bootstrapper

**Date:** 2026-01-07  
**Issue:** M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding#248  
**Benchmark Tool:** hyperfine v1.20.0

---

## Executive Summary

This benchmark compares the performance of the Bash bootstrapper (`scripts/bootstrap-repo-lint-toolchain.sh`) against the Rust bootstrapper (`rust/target/release/bootstrap-repo-cli`), focusing on **verification-only operations** which represent the most common developer workflow.

**Key Findings:**
- ✅ Bash verification gate (`repo-lint check --ci`): **~43.2 seconds** (mean)
- ⚠️  Rust verification currently has implementation issues preventing benchmarking
- 📊 Bash verification shows consistent performance with low variance (σ=0.737s)

---

## Test Environment

### Machine Specifications
- **OS:** Linux 6.11.0-1018-azure (Ubuntu 24.04.1)
- **CPU:** AMD EPYC 7763 64-Core Processor
- **Cores:** 4 (available)
- **Architecture:** x86_64
- **Runner:** GitHub Actions hosted runner

### Software Versions
- **Bash Bootstrapper:** `scripts/bootstrap-repo-lint-toolchain.sh` (latest from main)
- **Rust Bootstrapper:** `bootstrap-repo-cli` (release build)
- **Python:** 3.x (in virtual environment)
- **repo-lint:** Latest from editable install

---

## Benchmark Methodology

### Mode A: End-to-End "Real Dev" (Warm)
**Status:** ⏭️ Skipped

**Reason:** The Rust bootstrapper currently has a limitation where it requires a pre-existing virtual environment for pip operations. When attempting fresh installation (after removing `.venv`), the Rust bootstrapper exits with code 19 during the Python toolchain installation phase.

**Issue:** `Error: Command failed: pip install --upgrade pip setuptools wheel`

This will be addressed in a future update to Phase 1 parity implementation.

### Mode B: Verify-Only / Scan-Heavy ✅
**Status:** Completed (Bash only)

This mode benchmarks the **verification gate** behavior, which is the most frequently used operation during development (running linters/formatters/checks on existing code).

**Commands Benchmarked:**
1. **Bash:** `repo-lint check --ci` (with full environment activation)
2. **Rust:** `bootstrap verify` (attempted, currently non-functional)

**Benchmark Parameters:**
- Warmup runs: 2
- Measured runs: 10
- Pre-condition: Environment already set up via Bash bootstrapper

---

## Results: Mode B (Verify-Only)

### Bash Verification: `repo-lint check --ci`

| Metric | Value |
|--------|-------|
| **Mean** | 43.178 s |
| **Std Dev** | 0.737 s |
| **Median** | 42.813 s |
| **Min** | 42.586 s |
| **Max** | 44.749 s |
| **User Time** | 43.954 s |
| **System Time** | 5.647 s |

#### Individual Run Times (seconds)
```
Run  1: 42.586
Run  2: 42.654
Run  3: 44.749  ← outlier (max)
Run  4: 43.829
Run  5: 43.843
Run  6: 42.616
Run  7: 42.602
Run  8: 42.856
Run  9: 43.276
Run 10: 42.769
```

#### Performance Characteristics
- **Consistency:** Very consistent performance across runs (σ=0.737s, ~1.7% variance)
- **Outliers:** One outlier at 44.75s (Run 3), likely due to system scheduling
- **P90:** ~43.84s (9th fastest run)
- **P50 (Median):** 42.81s

### Rust Verification: `bootstrap verify`

**Status:** ❌ Non-functional

**Exit Code:** 19  
**Error:** Command terminated during verification phase

**Root Cause:** Similar to the Mode A issue, the Rust bootstrapper's verification logic encounters an error. This suggests the parity implementation needs additional work to handle edge cases in the verification workflow.

---

## Analysis & Interpretation

### What We Learned

1. **Bash Verification is Stable:** The current Bash-based verification gate (`repo-lint check --ci`) runs consistently in ~43 seconds on this hardware, processing all linters, formatters, and validators across multiple languages (Python, Bash, PowerShell, Perl, YAML, Rust).

2. **Rust Parity Incomplete:** The Rust bootstrapper, while structurally present, has functional gaps preventing it from being used as a drop-in replacement for:
   - Fresh environment installation (exit code 19 during pip operations)
   - Verification-only workflows (exit code 19 during verify command)

3. **Performance Baseline Established:** We now have a solid baseline (~43s) for verification operations, which can be used to measure improvements when the Rust implementation is fixed.

### Behavioral Mismatches

| Aspect | Bash | Rust | Status |
|--------|------|------|--------|
| Fresh install | ✅ Works | ❌ Fails (exit 19) | **Mismatch** |
| Verify-only | ✅ Works (~43s) | ❌ Fails (exit 19) | **Mismatch** |
| repo-lint install | ✅ Automatic | ⚠️  Intended but non-functional | **Incomplete** |
| Verification gate | ✅ Automatic | ⚠️  Intended but non-functional | **Incomplete** |

---

## Recommendations

### Immediate Actions

1. **Fix Rust Bootstrapper Core Issues**
   - Debug and resolve exit code 19 errors in both install and verify workflows
   - Ensure `pip install --upgrade pip setuptools wheel` succeeds in fresh venv contexts
   - Verify that the verification gate logic properly handles the Python environment

2. **Re-run Benchmarks After Fixes**
   - Once the Rust bootstrapper is functional, re-run this benchmark suite
   - Compare Rust verification performance against the Bash baseline (~43s)
   - Measure end-to-end installation performance for both implementations

3. **Document Known Limitations**
   - Update user-facing documentation to clarify current state of Rust bootstrapper
   - Mark Rust bootstrapper as "experimental" or "in development" until parity is achieved

### Future Benchmark Iterations

When Rust bootstrapper is functional:
- Run Mode A (end-to-end) benchmarks with 5 iterations each
- Compare cold vs warm cache performance
- Measure memory usage and CPU utilization
- Benchmark parallel vs sequential installation strategies
- Test on multiple platforms (Linux x86_64, Linux ARM64, macOS)

---

## Appendix: Exact Commands Used

### Bash Verification Benchmark
```bash
hyperfine \
    --warmup 2 \
    --runs 10 \
    --shell bash \
    --export-markdown /tmp/mode-b-bash.md \
    --export-json /tmp/mode-b-bash.json \
    'source .venv/bin/activate && \
     PERL_HOME="$HOME/perl5" && \
     export PERL_LOCAL_LIB_ROOT="${PERL_HOME}${PERL_LOCAL_LIB_ROOT:+:${PERL_LOCAL_LIB_ROOT}}" && \
     export PERL_MB_OPT="--install_base \"${PERL_HOME}\"" && \
     export PERL_MM_OPT="INSTALL_BASE=${PERL_HOME}" && \
     export PERL5LIB="${PERL_HOME}/lib/perl5${PERL5LIB:+:${PERL5LIB}}" && \
     export PATH="${PERL_HOME}/bin${PATH:+:${PATH}}" && \
     repo-lint check --ci'
```

### Rust Verification Benchmark (Attempted)
```bash
hyperfine \
    --warmup 2 \
    --runs 10 \
    --export-markdown /tmp/mode-b-rust.md \
    --export-json /tmp/mode-b-rust.json \
    './rust/target/release/bootstrap-repo-cli verify'
```

---

## Conclusion

While we successfully established a performance baseline for the Bash bootstrapper's verification workflow (~43 seconds), the Rust bootstrapper initially had implementation gaps. The primary deliverable from this benchmark effort is:

1. ✅ **Established Bash baseline:** 43.2s ± 0.7s for `repo-lint check --ci`
2. ✅ **Identified Rust implementation gaps:** Exit code 19 errors (actionlint detection)
3. ✅ **Fixed Rust implementation gaps:** (2026-01-07 04:20 UTC)
   - Updated ActionlintInstaller to check Go bin directories
   - Fixed version parsing for multi-line output and 'v' prefix
   - Rust `bootstrap verify` now exits 0 successfully
4. ✅ **Documented test methodology:** Ready for re-use

**Status Update (2026-01-07):** The Rust bootstrapper verification issue has been fixed. The `bootstrap verify` command now works correctly and exits with code 0. Quick timing comparison shows:
- Bash `repo-lint check --ci`: ~46 seconds (runs full linting suite)
- Rust `bootstrap verify`: ~1.5 seconds (checks tool availability only)

Note: These commands perform different operations. `repo-lint check --ci` runs all linters/formatters/checks, while `bootstrap verify` only verifies that tools are installed and accessible. For a fair performance comparison, the Rust bootstrapper would need to implement a command that runs the full linting suite.

**Next Steps:** The Rust bootstrapper is now functional for verification. Future work could include implementing a Rust equivalent to `repo-lint check --ci` for performance comparison.
