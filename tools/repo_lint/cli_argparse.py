"""CLI entry point and command handling for repo_lint.

:Purpose:
    Provides the command-line interface for repo_lint, handling argument parsing
    and dispatching to appropriate command handlers.

:Commands:
    - check: Run linting checks without modifying files
    - fix: Apply automatic fixes where possible (formatters only)
    - install: Install/bootstrap required linting tools (local only)

:Flags:
    - --ci/--no-install: CI mode - fail if tools are missing instead of installing
    - --verbose: Show verbose output including passed checks
    - --only <language>: Run checks for only the specified language
    - --json: Output results in JSON format for CI debugging

:Environment Variables:
    None - all configuration via command-line arguments

:Exit Codes:
    - 0: All checks passed
    - 1: Linting violations found
    - 2: Required tools missing (CI mode)
    - 3: Internal error
    - 4: Unsafe mode policy violation (CI or missing confirmation)

:Examples:
    Run checks in local mode::

        python3 -m tools.repo_lint check

    Run checks in CI mode::

        python3 -m tools.repo_lint check --ci

    Apply fixes::

        python3 -m tools.repo_lint fix
"""

from __future__ import annotations

import argparse
import sys

from tools.repo_lint.common import ExitCode, MissingToolError, safe_print
from tools.repo_lint.install.install_helpers import (
    cleanup_repo_local,
    get_venv_path,
    install_python_tools,
    print_bash_tool_instructions,
    print_perl_tool_instructions,
    print_powershell_tool_instructions,
)
from tools.repo_lint.policy import get_policy_summary, load_policy, validate_policy
from tools.repo_lint.reporting import print_install_instructions, report_results
from tools.repo_lint.runners.bash_runner import BashRunner
from tools.repo_lint.runners.naming_runner import NamingRunner
from tools.repo_lint.runners.perl_runner import PerlRunner
from tools.repo_lint.runners.powershell_runner import PowerShellRunner
from tools.repo_lint.runners.python_runner import PythonRunner
from tools.repo_lint.runners.rust_runner import RustRunner
from tools.repo_lint.runners.yaml_runner import YAMLRunner


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for repo_lint CLI.

    :returns: Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        prog="repo-lint",
        description="Unified multi-language linting and docstring validation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # check command
    check_parser = subparsers.add_parser("check", help="Run linting checks without modifying files")
    check_parser.add_argument("--verbose", "-v", action="store_true", help="Show verbose output")
    check_parser.add_argument("--ci", "--no-install", action="store_true", help="CI mode: fail if tools are missing")
    check_parser.add_argument(
        "--only",
        choices=["python", "bash", "powershell", "perl", "yaml", "rust"],
        help="Run checks for only the specified language",
    )
    check_parser.add_argument("--json", action="store_true", help="Output results in JSON format for CI debugging")
    check_parser.add_argument(
        "--include-fixtures",
        action="store_true",
        help="Include test fixture files in scans (vector mode for testing)",
    )
    check_parser.add_argument(
        "--jobs",
        "-j",
        type=int,
        default=None,
        metavar="N",
        help="Number of parallel jobs (default: AUTO based on CPU count, env: REPO_LINT_JOBS)",
    )

    # fix command
    fix_parser = subparsers.add_parser("fix", help="Apply automatic fixes (formatters only)")
    fix_parser.add_argument("--verbose", "-v", action="store_true", help="Show verbose output")
    fix_parser.add_argument("--ci", "--no-install", action="store_true", help="CI mode: fail if tools are missing")
    fix_parser.add_argument(
        "--only",
        choices=["python", "bash", "powershell", "perl", "yaml", "rust"],
        help="Run fixes for only the specified language",
    )
    fix_parser.add_argument("--json", action="store_true", help="Output results in JSON format for CI debugging")
    fix_parser.add_argument(
        "--include-fixtures",
        action="store_true",
        help="Include test fixture files in scans (vector mode for testing)",
    )
    fix_parser.add_argument(
        "--unsafe",
        action="store_true",
        help=(
            "DANGER: Enable unsafe fixers "
            "(REQUIRES --yes-i-know, FORBIDDEN in CI, see docs/contributing/ai-constraints.md)"
        ),
    )
    fix_parser.add_argument(
        "--yes-i-know",
        action="store_true",
        help=(
            "DANGER: Confirm unsafe mode execution "
            "(REQUIRED with --unsafe, review generated patch before committing)"
        ),
    )

    # install command
    install_parser = subparsers.add_parser("install", help="Install/bootstrap required linting tools")
    install_parser.add_argument("--verbose", "-v", action="store_true", help="Show verbose output")
    install_parser.add_argument("--cleanup", action="store_true", help="Remove repo-local tool installations")

    return parser


