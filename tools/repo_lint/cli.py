"""Click-based CLI entry point for repo_lint with Rich formatting.

:Purpose:
    Provides a modern command-line interface using Click with Rich formatting,
    shell completion support, and improved help text.

:Commands:
    - check: Run linting checks without modifying files
    - fix: Apply automatic fixes where possible (formatters only)
    - install: Install/bootstrap required linting tools (local only)

:Features:
    - Rich formatted help output
    - Shell completion support (bash, zsh, fish)
    - Improved error messages with colors and formatting
    - Context-aware help text

:Environment Variables:
    - REPO_LINT_*: Any Click option can be set via environment variables with REPO_LINT_ prefix
    - _REPO_LINT_COMPLETE: Used by shell completion systems (bash_source, zsh_source, fish_source)

:Exit Codes:
    - 0: All checks passed
    - 1: Linting violations found
    - 2: Required tools missing (CI mode)
    - 3: Internal error
    - 4: Unsafe mode policy violation (CI or missing confirmation)

:Examples:
    Run checks in local mode::

        repo-lint check

    Run checks in CI mode::

        repo-lint check --ci

    Apply fixes::

        repo-lint fix

    Enable shell completion::

        # For Bash
        _REPO_LINT_COMPLETE=bash_source repo-lint > ~/.repo-lint-complete.bash
        source ~/.repo-lint-complete.bash

        # For Zsh
        _REPO_LINT_COMPLETE=zsh_source repo-lint > ~/.repo-lint-complete.zsh
        source ~/.repo-lint-complete.zsh

        # For Fish
        _REPO_LINT_COMPLETE=fish_source repo-lint > ~/.config/fish/completions/repo-lint.fish
"""

import sys

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from tools.repo_lint.cli_argparse import cmd_check, cmd_fix, cmd_install
from tools.repo_lint.common import ExitCode, MissingToolError

# Initialize Rich console for formatted output
console = Console()


# Custom Click group with rich help formatting
class RichGroup(click.Group):
    """Click Group with Rich-formatted help.

    Provides enhanced help output with Rich formatting including tables and panels.
    """

    def format_help(self, ctx, formatter):
        """Format help with Rich styling.

        :param ctx: Click context object
        :param formatter: Click formatter object
        """
        console.print(
            Panel.fit(
                f"[bold cyan]{self.name or 'repo-lint'}[/bold cyan]\n\n"
                f"{self.help or 'Unified multi-language linting and docstring validation'}",
                title="[bold]Repository Linter[/bold]",
                border_style="cyan",
            )
        )

        if self.commands:
            table = Table(title="Commands", show_header=True, header_style="bold magenta")
            table.add_column("Command", style="cyan", no_wrap=True)
            table.add_column("Description")

            for name in sorted(self.list_commands(ctx)):
                cmd = self.get_command(ctx, name)
                if cmd and not cmd.hidden:
                    table.add_row(name, cmd.get_short_help_str(limit=60))

            console.print(table)
            console.print()

        console.print("[dim]Use 'repo-lint COMMAND --help' for more information on a specific command.[/dim]")
        console.print()


# Main CLI group
@click.group(cls=RichGroup, invoke_without_command=True)
@click.pass_context
@click.version_option(version="0.1.0", prog_name="repo-lint")
def cli(ctx):
    """Unified multi-language linting and docstring validation tool.

    repo-lint helps maintain code quality across multiple programming languages
    with consistent linting rules, docstring validation, and automatic formatting.

    :param ctx: Click context object
    """
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())


# Check command
@cli.command()
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show verbose output including passed checks",
)
@click.option(
    "--ci",
    "--no-install",
    "ci_mode",
    is_flag=True,
    help="CI mode: fail if tools are missing instead of installing",
)
@click.option(
    "--only",
    type=click.Choice(["python", "bash", "powershell", "perl", "yaml", "rust"], case_sensitive=False),
    help="Run checks for only the specified language",
)
@click.option(
    "--json",
    "use_json",
    is_flag=True,
    help="Output results in JSON format for CI debugging",
)
def check(verbose, ci_mode, only, use_json):
    """Run linting checks without modifying files.

    Performs comprehensive linting and docstring validation across all supported
    languages. By default, checks all languages found in the repository.

    :param verbose: Show verbose output including passed checks
    :param ci_mode: CI mode - fail if tools are missing instead of installing
    :param only: Run checks for only the specified language
    :param use_json: Output results in JSON format for CI debugging

    \b
    Examples:
        repo-lint check                  # Check all languages
        repo-lint check --only python    # Check only Python files
        repo-lint check --ci             # Run in CI mode (fail on missing tools)
        repo-lint check --json           # Output in JSON format
    """
    import argparse  # Local import - only needed for Namespace creation

    # Create a namespace object compatible with the existing cmd_check function
    args = argparse.Namespace(
        verbose=verbose,
        ci=ci_mode,
        only=only,
        json=use_json,
    )

    exit_code = cmd_check(args)
    sys.exit(exit_code)


