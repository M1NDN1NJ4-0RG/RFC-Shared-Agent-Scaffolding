#!/usr/bin/env bash
#
# benchmark-bootstrappers.sh - Benchmark Bash vs Rust Bootstrappers
#
# DESCRIPTION:
#   Compares performance of the Bash bootstrapper (bootstrap-repo-lint-toolchain.sh)
#   against the Rust bootstrapper (bootstrap-repo-cli) using hyperfine.
#
#   Runs two benchmark modes:
#   - Mode A: End-to-end installation (currently skipped due to Rust limitations)
#   - Mode B: Verification-only gate (repo-lint check --ci)
#
#   Mode B benchmarks the most common developer workflow: running linters/formatters
#   on existing code without reinstalling tooling.
#
# USAGE:
#   ./scripts/benchmarks/benchmark-bootstrappers.sh
#
# INPUTS:
#   Arguments:
#     None
#
#   Environment Variables:
#     None (creates its own environment setup)
#
# OUTPUTS:
#   Exit Codes:
#     0    Benchmarks completed successfully
#     1    Benchmark tool (hyperfine) failed
#
#   Stdout/Stderr:
#     Benchmark progress and results
#
#   Files Created:
#     /tmp/mode-b-bash.md    - Markdown table with Bash benchmark results
#     /tmp/mode-b-bash.json  - JSON data with Bash benchmark details
#     /tmp/mode-b-rust.md    - Markdown table with Rust benchmark results
#     /tmp/mode-b-rust.json  - JSON data with Rust benchmark details
#
# EXAMPLES:
#   # Run benchmarks
#   ./scripts/benchmarks/benchmark-bootstrappers.sh
#
#   # View results
#   cat /tmp/mode-b-bash.md
#
# NOTES:
#   - Requires hyperfine: cargo install hyperfine
#   - Repository must be bootstrapped before running
#   - Mode A (end-to-end) is skipped due to Rust bootstrapper requiring
#     pre-existing venv for pip operations
#   - Results are saved to /tmp and will be lost on system reboot

set -euo pipefail

# Determine repository root (script should be at scripts/benchmarks/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

echo "==== MODE A: END-TO-END 'REAL DEV' (WARM) ===="
echo "Note: Skipping Mode A due to Rust bootstrapper limitation (requires pre-existing venv)"
echo "This will be addressed in a future update. Mode B provides better signal anyway."
echo ""

# Ensure environment is set up for verify-only tests
echo "Setting up environment via Bash bootstrapper..."
./scripts/bootstrap-repo-lint-toolchain.sh >/dev/null 2>&1
echo "Environment ready."
echo ""

echo "==== MODE B: VERIFY-ONLY / SCAN-HEAVY ===="
echo "Benchmarking verification gate only (10 runs each)..."
echo ""

# Set up environment activation command
# Note: Using double quotes to allow variable expansion in the command string
ENV_SETUP="source .venv/bin/activate && PERL_HOME=\"\$HOME/perl5\" && export PERL_LOCAL_LIB_ROOT=\"\${PERL_HOME}\${PERL_LOCAL_LIB_ROOT:+:\${PERL_LOCAL_LIB_ROOT}}\" && export PERL_MB_OPT=\"--install_base \\\"\${PERL_HOME}\\\"\" && export PERL_MM_OPT=\"INSTALL_BASE=\${PERL_HOME}\" && export PERL5LIB=\"\${PERL_HOME}/lib/perl5\${PERL5LIB:+:\${PERL5LIB}}\" && export PATH=\"\${PERL_HOME}/bin\${PATH:+:\${PATH}}\""

# Mode B: Bash verification (via repo-lint check --ci)
echo "--- Bash Verification (repo-lint check --ci) ---"
hyperfine \
	--warmup 2 \
	--runs 10 \
	--shell bash \
	--export-markdown /tmp/mode-b-bash.md \
	--export-json /tmp/mode-b-bash.json \
	"$ENV_SETUP && repo-lint check --ci"

# Mode B: Rust verification (via bootstrap verify)
echo ""
echo "--- Rust Verification (bootstrap verify) ---"
hyperfine \
	--warmup 2 \
	--runs 10 \
	--export-markdown /tmp/mode-b-rust.md \
	--export-json /tmp/mode-b-rust.json \
	'./rust/target/release/bootstrap-repo-cli verify'

echo ""
echo "==== BENCHMARK COMPLETE ===="
echo "Results saved to /tmp/mode-b-*.md and /tmp/mode-b-*.json"