def _run_all_runners(args: argparse.Namespace, mode: str, action_callback) -> int:
    """Run all language runners with common logic.

    :param args: Parsed command-line arguments
    :param mode: Mode description for output ("Linting" or "Formatting")
    :param action_callback: Callable that takes a runner and returns results
    :returns: Exit code (0=success, 1=violations, 2=missing tools, 3=error)
    """
    import os
    from concurrent.futures import ThreadPoolExecutor, as_completed

    all_results = []
    use_json = getattr(args, "json", False)
    jobs = getattr(args, "jobs", 1)

    # Check for kill switch
    if os.getenv("REPO_LINT_DISABLE_CONCURRENCY", "").lower() in ("1", "true", "yes"):
        jobs = 1
        if args.verbose and not use_json:
            safe_print(
                "⚠️  Concurrency disabled via REPO_LINT_DISABLE_CONCURRENCY",
                "WARNING: Concurrency disabled via REPO_LINT_DISABLE_CONCURRENCY",
            )

    # Debug timing mode
    debug_timing = os.getenv("REPO_LINT_DEBUG_TIMING", "").lower() in ("1", "true", "yes")

    # Define all runners
    all_runners = [
        ("python", "Python", PythonRunner(ci_mode=args.ci, verbose=args.verbose)),
        ("bash", "Bash", BashRunner(ci_mode=args.ci, verbose=args.verbose)),
        ("powershell", "PowerShell", PowerShellRunner(ci_mode=args.ci, verbose=args.verbose)),
        ("perl", "Perl", PerlRunner(ci_mode=args.ci, verbose=args.verbose)),
        ("yaml", "YAML", YAMLRunner(ci_mode=args.ci, verbose=args.verbose)),
        ("rust", "Rust", RustRunner(ci_mode=args.ci, verbose=args.verbose)),
    ]

    # Add cross-language runners (run on all files, not language-specific)
    # Naming runner runs separately after language-specific checks
    cross_language_runners = []
    try:
        cross_language_runners.append(("naming", "Naming Conventions", NamingRunner()))
    except Exception as e:
        # If naming runner fails to initialize (e.g., config missing), skip it
        if args.verbose and not use_json:
            safe_print(f"⚠️  Naming validation skipped: {e}", f"WARNING: Naming validation skipped: {e}")
            print("")

    # Filter runners based on --only flag
    only_language = getattr(args, "only", None)
    tool_filter = getattr(args, "tool", None)  # List of tools to filter to

    if only_language:
        runners = [(key, name, runner) for key, name, runner in all_runners if key == only_language]
    else:
        runners = all_runners

    # Apply tool filtering: pass tool filter to each runner
    if tool_filter:
        for _, _, runner in runners:
            if hasattr(runner, "set_tool_filter"):
                runner.set_tool_filter(tool_filter)

    # If --only was used, ensure there is something to run
    if only_language:
        if not runners:
            print(f"Error: unknown language '{only_language}' for --only flag.", file=sys.stderr)
            return ExitCode.INTERNAL_ERROR
        if not any(runner.has_files() for _, _, runner in runners):
            print(
                f"Error: No files found for language '{only_language}'. " f"Nothing to {mode.lower()}.",
                file=sys.stderr,
            )
            return ExitCode.INTERNAL_ERROR

    # Apply changed-only filtering if --changed-only was specified
    changed_only = getattr(args, "changed_only", False)
    if changed_only:
        for _, _, runner in runners:
            if hasattr(runner, "set_changed_only"):
                runner.set_changed_only(True)

    # Apply include-fixtures filtering if --include-fixtures was specified
    include_fixtures = getattr(args, "include_fixtures", False)
    if include_fixtures:
        for _, _, runner in runners:
            if hasattr(runner, "set_include_fixtures"):
                runner.set_include_fixtures(True)

    # Check for fail-fast mode
    fail_fast = getattr(args, "fail_fast", False)
    max_violations = getattr(args, "max_violations", None)

    # Helper function to run a single runner
    def run_single_runner(key, name, runner):
        """Run a single runner.

        :param key: Runner key (e.g., "python")
        :param name: Display name (e.g., "Python")
        :param runner: Runner instance
        :returns: Tuple of (key, name, results, timing_info, error_msg)
        """
        import time

        error_msg = None
        results = []
        start_time = time.time()

        try:
            if not runner.has_files():
                return (key, name, results, time.time() - start_time, error_msg)

            # Check for missing tools
            missing_tools = runner.check_tools()
            if missing_tools:
                error_msg = f"Missing tools: {', '.join(missing_tools)}"
                return (key, name, results, time.time() - start_time, error_msg)

            # Run the action callback (with optional tool-level parallelism)
            # For check mode with tool-level parallelism enabled, run tools in parallel
            enable_tool_parallelism = (
                mode == "Linting"
                and jobs > 1
                and os.getenv("REPO_LINT_TOOL_PARALLELISM", "").lower() in ("1", "true", "yes")
            )

            if enable_tool_parallelism and hasattr(runner, "check_parallel"):
                # Use parallel check if available
                results = runner.check_parallel(max_workers=min(jobs, 4))
            else:
                # Standard sequential execution
                results = action_callback(runner)

        except Exception as e:
            error_msg = f"Runner failed: {str(e)}"
            import traceback

            traceback.print_exc()

        duration = time.time() - start_time
        return (key, name, results, duration, error_msg)

    # Determine if we should use parallel execution
    # Only parallelize for 'check' mode (not 'fix')
    use_parallel = jobs > 1 and mode == "Linting"

    # Determine if we should show progress
    show_progress = getattr(args, "progress", False)
    # Auto-disable progress in CI or non-TTY unless explicitly enabled
    if show_progress and (use_json or not sys.stdout.isatty()):
        show_progress = False

    # Filter runners that have files
    runners_to_run = [(key, name, runner) for key, name, runner in runners if runner.has_files()]

    # Store runner outputs in order for deterministic printing
    runner_results = {}  # key -> (name, results, error_msg)
    runner_timings = {}

    if use_parallel and runners_to_run:
        # Parallel execution with ThreadPoolExecutor
        if not use_json and args.verbose:
            safe_print(
                f"🚀 Running {len(runners_to_run)} runners in parallel (jobs={jobs})",
                f"Running {len(runners_to_run)} runners in parallel (jobs={jobs})",
            )
            print("")

        # Use Rich Progress if available and progress is enabled
        if show_progress:
            try:
                from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                    TimeElapsedColumn(),
                ) as progress:
                    task = progress.add_task(f"Running {len(runners_to_run)} runners...", total=len(runners_to_run))

                    with ThreadPoolExecutor(max_workers=jobs) as executor:
                        # Submit all runners
                        future_to_runner = {
                            executor.submit(run_single_runner, key, name, runner): (key, name)
                            for key, name, runner in runners_to_run
                        }

                        # Collect results as they complete
                        for future in as_completed(future_to_runner):
                            key, name = future_to_runner[future]
                            try:
                                result_tuple = future.result()
                                runner_key, runner_name, results, duration, error_msg = result_tuple

                                # Store results in order
                                runner_results[runner_key] = (runner_name, results, error_msg)
                                runner_timings[runner_key] = duration

                                # Update progress
                                progress.update(task, advance=1, description=f"Completed {runner_name}")

                                # Handle errors
                                if error_msg:
                                    if "Missing tools" in error_msg:
                                        if args.ci:
                                            # Extract missing tools and print instructions
                                            print_install_instructions(
                                                [t.strip() for t in error_msg.split(":", 1)[1].split(",")],
                                                ci_mode=args.ci,
                                            )
                                            return ExitCode.MISSING_TOOLS
                                        safe_print(f"⚠️  {error_msg}", f"WARNING: {error_msg}")
                                        print("   Run 'repo-lint install' to install them")
                                        print("")
                                        return ExitCode.MISSING_TOOLS

                            except Exception as e:
                                safe_print(f"❌ Runner {name} failed: {e}", f"ERROR: Runner {name} failed: {e}")
                                if args.verbose:
                                    import traceback

                                    traceback.print_exc()
            except ImportError:
                # Fall back to non-progress version if Rich not available
                show_progress = False

        if not show_progress:
            # No progress bar version
            with ThreadPoolExecutor(max_workers=jobs) as executor:
                # Submit all runners
                future_to_runner = {
                    executor.submit(run_single_runner, key, name, runner): (key, name)
                    for key, name, runner in runners_to_run
                }

                # Collect results as they complete
                for future in as_completed(future_to_runner):
                    key, name = future_to_runner[future]
                    try:
                        result_tuple = future.result()
                        runner_key, runner_name, results, duration, error_msg = result_tuple

                        # Store results in order
                        runner_results[runner_key] = (runner_name, results, error_msg)
                        runner_timings[runner_key] = duration

                        # Handle errors
                        if error_msg:
                            if "Missing tools" in error_msg:
                                if args.ci:
                                    # Extract missing tools and print instructions
                                    print_install_instructions(
                                        [t.strip() for t in error_msg.split(":", 1)[1].split(",")], ci_mode=args.ci
                                    )
                                    return ExitCode.MISSING_TOOLS
                                safe_print(f"⚠️  {error_msg}", f"WARNING: {error_msg}")
                                print("   Run 'repo-lint install' to install them")
                                print("")
                                return ExitCode.MISSING_TOOLS

                    except Exception as e:
                        safe_print(f"❌ Runner {name} failed: {e}", f"ERROR: Runner {name} failed: {e}")
                        if args.verbose:
                            import traceback

                            traceback.print_exc()

        # Collect all results in deterministic order
        for key, name, runner in runners:
            if key in runner_results:
                runner_name, results, error_msg = runner_results[key]
                all_results.extend(results)

    else:
        # Sequential execution (original behavior)
        for key, name, runner in runners:
            if runner.has_files():
                # Skip progress output in JSON mode
                if not use_json:
                    safe_print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "=" * 70)
                    print(f"  {name} {mode}")
                    safe_print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "=" * 70)

                missing_tools = runner.check_tools()
                if missing_tools:
                    if args.ci:
                        print_install_instructions(missing_tools, ci_mode=args.ci)
                        return ExitCode.MISSING_TOOLS
                    safe_print(
                        f"⚠️  Missing tools: {', '.join(missing_tools)}",
                        f"WARNING: Missing tools: {', '.join(missing_tools)}",
                    )
                    print("   Run 'repo-lint install' to install them")
                    print("")
                    return ExitCode.MISSING_TOOLS

                results = action_callback(runner)
                all_results.extend(results)

                # If fail-fast is enabled and we have violations, stop
                if fail_fast and any(r.violations for r in results):
                    break

                # If max-violations is set and we've exceeded it, stop
                if max_violations and sum(len(r.violations) for r in all_results) >= max_violations:
                    break
            else:
                if args.verbose and not use_json:
                    print(f"No {name} files found. Skipping {name} {mode.lower()}.")

    # Run cross-language runners (only if --only not specified)
    if not only_language:
        for key, name, runner in cross_language_runners:
            if not use_json:
                safe_print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "=" * 70)
                print(f"  {name} {mode}")
                safe_print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "=" * 70)

            results = action_callback(runner)
            all_results.extend(results)

    # Print timing summary if debug mode is enabled
    if debug_timing and runner_timings and not use_json:
        print("")
        safe_print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "=" * 70)
        print("  Timing Summary (REPO_LINT_DEBUG_TIMING=1)")
        safe_print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "=" * 70)
        # Print in deterministic order
        for key, name, runner in runners:
            if key in runner_timings:
                duration = runner_timings[key]
                print(f"  {name:30s} {duration:6.2f}s")
        print("")

    # Report results
    if not use_json:
        print("")

    # Use JSON or standard reporting based on flag
    if use_json or getattr(args, "format", "rich") == "json":
        from tools.repo_lint.reporting import report_results_json

        return report_results_json(
            all_results,
            verbose=args.verbose,
            report_path=getattr(args, "report", None),
        )
    else:
        return report_results(
            all_results,
            verbose=args.verbose,
            ci_mode=args.ci,
            summary=getattr(args, "summary", False),
            summary_only=getattr(args, "summary_only", False),
            summary_format=getattr(args, "summary_format", "short"),
            show_files=getattr(args, "show_files", True),
            show_codes=getattr(args, "show_codes", True),
            max_violations=getattr(args, "max_violations", None),
            output_format=getattr(args, "format", "rich"),
            report_path=getattr(args, "report", None),
            reports_dir=getattr(args, "reports_dir", None),
        )


