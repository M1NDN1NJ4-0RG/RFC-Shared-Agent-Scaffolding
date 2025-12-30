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
    - --json: Output results in JSON format (future)

:Environment Variables:
    None - all configuration via command-line arguments

:Exit Codes:
    - 0: All checks passed
    - 1: Linting violations found
    - 2: Required tools missing (CI mode)
    - 3: Internal error

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

from tools.repo_lint.common import ExitCode, MissingToolError
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

    # fix command
    fix_parser = subparsers.add_parser("fix", help="Apply automatic fixes (formatters only)")
    fix_parser.add_argument("--verbose", "-v", action="store_true", help="Show verbose output")
    fix_parser.add_argument("--ci", "--no-install", action="store_true", help="CI mode: fail if tools are missing")
    fix_parser.add_argument(
        "--only",
        choices=["python", "bash", "powershell", "perl", "yaml", "rust"],
        help="Run fixes for only the specified language",
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

    # Define all runners
    all_runners = [
        ("python", "Python", PythonRunner(ci_mode=args.ci, verbose=args.verbose)),
        ("bash", "Bash", BashRunner(ci_mode=args.ci, verbose=args.verbose)),
        ("powershell", "PowerShell", PowerShellRunner(ci_mode=args.ci, verbose=args.verbose)),
        ("perl", "Perl", PerlRunner(ci_mode=args.ci, verbose=args.verbose)),
        ("yaml", "YAML", YAMLRunner(ci_mode=args.ci, verbose=args.verbose)),
        ("rust", "Rust", RustRunner(ci_mode=args.ci, verbose=args.verbose)),
    ]

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
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print(f"  {name} {mode}")
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

            missing_tools = runner.check_tools()
            if missing_tools:
                if args.ci:
                    print_install_instructions(missing_tools)
                    return ExitCode.MISSING_TOOLS
                print(f"⚠️  Missing tools: {', '.join(missing_tools)}")
                print("   Run 'python3 -m tools.repo_lint install' to install them")
                print("")
                return ExitCode.MISSING_TOOLS

            results = action_callback(runner)
            all_results.extend(results)
        else:
            if args.verbose:
                print(f"No {name} files found. Skipping {name} {mode.lower()}.")

    # Report results
    print("")
    return report_results(all_results, verbose=args.verbose)


def cmd_check(args: argparse.Namespace) -> int:
    """Run linting checks without modifying files.

    :param args: Parsed command-line arguments
    :returns: Exit code (0=success, 1=violations, 2=missing tools, 3=error)
    """
    print("🔍 Running repository linters and formatters...")
    print("")

    return _run_all_runners(args, "Linting", lambda runner: runner.check())


def cmd_fix(args: argparse.Namespace) -> int:
    """Apply automatic fixes where possible (formatters only).

    :param args: Parsed command-line arguments
    :returns: Exit code (0=success, 1=violations remain, 2=missing tools, 3=error)
    """
    print("🔧 Running formatters in fix mode...")
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

    # Pass policy to runners via callback
    return _run_all_runners(args, "Formatting", lambda runner: runner.fix(policy=policy))


def cmd_install(args: argparse.Namespace) -> int:
    """Install/bootstrap required linting tools.

    :param args: Parsed command-line arguments
    :returns: Exit code (0=success, 3=error)
    """
    # Handle cleanup mode
    if args.cleanup:
        print("🧹 Cleaning up repo-local tool installations...")
        print("")

        success, messages = cleanup_repo_local(verbose=args.verbose)

        for msg in messages:
            print(msg)

        print("")
        if success:
            print("✓ Cleanup complete")
            return ExitCode.SUCCESS
        else:
            print("✗ Cleanup completed with errors")
            return ExitCode.INTERNAL_ERROR

    # Normal install mode
    print("📦 Installing linting tools...")
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
    else:
        print("")
        print("✗ Python tool installation failed:")
        for error in errors:
            print(f"  {error}")
        print("")

    # Print manual install instructions for other tools
    print_bash_tool_instructions()
    print_powershell_tool_instructions()
    print_perl_tool_instructions()

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("")

    if success:
        print("✓ Installation complete")
        print("")
        print("Next steps:")
        print("  1. Follow the manual installation instructions above")
        print("  2. Run 'python3 -m tools.repo_lint check' to verify")
        return ExitCode.SUCCESS
    else:
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
