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
    all_results = []
    use_json = getattr(args, "json", False)

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
            print(f"⚠️  Naming validation skipped: {e}")
            print("")

    # Filter runners based on --only flag
    only_language = getattr(args, "only", None)
    if only_language:
        runners = [(key, name, runner) for key, name, runner in all_runners if key == only_language]
    else:
        runners = all_runners

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
    # Run each runner if it has files
    for key, name, runner in runners:
        if runner.has_files():
            # Skip progress output in JSON mode
            if not use_json:
                print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                print(f"  {name} {mode}")
                print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

            missing_tools = runner.check_tools()
            if missing_tools:
                if args.ci:
                    print_install_instructions(missing_tools, ci_mode=args.ci)
                    return ExitCode.MISSING_TOOLS
                print(f"⚠️  Missing tools: {', '.join(missing_tools)}")
                print("   Run 'repo-lint install' to install them")
                print("")
                return ExitCode.MISSING_TOOLS

            results = action_callback(runner)
            all_results.extend(results)
        else:
            if args.verbose and not use_json:
                print(f"No {name} files found. Skipping {name} {mode.lower()}.")

    # Run cross-language runners (only if --only not specified)
    if not only_language:
        for key, name, runner in cross_language_runners:
            if not use_json:
                print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                print(f"  {name} {mode}")
                print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

            results = action_callback(runner)
            all_results.extend(results)

    # Report results
    if not use_json:
        print("")

    # Use JSON or standard reporting based on flag
    if use_json:
        from tools.repo_lint.reporting import report_results_json

        return report_results_json(all_results, verbose=args.verbose)
    else:
        return report_results(all_results, verbose=args.verbose, ci_mode=args.ci)


def cmd_check(args: argparse.Namespace) -> int:
    """Run linting checks without modifying files.

    :param args: Parsed command-line arguments
    :returns: Exit code (0=success, 1=violations, 2=missing tools, 3=error)
    """
    use_json = getattr(args, "json", False)
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
        print("❌ UNSAFE MODE FORBIDDEN IN CI")
        print("")
        print("Unsafe fixes are not allowed in CI environments.")
        print("See: docs/contributing/ai-constraints.md")
        print("")
        return ExitCode.UNSAFE_VIOLATION  # Exit code 4 for policy violations

    # Guard: --unsafe requires --yes-i-know
    if unsafe_mode and not yes_i_know:
        print("❌ UNSAFE MODE BLOCKED FOR SAFETY")
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

    if not use_json:
        if unsafe_mode:
            print("⚠️  DANGER: Running in UNSAFE FIX MODE")
            safe_print("⚠️  Review the generated patch/log before committing!", "WARNING: Review the generated patch/log before committing!")
            print("")
        else:
            safe_print("🔧 Running formatters in fix mode...", "Running formatters in fix mode...")
            print("")

    # Load and validate auto-fix policy
    try:
        policy = load_policy()
        policy_errors = validate_policy(policy)
        if policy_errors:
            print("❌ Auto-fix policy validation failed:")
            for error in policy_errors:
                print(f"   {error}")
            print("")
            return ExitCode.INTERNAL_ERROR

        # Display policy summary
        if args.verbose:
            print(get_policy_summary(policy))
            print("")

    except FileNotFoundError:
        print("❌ Auto-fix policy file not found")
        print("   Expected: conformance/repo-lint/autofix-policy.json")
        print("")
        return ExitCode.INTERNAL_ERROR
    except Exception as e:
        print(f"❌ Failed to load auto-fix policy: {e}")
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
            print("❌ Unsafe fixes not supported for this language", file=sys.stderr)
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
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  Python Tools - Auto-Install")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("")

    success, errors = install_python_tools(verbose=args.verbose)

    if success:
        venv_path = get_venv_path()
        print("")
        print(f"✓ Python tools installed successfully in {venv_path}")
        print("")
        print("To use these tools in your shell:")
        print(f"  source {venv_path}/bin/activate  # Linux/macOS")
        print(f"  {venv_path}\\Scripts\\activate     # Windows")
        print("")

        # Print manual install instructions for other tools
        print_bash_tool_instructions()
        print_powershell_tool_instructions()
        print_perl_tool_instructions()

        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("")
        print("✓ Installation complete")
        print("")
        print("Next steps:")
        print("  1. Follow the manual installation instructions above")
        print("  2. Run 'python3 -m tools.repo_lint check' to verify")
        return ExitCode.SUCCESS
    else:
        print("")
        print("✗ Python tool installation failed:")
        for error in errors:
            print(f"  {error}")
        print("")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("")
        print("⚠️  Python tools are required for repo_lint to function.")
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
        print(f"❌ Error: {e}", file=sys.stderr)
        if getattr(args, "ci", False):
            sys.exit(ExitCode.MISSING_TOOLS)
        print("\nRun 'python3 -m tools.repo_lint install' to install missing tools", file=sys.stderr)
        sys.exit(ExitCode.MISSING_TOOLS)

    except Exception as e:
        print(f"❌ Internal error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(ExitCode.INTERNAL_ERROR)


if __name__ == "__main__":
    main()
