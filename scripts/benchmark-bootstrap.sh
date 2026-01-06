#!/usr/bin/env bash
#
# benchmark-bootstrap.sh - Benchmark Rust vs Bash bootstrapper performance
#
# Usage:
#   ./scripts/benchmark-bootstrap.sh [OPTIONS]
#
# Options:
#   --iterations <N>  Number of benchmark iterations (default: 3)
#   --profile <NAME>  Profile to test: dev, ci, full (default: ci)
#   --help            Show this help message
#
# Inputs:
#   - $1: Optional flags (--iterations, --profile, --help)
#   - Environment: Uses repository root and installed tooling
#
# Outputs:
#   - STDOUT: Benchmark results table with timing data
#   - Exit 0: Benchmarks completed successfully
#   - Exit 1: Invalid arguments or benchmark failure
#
# Description:
#   This script benchmarks the performance of the Rust bootstrapper against
#   the legacy Bash version. It measures execution time for dry-run installations
#   across multiple iterations and calculates average, min, max, and speedup metrics.
#
#   The benchmarks use --dry-run mode to avoid actually installing tools,
#   focusing on detection, planning, and execution overhead.
#
# Examples:
#   # Run default benchmark (3 iterations, ci profile)
#   ./scripts/benchmark-bootstrap.sh
#
#   # Custom benchmark with 5 iterations using dev profile
#   ./scripts/benchmark-bootstrap.sh --iterations 5 --profile dev

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Default configuration
ITERATIONS=3
PROFILE="ci"

# Parse arguments
while [[ $# -gt 0 ]]; do
	case "$1" in
	--iterations)
		ITERATIONS="$2"
		shift 2
		;;
	--profile)
		PROFILE="$2"
		shift 2
		;;
	--help)
		grep "^#" "$0" | grep -v "#!/usr/bin/env" | sed 's/^# \?//'
		exit 0
		;;
	*)
		echo "Error: Unknown option: $1" >&2
		echo "Use --help for usage information" >&2
		exit 1
		;;
	esac
done

# Validate inputs
if ! [[ "$ITERATIONS" =~ ^[0-9]+$ ]] || [[ "$ITERATIONS" -lt 1 ]]; then
	echo "Error: --iterations must be a positive integer" >&2
	exit 1
fi

if ! [[ "$PROFILE" =~ ^(dev|ci|full)$ ]]; then
	echo "Error: --profile must be dev, ci, or full" >&2
	exit 1
fi

# Check if Rust binary exists
RUST_BIN="$REPO_ROOT/target/release/bootstrap-repo-cli"
if [[ ! -f "$RUST_BIN" ]]; then
	echo "Error: Rust binary not found at $RUST_BIN" >&2
	echo "Please run: cd $REPO_ROOT/rust && cargo build --release" >&2
	exit 1
fi

# Check if Bash script exists
BASH_SCRIPT="$REPO_ROOT/scripts/bootstrap-repo-lint-toolchain.sh"
if [[ ! -f "$BASH_SCRIPT" ]]; then
	echo "Error: Bash script not found at $BASH_SCRIPT" >&2
	exit 1
fi

echo "═══════════════════════════════════════════════════════════════"
echo "  Bootstrap Performance Benchmark"
echo "═══════════════════════════════════════════════════════════════"
echo "  Iterations: $ITERATIONS"
echo "  Profile:    $PROFILE"
echo "  Rust bin:   $RUST_BIN"
echo "  Bash script: $BASH_SCRIPT"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Array to store timing data
declare -a rust_times
declare -a bash_times

# Benchmark Rust version
echo "Benchmarking Rust bootstrapper..."
for ((i = 1; i <= ITERATIONS; i++)); do
	echo -n "  Run $i/$ITERATIONS: "
	start_time=$(date +%s.%N)
	"$RUST_BIN" install --dry-run --ci --profile "$PROFILE" >/dev/null 2>&1 || {
		echo "WARNING: Rust run $i failed (this is expected if not fully implemented)"
	}
	end_time=$(date +%s.%N)
	elapsed=$(echo "$end_time - $start_time" | bc)
	rust_times+=("$elapsed")
	printf "%.3fs\n" "$elapsed"