def cmd_check(args: argparse.Namespace) -> int:
    """Run linting checks without modifying files.

    :param args: Parsed command-line arguments
    :returns: Exit code (0=success, 1=violations, 2=missing tools, 3=error)
    """
    import os

    use_json = getattr(args, "json", False)

    # Calculate safe AUTO maximum for default behavior
    cpu = os.cpu_count() or 1
    auto_max = min(max(cpu - 1, 1), 8)  # Safe default: 1..8

    # Handle --jobs/-j with environment variable fallback and AUTO default
    jobs = getattr(args, "jobs", None)
    explicit_override = False  # Track if user explicitly set jobs
    source = None  # Track source of jobs value for warning

    # Precedence: 1) CLI flag, 2) env var, 3) AUTO
    if jobs is None:
        # Try environment variable
        env_jobs = os.getenv("REPO_LINT_JOBS")
        if env_jobs:
            try:
                jobs = int(env_jobs)
                explicit_override = True
                source = f"REPO_LINT_JOBS={env_jobs}"
            except ValueError:
                safe_print(
                    f"❌ Invalid REPO_LINT_JOBS value: '{env_jobs}' (must be an integer)",
                    f"ERROR: Invalid REPO_LINT_JOBS value: '{env_jobs}' (must be an integer)",
                )
                return ExitCode.INTERNAL_ERROR
        else:
            # AUTO: Conservative auto-detection
            jobs = auto_max
            source = "AUTO"

            if args.verbose and not use_json:
                safe_print(
                    f"ℹ️  Auto-detected {cpu} CPUs, using {jobs} parallel workers",
                    f"INFO: Auto-detected {cpu} CPUs, using {jobs} parallel workers",
                )
    else:
        explicit_override = True
        source = f"--jobs={jobs}"

    # Validate jobs count
    if jobs <= 0:
        safe_print(f"❌ Invalid jobs value: {jobs} (must be >= 1)", f"ERROR: Invalid jobs value: {jobs} (must be >= 1)")
        return ExitCode.INTERNAL_ERROR

    # Check for hard cap override (opt-in safety lock for CI/agents)
    hard_cap_enabled = os.getenv("REPO_LINT_HARD_CAP_JOBS", "").lower() in ("1", "true", "yes")

    # Safety warning banner when explicit override exceeds auto_max
    if explicit_override and jobs > auto_max:
        if hard_cap_enabled:
            # Hard cap enabled - cap the value and warn
            if not use_json:
                safe_print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "=" * 70)
                safe_print(
                    f"⚠️  HARD CAP ENABLED: Requested {jobs} workers exceeds safe maximum",
                    f"WARNING: HARD CAP ENABLED: Requested {jobs} workers exceeds safe maximum",
                )
                safe_print(
                    "⚠️  Hard cap enabled via REPO_LINT_HARD_CAP_JOBS",
                    "WARNING: Hard cap enabled via REPO_LINT_HARD_CAP_JOBS",
                )
                safe_print(
                    f"⚠️  Capping to {auto_max} workers (cpu={cpu}; auto_max=min(max(cpu-1,1),8))",
                    f"WARNING: Capping to {auto_max} workers (cpu={cpu}; auto_max=min(max(cpu-1,1),8))",
                )
                safe_print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "=" * 70)
                print("")
            jobs = auto_max
        else:
            # No hard cap - honor user request but warn
            if not use_json:
                safe_print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "=" * 70)
                safe_print(
                    f"⚠️  Requested {jobs} workers exceeds safe AUTO max {auto_max}",
                    f"WARNING: Requested {jobs} workers exceeds safe AUTO max {auto_max}",
                )
                safe_print(
                    f"    (cpu={cpu}; auto_max=min(max(cpu-1,1),8)={auto_max})",
                    f"    (cpu={cpu}; auto_max=min(max(cpu-1,1),8)={auto_max})",
                )
                safe_print(
                    f"⚠️  Proceeding with {jobs} workers as explicitly requested via {source}",
                    f"WARNING: Proceeding with {jobs} workers as explicitly requested via {source}",
                )
                safe_print(
                    "⚠️  High worker counts may cause resource exhaustion and flaky CI",
                    "WARNING: High worker counts may cause resource exhaustion and flaky CI",
                )
                safe_print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "=" * 70)
                print("")
            # jobs remains as requested - no capping

    # Store validated jobs count back in args for _run_all_runners
    args.jobs = jobs

    if not use_json:
        safe_print("🔍 Running repository linters and formatters...", "Running repository linters and formatters...")
        print("")

    return _run_all_runners(args, "Linting", lambda runner: runner.check())


