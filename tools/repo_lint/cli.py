"""Click-based CLI entry point for repo_lint with Rich-Click formatting.

:Purpose:
    Provides a modern command-line interface using Click with Rich-Click formatting,
    shell completion support, and comprehensive help text following Help Content Contract.

:Commands:
    - check: Run linting checks without modifying files
    - fix: Apply automatic fixes where possible (formatters only)
    - install: Install/bootstrap required linting tools (local only)

:Features:
    - Rich-Click formatted help output with option grouping
    - Shell completion support (bash, zsh, fish, PowerShell)
    - Reporter-based output routing (TTY vs CI modes)
    - Comprehensive help following Help Content Contract

:Environment Variables:
    - REPO_LINT_*: Any Click option can be set via environment variables with REPO_LINT_ prefix
    - REPO_LINT_UI_THEME: Path to custom UI theme YAML file
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

import rich_click as click

from tools.repo_lint.cli_argparse import cmd_check, cmd_fix, cmd_install
from tools.repo_lint.common import ExitCode, MissingToolError

# Configure rich-click globally
click.rich_click.USE_RICH_MARKUP = True
click.rich_click.USE_MARKDOWN = False
click.rich_click.SHOW_ARGUMENTS = True
click.rich_click.GROUP_ARGUMENTS_OPTIONS = True
click.rich_click.SHOW_METAVARS_COLUMN = False
click.rich_click.APPEND_METAVARS_HELP = True
click.rich_click.STYLE_ERRORS_SUGGESTION = "magenta italic"
click.rich_click.ERRORS_SUGGESTION = "Try running the '--help' flag for more information."
click.rich_click.ERRORS_EPILOGUE = ""
# Note: MAX_WIDTH controls help text formatting. This is independent of theme.help.width,
# which is stored in the theme YAML but not currently used (both set to 120 for consistency).
click.rich_click.MAX_WIDTH = 120
click.rich_click.COLOR_SYSTEM = "auto"  # Respect NO_COLOR environment variable

# Option groups for all commands (following Help Content Contract)
click.rich_click.OPTION_GROUPS = {
    "repo-lint": [],
    "repo-lint check": [
        {
            "name": "Output",
            "options": ["--ci", "--verbose", "--json"],
        },
        {
            "name": "Filtering",
            "options": ["--only"],
        },
    ],
    "repo-lint fix": [
        {
            "name": "Output",
            "options": ["--ci", "--verbose", "--json"],
        },
        {
            "name": "Filtering",
            "options": ["--only"],
        },
        {
            "name": "Safety",
            "options": ["--unsafe", "--yes-i-know"],
        },
    ],
    "repo-lint install": [
        {
            "name": "Execution",
            "options": ["--cleanup", "--verbose"],
        },
    ],
}


# Main CLI group
@click.group(invoke_without_command=True)
@click.pass_context
@click.version_option(version="0.1.0", prog_name="repo-lint")
def cli(ctx):
    """Unified multi-language linting and docstring validation tool.

    repo-lint helps maintain code quality across multiple programming languages
    with consistent linting rules, docstring validation, and automatic formatting.

    For detailed usage instructions, see: HOW-TO-USE-THIS-TOOL.md

    For shell completion setup, run: repo-lint --help

    :param ctx: Click context object (passed automatically by Click)
    """
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        sys.exit(0)


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
    help="CI mode: stable output, fail if tools missing, no interactive features",
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

    \b
    WHAT THIS DOES:
    Performs comprehensive linting and docstring validation across all supported
    languages. Scans repository files and reports violations without making changes.

    \b
    EXAMPLES:
    Example 1 — Most common usage:
      $ repo-lint check
      Scans all languages, shows violations, installs missing tools if needed

    Example 2 — CI usage:
      $ repo-lint check --ci
      Stable output for CI, fails if tools missing (no auto-install)

    Example 3 — Focused usage:
      $ repo-lint check --only python
      Check only Python files, skip other languages

    \b
    OUTPUT MODES:
    - Interactive (TTY): Rich formatting with colors, panels, and tables
    - CI mode (--ci): Stable, greppable output without ANSI colors or spinners
    - JSON mode (--json): Machine-readable JSON output for automation

    \b
    CONFIGURATION:
    Config files loaded from conformance/repo-lint/:
    - repo-lint-linting-rules.yaml: Tool configurations per language
    - repo-lint-naming-rules.yaml: Filename conventions
    - repo-lint-docstring-rules.yaml: Docstring requirements
    - repo-lint-ui-theme.yaml: UI colors and styling (interactive mode)

    \b
    EXIT CODES:
    - 0: All checks passed (no violations)
    - 1: Linting violations found
    - 2: Required tools missing (CI mode only)
    - 3: Internal error or exception

    \b
    TROUBLESHOOTING:
    - Missing tools: Run 'repo-lint install' to bootstrap Python tools
    - Config errors: Check YAML syntax in conformance/repo-lint/*.yaml
    - No files found: Ensure you're running from repository root
    - CI failures: Add '--ci' locally to reproduce CI environment

    See HOW-TO-USE-THIS-TOOL.md for detailed usage and examples.

    :param verbose: Show verbose output including passed checks
    :param ci_mode: CI mode - stable output, fail if tools missing
    :param only: Run only for specific language (python, bash, etc.)
    :param use_json: Output results in JSON format for CI debugging
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
    help="CI mode: stable output, fail if tools missing, no interactive features",
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

    \b
    WHAT THIS DOES:
    Runs auto-formatters to fix code style issues in-place. Only modifies files
    that need formatting. By default, only runs safe formatters that don't change
    code behavior. Unsafe mode available for advanced users with explicit confirmation.

    \b
    EXAMPLES:
    Example 1 — Most common usage:
      $ repo-lint fix
      Auto-format all files with safe formatters (Black, shfmt, perltidy, etc.)

    Example 2 — CI usage:
      $ repo-lint fix --ci
      Verify formatting in CI (fails if changes needed, doesn't modify files)

    Example 3 — Focused usage:
      $ repo-lint fix --only python
      Fix only Python files, skip other languages

    \b
    SAFE FORMATTERS:
    - Python: Black (code formatter), Ruff (auto-fixable rules)
    - YAML: yamllint --fix (whitespace/indentation)
    - Bash: shfmt (shell script formatter)
    - PowerShell: PSScriptAnalyzer formatting rules
    - Perl: perltidy (code formatter)
    - Rust: rustfmt (code formatter)

    \b
    UNSAFE MODE (⚠️ Use with extreme caution):
    The --unsafe flag enables experimental fixers that MAY change code behavior.
    - FORBIDDEN in CI environments (auto-detected via --ci or CI env vars)
    - REQUIRES --yes-i-know confirmation flag
    - Generates forensic report in repo-lint-failure-reports/
    - Always review generated patch before committing
    - Only supports Python currently (other languages error out)

    \b
    OUTPUT MODES:
    - Interactive (TTY): Rich formatting with action tables and summaries
    - CI mode (--ci): Stable, greppable output without ANSI colors or spinners
    - JSON mode (--json): Machine-readable JSON output for automation

    \b
    CONFIGURATION:
    Config files loaded from conformance/repo-lint/:
    - repo-lint-linting-rules.yaml: Tool configurations per language
    - repo-lint-ui-theme.yaml: UI colors and styling (interactive mode)

    \b
    EXIT CODES:
    - 0: All fixes applied successfully (or no fixes needed)
    - 1: Fixes applied but violations remain
    - 2: Required tools missing (CI mode only)
    - 3: Internal error or exception
    - 4: Unsafe mode policy violation (CI or missing confirmation)

    \b
    TROUBLESHOOTING:
    - Unsafe blocked in CI: This is intentional, unsafe mode only works locally
    - Unsafe without --yes-i-know: Add --yes-i-know to confirm you understand risks
    - Missing tools: Run 'repo-lint install' to bootstrap Python tools
    - Fixes not applied: Check file permissions and repo write access
    - Unsafe with non-Python: --unsafe only supports Python currently

    See HOW-TO-USE-THIS-TOOL.md for detailed usage, forensic reports, and examples.

    :param verbose: Show verbose output including passed checks
    :param ci_mode: CI mode - stable output, fail if tools missing
    :param only: Run only for specific language (python, bash, etc.)
    :param use_json: Output results in JSON format for CI debugging
    :param unsafe: Enable unsafe experimental fixers (DANGER - requires --yes-i-know)
    :param yes_i_know: Confirmation flag required for unsafe mode
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

    \b
    WHAT THIS DOES:
    Installs Python-based linting tools in a repository-local virtual environment
    (.venv-lint). Also provides installation instructions for language-specific
    tools that must be installed system-wide or via language package managers.

    \b
    EXAMPLES:
    Example 1 — Most common usage:
      $ repo-lint install
      Install Python tools and show instructions for other tools

    Example 2 — Cleanup:
      $ repo-lint install --cleanup
      Remove .venv-lint and reset to clean state

    Example 3 — Verbose mode:
      $ repo-lint install --verbose
      Show detailed progress and pip output

    \b
    WHAT GETS INSTALLED:
    Auto-installed (Python tools in .venv-lint):
    - black (v24.10.0): Python code formatter
    - ruff (v0.8.4): Fast Python linter
    - pylint (v3.3.2): Comprehensive Python linter
    - yamllint (v1.35.1): YAML linter

    Instructions provided (install manually):
    - shellcheck: Bash linter (apt/brew/choco)
    - shfmt: Bash formatter (apt/brew/choco/go install)
    - perltidy: Perl formatter (cpan)
    - Perl::Critic: Perl linter (cpan)
    - pwsh: PowerShell (download from Microsoft)
    - PSScriptAnalyzer: PowerShell linter (Install-Module)
    - rustfmt/clippy: Rust tools (rustup component add)

    \b
    OUTPUT MODES:
    - Interactive (TTY): Step-by-step checklist with tool status table
    - All modes: Clear instructions for manual tool installation

    \b
    CONFIGURATION:
    Tool versions are pinned in:
    - tools/repo_lint/install/version_pins.py (source of truth)
    - pyproject.toml [project.optional-dependencies] (synced)

    \b
    EXIT CODES:
    - 0: All auto-installable tools installed successfully
    - 3: Installation failed (Python tools or venv creation)

    \b
    TROUBLESHOOTING:
    - venv creation fails: Check Python 3.8+ is installed and working
    - pip install fails: Check network connectivity and pip version
    - Permission denied: Don't use sudo, installs to local .venv-lint
    - Cleanup removes everything: Cleanup deletes .venv-lint, you'll need to re-run install
    - Manual tools not found: Follow provided instructions for your OS

    See HOW-TO-USE-THIS-TOOL.md for detailed installation guide and OS-specific instructions.

    :param verbose: Show verbose output during installation
    :param cleanup: Remove repo-local tool installations (.venv-lint)
    """
    import argparse  # Local import - only needed for Namespace creation

    # Create a namespace object compatible with the existing cmd_install function
    args = argparse.Namespace(
        verbose=verbose,
        cleanup=cleanup,
    )

    exit_code = cmd_install(args)
    sys.exit(exit_code)


def main():
    """Main entry point for Click-based CLI with error handling."""
    try:
        cli(auto_envvar_prefix="REPO_LINT")  # pylint: disable=no-value-for-parameter
    except MissingToolError as e:
        # Use rich-click's echo for consistent output
        click.echo(f"❌ Error: {e}", err=True)
        click.echo("\nRun 'repo-lint install' to install missing tools", err=True)
        sys.exit(ExitCode.MISSING_TOOLS)
    except Exception as e:
        click.echo(f"❌ Internal error: {e}", err=True)
        import traceback

        # Check for verbose flag - check sys.argv since we're outside Click context
        # Note: This handles common cases but won't detect REPO_LINT_VERBOSE env var
        # or complex bundled options. For those edge cases, users can run with -v explicitly.
        verbose_flags = {"-v", "--verbose"}
        has_verbose = any(arg in verbose_flags or arg.startswith("--verbose=") for arg in sys.argv[1:])
        if has_verbose:
            traceback.print_exc()
        sys.exit(ExitCode.INTERNAL_ERROR)


if __name__ == "__main__":
    main()