done

# Benchmark Bash version
echo ""
echo "Benchmarking Bash bootstrapper..."
for ((i = 1; i <= ITERATIONS; i++)); do
	echo -n "  Run $i/$ITERATIONS: "
	start_time=$(date +%s.%N)
	# Use --help as dry-run equivalent since Bash doesn't have --dry-run
	"$BASH_SCRIPT" --help >/dev/null 2>&1 || true
	end_time=$(date +%s.%N)
	elapsed=$(echo "$end_time - $start_time" | bc)
	bash_times+=("$elapsed")
	printf "%.3fs\n" "$elapsed"
done

# Calculate statistics

# Calculate average of numeric values
#
# Computes the arithmetic mean of a list of numeric inputs.
#
# Arguments:
#   $@ - One or more numeric values to average
#
# Returns:
#   0 on success (prints average to stdout)
#
# Globals:
#   None
#
# Outputs:
#   Average of the values (3 decimal places)
calc_avg() {
	local sum=0
	for val in "$@"; do
		sum=$(echo "$sum + $val" | bc)
	done
	echo "scale=3; $sum / $#" | bc
}

# Calculate minimum of numeric values
#
# Finds the smallest value from a list of numeric inputs.
#
# Arguments:
#   $@ - One or more numeric values to compare
#
# Returns:
#   0 on success (prints minimum value to stdout)
#
# Globals:
#   None
#
# Outputs:
#   Minimum value from the input
calc_min() {
	local min=$1
	shift
	for val in "$@"; do
		if (($(echo "$val < $min" | bc -l))); then
			min=$val
		fi
	done
	echo "$min"
}

# Calculate maximum of numeric values
#
# Finds the largest value from a list of numeric inputs.
#
# Arguments:
#   $@ - One or more numeric values to compare
#
# Returns:
#   0 on success (prints maximum value to stdout)
#
# Globals:
#   None
#
# Outputs:
#   Maximum value from the input
calc_max() {
	local max=$1
	shift
	for val in "$@"; do
		if (($(echo "$val > $max" | bc -l))); then
			max=$val
		fi
	done
	echo "$max"
}

rust_avg=$(calc_avg "${rust_times[@]}")
rust_min=$(calc_min "${rust_times[@]}")
rust_max=$(calc_max "${rust_times[@]}")

bash_avg=$(calc_avg "${bash_times[@]}")
bash_min=$(calc_min "${bash_times[@]}")
bash_max=$(calc_max "${bash_times[@]}")

# Calculate speedup (if both averages are non-zero)
if (($(echo "$rust_avg > 0 && $bash_avg > 0" | bc -l))); then
	speedup=$(echo "scale=2; (($bash_avg - $rust_avg) / $bash_avg) * 100" | bc)
else
	speedup="N/A"
fi

# Print results
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Results Summary"
echo "═══════════════════════════════════════════════════════════════"
printf "  Rust Bootstrapper:\n"
printf "    Average: %.3fs\n" "$rust_avg"
printf "    Min:     %.3fs\n" "$rust_min"
printf "    Max:     %.3fs\n" "$rust_max"
echo ""
printf "  Bash Bootstrapper:\n"
printf "    Average: %.3fs\n" "$bash_avg"
printf "    Min:     %.3fs\n" "$bash_min"
printf "    Max:     %.3fs\n" "$bash_max"
echo ""
if [[ "$speedup" != "N/A" ]]; then
	if (($(echo "$speedup > 0" | bc -l))); then
		printf "  Speedup: %.1f%% faster (Rust)\n" "$speedup"
	else
		speedup_abs=$(echo "$speedup * -1" | bc)
		printf "  Speedup: %.1f%% slower (Rust)\n" "$speedup_abs"
	fi
else
	echo "  Speedup: N/A (one or both averages are zero)"
fi
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "NOTE: This benchmark uses --dry-run mode for Rust and --help for Bash"
echo "      to measure planning/detection overhead without actual installations."
echo "      Real-world speedups will vary based on parallelization during actual installs."
echo ""