def cmd_fix(args: argparse.Namespace) -> int:
    """Apply automatic fixes where possible (formatters only).

    :param args: Parsed command-line arguments
    :returns: Exit code (0=success, 1=violations remain, 2=missing tools, 3=error, 4=unsafe violation)
    """
    import os

    use_json = getattr(args, "json", False)
    unsafe_mode = getattr(args, "unsafe", False)
    yes_i_know = getattr(args, "yes_i_know", False)

    # Detect CI environment
    is_ci = args.ci or os.getenv("CI", "").lower() in ("true", "1", "yes")

    # Guard: Unsafe mode is forbidden in CI
    if unsafe_mode and is_ci:
        safe_print("❌ UNSAFE MODE FORBIDDEN IN CI", "ERROR: UNSAFE MODE FORBIDDEN IN CI")
        print("")
        print("Unsafe fixes are not allowed in CI environments.")
        print("See: docs/contributing/ai-constraints.md")
        print("")
        return ExitCode.UNSAFE_VIOLATION  # Exit code 4 for policy violations

    # Guard: --unsafe requires --yes-i-know
    if unsafe_mode and not yes_i_know:
        safe_print("❌ UNSAFE MODE BLOCKED FOR SAFETY", "ERROR: UNSAFE MODE BLOCKED FOR SAFETY")
        print("")
        print("The --unsafe flag requires --yes-i-know to actually execute.")
        print("Unsafe fixes can change behavior and MUST be reviewed before committing.")
        print("")
        print("To proceed (LOCAL ONLY, AFTER READING THE WARNINGS):")
        print("  python3 -m tools.repo_lint fix --unsafe --yes-i-know")
        print("")
        print("See: docs/contributing/ai-constraints.md")
        print("")
        return ExitCode.UNSAFE_VIOLATION  # Exit code 4 for policy violations

    # Check for dry-run mode
    dry_run = getattr(args, "dry_run", False)
    show_diff = getattr(args, "diff", False)

    if not use_json:
        if dry_run:
            safe_print(
                "🔍 DRY RUN: Showing what would be changed (no files modified)",
                "DRY RUN: Showing what would be changed",
            )
            if show_diff:
                safe_print(
                    "   Unified diffs will be shown for each change",
                    "   Unified diffs will be shown for each change",
                )
            print("")
        elif unsafe_mode:
            safe_print("⚠️  DANGER: Running in UNSAFE FIX MODE", "WARNING: DANGER: Running in UNSAFE FIX MODE")
            safe_print(
                "⚠️  Review the generated patch/log before committing!",
                "WARNING: Review the generated patch/log before committing!",
            )
            print("")
        else:
            safe_print("🔧 Running formatters in fix mode...", "Running formatters in fix mode...")
            print("")

    # Load and validate auto-fix policy
    try:
        policy = load_policy()
        policy_errors = validate_policy(policy)
        if policy_errors:
            safe_print("❌ Auto-fix policy validation failed:", "ERROR: Auto-fix policy validation failed:")
            for error in policy_errors:
                print(f"   {error}")
            print("")
            return ExitCode.INTERNAL_ERROR

        # Display policy summary
        if args.verbose:
            print(get_policy_summary(policy))
            print("")

    except FileNotFoundError:
        safe_print("❌ Auto-fix policy file not found", "ERROR: Auto-fix policy file not found")
        print("   Expected: conformance/repo-lint/autofix-policy.json")
        print("")
        return ExitCode.INTERNAL_ERROR
    except Exception as e:
        safe_print(f"❌ Failed to load auto-fix policy: {e}", f"ERROR: Failed to load auto-fix policy: {e}")
        print("")
        return ExitCode.INTERNAL_ERROR

    # If unsafe mode is enabled, run unsafe fixers
    if unsafe_mode:
        from datetime import datetime
        from pathlib import Path

        from tools.repo_lint.forensics import print_forensics_summary, save_forensics
        from tools.repo_lint.unsafe_fixers import apply_unsafe_fixes

        # Guard: Unsafe fixes only supported for Python
        only_language = getattr(args, "only", None)
        if only_language and only_language != "python":
            safe_print(
                "❌ Unsafe fixes not supported for this language", "ERROR: Unsafe fixes not supported for this language"
            )
            print("", file=sys.stderr)
            print("Unsafe mode currently only supports Python files.", file=sys.stderr)
            print(f"You specified: --only={only_language}", file=sys.stderr)
            print("", file=sys.stderr)
            print("Remove --unsafe flag or use --only=python", file=sys.stderr)
            print("", file=sys.stderr)
            return ExitCode.UNSAFE_VIOLATION

        # Collect all Python files to process
        # At this point, only_language is either "python" or None (all languages)
        repo_root = Path.cwd()
        all_files = []

        if only_language == "python" or only_language is None:
            all_files.extend(repo_root.rglob("*.py"))

        # Filter out common non-source directories and test fixtures
        all_files = [
            f
            for f in all_files
            if not any(
                part in f.parts
                for part in [".venv", ".venv-lint", "venv", "__pycache__", ".git", "dist", "conformance"]
            )
        ]

        start_time = datetime.now()
        results = apply_unsafe_fixes(all_files)
        end_time = datetime.now()

        # Generate forensics
        patch_path, log_path = save_forensics(results, start_time, end_time)
        print_forensics_summary(patch_path, log_path, results)

        # After unsafe fixes, run normal fix to clean up formatting
        if results:
            if not use_json:
                print("Running safe formatters to clean up after unsafe fixes...")
                print("")

    # Pass policy to runners via callback
    return _run_all_runners(args, "Formatting", lambda runner: runner.fix(policy=policy))


