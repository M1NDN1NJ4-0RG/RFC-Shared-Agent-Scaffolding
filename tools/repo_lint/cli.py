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
    - --json: Output results in JSON format (future)
"""

import argparse
import sys
from typing import List

from tools.repo_lint.common import ExitCode, MissingToolError
from tools.repo_lint.reporting import print_install_instructions, report_results


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for repo_lint CLI.

    :Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        prog="repo-lint",
        description="Unified multi-language linting and docstring validation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Global flags
    parser.add_argument("--verbose", "-v", action="store_true", help="Show verbose output")
    parser.add_argument("--ci", "--no-install", action="store_true", help="CI mode: fail if tools are missing")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format (not yet implemented)")

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # check command
    check_parser = subparsers.add_parser("check", help="Run linting checks without modifying files")
    check_parser.add_argument(
        "--language",
        "-l",
        action="append",
        help="Run only specific language(s): python, bash, powershell, perl, yaml",
    )

    # fix command
    fix_parser = subparsers.add_parser("fix", help="Apply automatic fixes (formatters only)")
    fix_parser.add_argument(
        "--language", "-l", action="append", help="Fix only specific language(s): python, bash, powershell, perl, yaml"
    )

    # install command
    install_parser = subparsers.add_parser("install", help="Install/bootstrap required linting tools")
    install_parser.add_argument("--tool", "-t", action="append", help="Install only specific tool(s)")

    return parser


def cmd_check(args: argparse.Namespace) -> int:
    """Run linting checks without modifying files.

    :Args:
        args: Parsed command-line arguments

    :Returns:
        Exit code (0=success, 1=violations, 2=missing tools, 3=error)
    """
    # Placeholder implementation - will be replaced with actual runner logic
    print("🔍 Running repository linters and formatters...")
    print("")

    # For now, just print a message that we're a stub
    print("⚠️  repo-lint check is not yet fully implemented")
    print("    This is a minimal stub implementation for Phase 1")
    print("")
    print("Next steps:")
    print("  - Implement per-language runners (Phase 3)")
    print("  - Add Ruff configuration (Phase 2)")
    print("  - Integrate with existing validate_docstrings.py")
    print("")

    return ExitCode.SUCCESS


def cmd_fix(args: argparse.Namespace) -> int:
    """Apply automatic fixes where possible (formatters only).

    :Args:
        args: Parsed command-line arguments

    :Returns:
        Exit code (0=success, 1=violations remain, 2=missing tools, 3=error)
    """
    print("🔧 Running formatters in fix mode...")
    print("")

    # Placeholder implementation
    print("⚠️  repo-lint fix is not yet fully implemented")
    print("    This is a minimal stub implementation for Phase 1")
    print("")
    print("Next steps:")
    print("  - Implement formatter runners (Black, shfmt)")
    print("  - Add fix mode to language runners")
    print("  - Re-run checks after fixing")
    print("")

    return ExitCode.SUCCESS


def cmd_install(args: argparse.Namespace) -> int:
    """Install/bootstrap required linting tools.

    :Args:
        args: Parsed command-line arguments

    :Returns:
        Exit code (0=success, 3=error)
    """
    print("📦 Installing linting tools...")
    print("")

    # Placeholder implementation
    print("⚠️  repo-lint install is not yet fully implemented")
    print("    This is a minimal stub implementation for Phase 1")
    print("")
    print("For now, please install tools manually:")
    print("  - Python: pip install black ruff pylint")
    print("  - Bash: apt-get install shellcheck && go install mvdan.cc/sh/v3/cmd/shfmt@v3.12.0")
    print("  - PowerShell: Install-Module -Name PSScriptAnalyzer")
    print("  - Perl: cpanm Perl::Critic")
    print("  - YAML: pip install yamllint")
    print("")

    return ExitCode.SUCCESS


def main() -> None:
    """Main entry point for repo_lint CLI.

    :Returns:
        None (exits with appropriate code)
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
        if args.ci:
            sys.exit(ExitCode.MISSING_TOOLS)
        print("\nRun 'repo-lint install' to install missing tools", file=sys.stderr)
        sys.exit(ExitCode.MISSING_TOOLS)

    except Exception as e:
        print(f"❌ Internal error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(ExitCode.INTERNAL_ERROR)


if __name__ == "__main__":
    main()