# Fix command
@cli.command()
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show verbose output including passed checks",
)
@click.option(
    "--ci",
    "--no-install",
    "ci_mode",
    is_flag=True,
    help="CI mode: fail if tools are missing instead of installing",
)
@click.option(
    "--only",
    type=click.Choice(["python", "bash", "powershell", "perl", "yaml", "rust"], case_sensitive=False),
    help="Run fixes for only the specified language",
)
@click.option(
    "--json",
    "use_json",
    is_flag=True,
    help="Output results in JSON format for CI debugging",
)
@click.option(
    "--unsafe",
    is_flag=True,
    help="⚠️  DANGER: Enable unsafe fixers (REQUIRES --yes-i-know, FORBIDDEN in CI)",
)
@click.option(
    "--yes-i-know",
    "yes_i_know",
    is_flag=True,
    help="⚠️  DANGER: Confirm unsafe mode execution (REQUIRED with --unsafe)",
)
# pylint: disable=too-many-arguments,too-many-positional-arguments
def fix(verbose, ci_mode, only, use_json, unsafe, yes_i_know):
    """Apply automatic fixes (formatters only).

    Runs auto-formatters to fix code style issues. By default, only runs safe
    formatters. Unsafe mode is available for advanced users with --unsafe flag.

    :param verbose: Show verbose output including passed checks
    :param ci_mode: CI mode - fail if tools are missing instead of installing
    :param only: Run fixes for only the specified language
    :param use_json: Output results in JSON format for CI debugging
    :param unsafe: Enable unsafe fixers (REQUIRES --yes-i-know, FORBIDDEN in CI)
    :param yes_i_know: Confirm unsafe mode execution (REQUIRED with --unsafe)

    \b
    Safe Formatters:
        - Python: Black, Ruff autofix
        - YAML: yamllint --fix
        - PowerShell: PSScriptAnalyzer formatting
        - Perl: perltidy
        - Bash: shfmt

    \b
    Unsafe Mode (⚠️  Use with caution):
        The --unsafe flag enables experimental fixers that may change code behavior.
        This mode is FORBIDDEN in CI and requires --yes-i-know confirmation.
        Always review the generated patch before committing.

    \b
    Examples:
        repo-lint fix                    # Fix all languages (safe mode)
        repo-lint fix --only python      # Fix only Python files
        repo-lint fix --unsafe --yes-i-know  # Enable unsafe fixers (LOCAL ONLY)
    """
    import argparse  # Local import - only needed for Namespace creation

    # Create a namespace object compatible with the existing cmd_fix function
    args = argparse.Namespace(
        verbose=verbose,
        ci=ci_mode,
        only=only,
        json=use_json,
        unsafe=unsafe,
        yes_i_know=yes_i_know,
    )

    exit_code = cmd_fix(args)
    sys.exit(exit_code)


# Install command
@cli.command()
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show verbose output during installation",
)
@click.option(
    "--cleanup",
    is_flag=True,
    help="Remove repo-local tool installations",
)
def install(verbose, cleanup):
    """Install/bootstrap required linting tools.

    Installs Python-based linting tools (black, ruff, pylint, yamllint) in a
    repository-local virtual environment. Also provides installation instructions
    for language-specific tools (shellcheck, perltidy, etc.).

    :param verbose: Show verbose output during installation
    :param cleanup: Remove repo-local tool installations

    \b
    What gets installed:
        - Python tools: black, ruff, pylint, yamllint (auto-installed)
        - Instructions for: shellcheck, shfmt, perltidy, pwsh, etc.

    \b
    Examples:
        repo-lint install                # Install all auto-installable tools
        repo-lint install --cleanup      # Remove repo-local installations
        repo-lint install --verbose      # Show detailed progress
    """
    import argparse  # Local import - only needed for Namespace creation

    # Create a namespace object compatible with the existing cmd_install function
    args = argparse.Namespace(
        verbose=verbose,
        cleanup=cleanup,
    )

    exit_code = cmd_install(args)
    sys.exit(exit_code)


# Shell completion command (hidden, used by shell completion systems)
@cli.command(hidden=True)
@click.argument("shell", type=click.Choice(["bash", "zsh", "fish"]))
def completion(shell):
    """Generate shell completion script.

    This command is used internally by shell completion systems.
    See HOW-TO-USE-THIS-TOOL.md for setup instructions.

    :param shell: Shell type (bash, zsh, or fish)
    """
    # Click's built-in completion support handles this via _REPO_LINT_COMPLETE environment variable
    # This function exists as a placeholder for the command in help text


def main():
    """Main entry point for Click-based CLI."""
    try:
        cli(auto_envvar_prefix="REPO_LINT")  # pylint: disable=no-value-for-parameter
    except MissingToolError as e:
        # Print to stderr using Click's echo
        click.echo(f"❌ Error: {e}", err=True)
        click.echo("\nRun 'repo-lint install' to install missing tools", err=True)
        sys.exit(ExitCode.MISSING_TOOLS)
    except Exception as e:
        click.echo(f"❌ Internal error: {e}", err=True)
        sys.exit(ExitCode.INTERNAL_ERROR)


if __name__ == "__main__":
    main()