def cmd_install(args: argparse.Namespace) -> int:
    """Install/bootstrap required linting tools.

    :param args: Parsed command-line arguments
    :returns: Exit code (0=success, 3=error)
    """
    # Handle cleanup mode
    if args.cleanup:
        safe_print("🧹 Cleaning up repo-local tool installations...", "Cleaning up repo-local tool installations...")
        print("")

        success, messages = cleanup_repo_local(verbose=args.verbose)

        for msg in messages:
            print(msg)

        print("")
        if success:
            safe_print("✓ Cleanup complete", "Cleanup complete")
            return ExitCode.SUCCESS
        else:
            safe_print("✗ Cleanup completed with errors", "Cleanup completed with errors")
            return ExitCode.INTERNAL_ERROR

    # Normal install mode
    safe_print("📦 Installing linting tools...", "Installing linting tools...")
    print("")

    # Install Python tools (auto-installable)
    safe_print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "=" * 70)
    print("  Python Tools - Auto-Install")
    safe_print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "=" * 70)
    print("")

    success, errors = install_python_tools(verbose=args.verbose)

    if success:
        venv_path = get_venv_path()
        print("")
        safe_print(
            f"✓ Python tools installed successfully in {venv_path}",
            f"Python tools installed successfully in {venv_path}",
        )
        print("")
        print("To use these tools in your shell:")
        print(f"  source {venv_path}/bin/activate  # Linux/macOS")
        print(f"  {venv_path}\\Scripts\\activate     # Windows")
        print("")

        # Print manual install instructions for other tools
        print_bash_tool_instructions()
        print_powershell_tool_instructions()
        print_perl_tool_instructions()

        safe_print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "=" * 70)
        print("")
        safe_print("✓ Installation complete", "Installation complete")
        print("")
        print("Next steps:")
        print("  1. Follow the manual installation instructions above")
        print("  2. Run 'python3 -m tools.repo_lint check' to verify")
        return ExitCode.SUCCESS
    else:
        print("")
        safe_print("✗ Python tool installation failed:", "Python tool installation failed:")
        for error in errors:
            print(f"  {error}")
        print("")
        safe_print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "=" * 70)
        print("")
        safe_print(
            "⚠️  Python tools are required for repo_lint to function.",
            "WARNING: Python tools are required for repo_lint to function.",
        )
        print("   Please fix the errors above and try again.")
        print("")
        print("Common issues:")
        print("  - Python 3.8+ required")
        print("  - Ensure pip is up to date: python3 -m pip install --upgrade pip")
        print("  - Check network connectivity for package downloads")
        return ExitCode.INTERNAL_ERROR


def main() -> None:
    """Main entry point for repo_lint CLI.

    :returns: None (exits with appropriate code)
    """
    parser = create_parser()
    args = parser.parse_args()

    # If no command specified, show help
    if not args.command:
        parser.print_help()
        sys.exit(ExitCode.SUCCESS)

    # Dispatch to command handlers
    try:
        if args.command == "check":
            exit_code = cmd_check(args)
        elif args.command == "fix":
            exit_code = cmd_fix(args)
        elif args.command == "install":
            exit_code = cmd_install(args)
        else:
            parser.print_help()
            exit_code = ExitCode.INTERNAL_ERROR

        sys.exit(exit_code)

    except MissingToolError as e:
        safe_print(f"❌ Error: {e}", f"Error: {e}")
        if getattr(args, "ci", False):
            sys.exit(ExitCode.MISSING_TOOLS)
        print("\nRun 'python3 -m tools.repo_lint install' to install missing tools", file=sys.stderr)
        sys.exit(ExitCode.MISSING_TOOLS)

    except Exception as e:
        safe_print(f"❌ Internal error: {e}", f"Internal error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(ExitCode.INTERNAL_ERROR)


if __name__ == "__main__":
    main()
