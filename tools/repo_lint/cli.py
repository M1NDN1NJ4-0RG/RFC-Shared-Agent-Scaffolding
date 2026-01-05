"""Click-based CLI entry point for repo_lint with Rich-Click formatting.

:Purpose:
    Provides a modern command-line interface using Click with Rich-Click formatting,
    shell completion support, and comprehensive help text following Help Content Contract.

:Commands:
    - check: Run linting checks without modifying files
    - fix: Apply automatic fixes where possible (formatters only)
    - install: Install/bootstrap required linting tools (local only)
    - doctor: Diagnose installation and configuration
    - list-langs: List supported languages
    - list-tools: List available linting tools
    - tool-help: Show help for a specific tool
    - dump-config: Print fully-resolved configuration
    - validate-config: Validate a YAML configuration file
    - which: Show repo-lint environment information
    - env: Generate shell integration snippets
    - activate: Launch subshell with venv activated

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

:Notes:
    This module contains multiple CLI commands and naturally exceeds 1000 lines.
    The too-many-lines pylint warning is disabled as splitting this file would
    reduce cohesion of the CLI interface.
"""

from __future__ import annotations

# pylint: disable=too-many-lines
import json
import sys
from pathlib import Path

import rich_click as click
import yaml

from tools.repo_lint.cli_argparse import cmd_check, cmd_fix, cmd_install
from tools.repo_lint.common import ExitCode, MissingToolError, safe_print

# Config-type-specific allowed keys mapping
# Used by validate-config command to support custom schemas
CONFIG_TYPE_ALLOWED_KEYS = {
    "repo-lint-file-patterns": [
        "config_type",
        "version",
        "description",
        "languages",  # Required by validator
        "in_scope",
        "exclusions",
        "metadata",
    ],
    # Add more config types here as needed
}


def _resolve_language_filter(lang, only):
    """Resolve language filter from --lang and --only options.

    :Purpose:
        Handles precedence between --lang and deprecated --only options.
        Issues warning if both are specified.

    :param lang: Value from --lang option (or None)
    :param only: Value from --only option (or None)
    :returns: Resolved language filter (or None for all languages)

    :Notes:
        - --lang takes precedence over --only
        - "all" is treated as None (run all languages)
        - Warns if both options specified simultaneously
    """
    if lang and only:
        print(
            "⚠️  Warning: Both --lang and --only specified. Using --lang (--only is deprecated).",
            file=sys.stderr,
        )

    # Handle --lang / --only precedence: --lang takes priority
    # "all" is same as not specifying a language (run all)
    if lang:
        return None if lang == "all" else lang
    return only


def _escape_cmd_argument(arg: str) -> str:
    """Escape a string for safe use as a literal argument in a CMD command line.

    This function:
    - prefixes CMD metacharacters with ^ so they are treated literally
    - doubles % to avoid unintended environment variable expansion

    :param arg: The string to escape for CMD
    :returns: Escaped string safe for CMD command line
    """
    # First escape the caret itself
    escaped = arg.replace("^", "^^")
    # Escape other CMD metacharacters that can be used for command chaining
    for ch in ("&", "|", ">", "<", "(", ")"):
        escaped = escaped.replace(ch, "^" + ch)
    # Prevent environment variable expansion
    escaped = escaped.replace("%", "%%")
    return escaped


def _escape_powershell_command(command: str) -> str:
    """Escape a command string for safe execution in PowerShell.

    PowerShell uses backtick (`) as the escape character. This function escapes
    special characters that could be used for command injection.

    :param command: The command string to escape
    :returns: Escaped command safe for PowerShell -Command execution
    
    :Notes:
        This provides basic protection against injection via PowerShell metacharacters.
        Users should still avoid passing untrusted input to the --command flag.
    """
    # Escape PowerShell special characters
    # See: https://docs.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_special_characters
    special_chars = (";", "|", "&", "$", "`", "(", ")", "<", ">", '"', "'")
    escaped = command
    for char in special_chars:
        escaped = escaped.replace(char, "`" + char)
    return escaped


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
# Note: MAX_WIDTH controls help text formatting and is hardcoded here for consistency.
# The theme.help.width field exists in the theme YAML schema for potential future use
# but is not currently applied. If you need to customize help width, change this value
# here (and optionally update the theme YAML to match for documentation purposes).
click.rich_click.MAX_WIDTH = 120
click.rich_click.COLOR_SYSTEM = "auto"  # Respect NO_COLOR environment variable

# Option groups for all commands (following Help Content Contract)
click.rich_click.OPTION_GROUPS = {
    "repo-lint": [],
    "repo-lint check": [
        {
            "name": "Filtering",
            "options": ["--lang", "--only", "--tool", "--changed-only", "--include-fixtures"],
        },
        {
            "name": "Output",
            "options": ["--ci", "--verbose", "--json", "--format", "--summary", "--summary-only", "--summary-format"],
        },
        {
            "name": "Reporting",
            "options": ["--report", "--reports-dir", "--show-files", "--hide-files", "--show-codes", "--hide-codes"],
        },
        {
            "name": "Execution",
            "options": ["--max-violations", "--fail-fast"],
        },
    ],
    "repo-lint fix": [
        {
            "name": "Filtering",
            "options": ["--lang", "--only", "--tool", "--changed-only", "--include-fixtures"],
        },
        {
            "name": "Output",
            "options": ["--ci", "--verbose", "--json", "--format"],
        },
        {
            "name": "Safety",
            "options": ["--unsafe", "--yes-i-know", "--dry-run", "--diff"],
        },
    ],
    "repo-lint install": [
        {
            "name": "Execution",
            "options": ["--cleanup", "--verbose"],
        },
    ],
    "repo-lint doctor": [
        {
            "name": "Output",
            "options": ["--ci", "--format", "--report"],
        },
    ],
    "repo-lint dump-config": [
        {
            "name": "Output",
            "options": ["--format", "--config"],
        },
    ],
}


def _is_verbose_enabled() -> bool:
    """Check if verbose mode is enabled via CLI flags or environment variable.

    Note: This function checks sys.argv before Click parses arguments, so it may
    have false positives if 'verbose' appears as a value for another argument.
    In practice, this is acceptable for traceback display since the worst case
    is showing a traceback when not requested (better than hiding errors).

    :returns: True if verbose mode is enabled, False otherwise
    """
    import os

    # Check CLI flags
    # Look for exact -v or --verbose flags (not as substring of other args)
    verbose_flags = {"-v", "--verbose"}
    has_verbose_flag = any(arg in verbose_flags or arg.startswith("--verbose=") for arg in sys.argv[1:])

    # Check environment variable
    has_verbose_env = os.environ.get("REPO_LINT_VERBOSE", "").lower() in (
        "1",
        "true",
        "yes",
    )

    return has_verbose_flag or has_verbose_env


# Main CLI group
@click.group(invoke_without_command=True)
@click.pass_context
@click.version_option(version="0.1.0", prog_name="repo-lint")
def cli(ctx):
    """Unified multi-language linting and docstring validation tool.

    repo-lint helps maintain code quality across multiple programming languages
    with consistent linting rules, docstring validation, and automatic formatting.

    For detailed usage instructions, see: REPO-LINT-USER-MANUAL.md

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
    help="Run checks for only the specified language (deprecated: use --lang)",
)
@click.option(
    "--lang",
    type=click.Choice(["python", "bash", "powershell", "perl", "yaml", "rust", "all"], case_sensitive=False),
    help="Filter checks to specified language (python|bash|powershell|perl|yaml|rust|all)",
)
@click.option(
    "--tool",
    multiple=True,
    help="Filter to specific tool(s) - repeatable (e.g., --tool black --tool ruff)",
)
@click.option(
    "--changed-only",
    is_flag=True,
    help="Only check files changed in git (requires git repository)",
)
@click.option(
    "--include-fixtures",
    is_flag=True,
    help="Include test fixture files in scans (vector mode for testing)",
)
@click.option(
    "--json",
    "use_json",
    is_flag=True,
    help="Output results in JSON format for CI debugging",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["rich", "plain", "json", "yaml", "csv", "xlsx"], case_sensitive=False),
    help="Output format (rich=TTY default, plain=CI default, json/yaml/csv/xlsx=structured)",
)
@click.option(
    "--summary",
    is_flag=True,
    help="Show summary after results",
)
@click.option(
    "--summary-only",
    is_flag=True,
    help="Show ONLY summary (no individual violations)",
)
@click.option(
    "--summary-format",
    type=click.Choice(["short", "by-tool", "by-file", "by-code"], case_sensitive=False),
    help="Summary format (short=counts only, by-tool/by-file/by-code=grouped)",
)
@click.option(
    "--report",
    type=click.Path(),
    help="Write consolidated report to file (format auto-detected from extension)",
)
@click.option(
    "--reports-dir",
    type=click.Path(),
    help="Write per-tool reports + index summary to directory",
)
@click.option(
    "--show-files/--hide-files",
    default=True,
    help="Show/hide per-file breakdown in output",
)
@click.option(
    "--show-codes/--hide-codes",
    default=True,
    help="Show/hide tool rule IDs/codes in output",
)
@click.option(
    "--max-violations",
    type=int,
    help="Stop after N violations (for limiting output)",
)
@click.option(
    "--fail-fast",
    is_flag=True,
    help="Stop after first tool failure",
)
# pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals
def check(
    verbose,
    ci_mode,
    only,
    lang,
    tool,
    changed_only,
    include_fixtures,
    use_json,
    output_format,
    summary,
    summary_only,
    summary_format,
    report,
    reports_dir,
    show_files,
    show_codes,
    max_violations,
    fail_fast,
):
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
      $ repo-lint check --lang python --tool black --tool ruff
      Check only Python files with specific tools

    Example 4 — Summary usage:
      $ repo-lint check --summary-only --summary-format by-tool
      Show only summary grouped by tool

    Example 5 — Report generation:
      $ repo-lint check --report report.json --format json
      Generate JSON report for CI artifacts

    \b
    OUTPUT MODES:
    - Interactive (TTY): Rich formatting with colors, panels, and tables
    - CI mode (--ci): Stable, greppable output without ANSI colors or spinners
    - JSON mode (--json or --format json): Machine-readable JSON output
    - YAML/CSV/XLSX: Structured formats for reporting and analysis

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

    See REPO-LINT-USER-MANUAL.md for detailed usage and examples.

    :param verbose: Show verbose output including passed checks
    :param ci_mode: CI mode - stable output, fail if tools missing
    :param only: (Deprecated) Run only for specific language - use --lang instead
    :param lang: Filter checks to specified language
    :param tool: Filter to specific tool(s) (repeatable)
    :param changed_only: Only check files changed in git
    :param use_json: Output results in JSON format (deprecated: use --format json)
    :param output_format: Output format (rich|plain|json|yaml|csv|xlsx)
    :param summary: Show summary after results
    :param summary_only: Show ONLY summary (no individual violations)
    :param summary_format: Summary format (short|by-tool|by-file|by-code)
    :param report: Write consolidated report to file
    :param reports_dir: Write per-tool reports + index to directory
    :param show_files: Show per-file breakdown in output
    :param show_codes: Show tool rule IDs/codes in output
    :param max_violations: Stop after N violations
    :param fail_fast: Stop after first tool failure
    """
    import argparse  # Local import - only needed for Namespace creation

    # Resolve language filter with precedence and warning
    effective_lang = _resolve_language_filter(lang, only)

    # Create a namespace object compatible with the existing cmd_check function
    args = argparse.Namespace(
        verbose=verbose,
        ci=ci_mode,
        only=effective_lang,
        json=use_json,
        tool=list(tool) if tool else None,
        changed_only=changed_only,
        include_fixtures=include_fixtures,
        format=output_format,
        summary=summary,
        summary_only=summary_only,
        summary_format=summary_format,
        report=report,
        reports_dir=reports_dir,
        show_files=show_files,
        show_codes=show_codes,
        max_violations=max_violations,
        fail_fast=fail_fast,
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
    help="Run fixes for only the specified language (deprecated: use --lang)",
)
@click.option(
    "--lang",
    type=click.Choice(["python", "bash", "powershell", "perl", "yaml", "rust", "all"], case_sensitive=False),
    help="Filter fixes to specified language (python|bash|powershell|perl|yaml|rust|all)",
)
@click.option(
    "--tool",
    multiple=True,
    help="Filter to specific tool(s) - repeatable (e.g., --tool black --tool ruff)",
)
@click.option(
    "--changed-only",
    is_flag=True,
    help="Only fix files changed in git (requires git repository)",
)
@click.option(
    "--include-fixtures",
    is_flag=True,
    help="Include test fixture files in scans (vector mode for testing)",
)
@click.option(
    "--json",
    "use_json",
    is_flag=True,
    help="Output results in JSON format for CI debugging",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["rich", "plain", "json", "yaml"], case_sensitive=False),
    help="Output format (rich=TTY default, plain=CI default, json/yaml=structured)",
)
@click.option(
    "--unsafe",
    is_flag=True,
    help="WARNING: DANGER: Enable unsafe fixers (REQUIRES --yes-i-know, FORBIDDEN in CI)",
)
@click.option(
    "--yes-i-know",
    "yes_i_know",
    is_flag=True,
    help="WARNING: DANGER: Confirm unsafe mode execution (REQUIRED with --unsafe)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be changed without modifying files",
)
@click.option(
    "--diff",
    is_flag=True,
    help="Show unified diff previews (TTY-only)",
)
# pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals
def fix(
    verbose,
    ci_mode,
    only,
    lang,
    tool,
    changed_only,
    include_fixtures,
    use_json,
    output_format,
    unsafe,
    yes_i_know,
    dry_run,
    diff,
):
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

    Example 2 — Dry-run usage:
      $ repo-lint fix --dry-run --diff
      Preview what would be changed without modifying files

    Example 3 — Focused usage:
      $ repo-lint fix --lang python --tool black
      Fix only Python files with Black formatter

    Example 4 — Changed files only:
      $ repo-lint fix --changed-only
      Fix only files changed in git (requires git repository)

    \b
    SAFE FORMATTERS:
    - Python: Black (code formatter), Ruff (auto-fixable rules)
    - YAML: yamllint --fix (whitespace/indentation)
    - Bash: shfmt (shell script formatter)
    - PowerShell: PSScriptAnalyzer formatting rules
    - Perl: perltidy (code formatter)
    - Rust: rustfmt (code formatter)

    \b
    UNSAFE MODE (WARNING: Use with extreme caution):
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

    See REPO-LINT-USER-MANUAL.md for detailed usage, forensic reports, and examples.

    :param verbose: Show verbose output including passed checks
    :param ci_mode: CI mode - stable output, fail if tools missing
    :param only: (Deprecated) Run only for specific language - use --lang instead
    :param lang: Filter fixes to specified language
    :param tool: Filter to specific tool(s) (repeatable)
    :param changed_only: Only fix files changed in git
    :param use_json: Output results in JSON format (deprecated: use --format json)
    :param output_format: Output format (rich|plain|json|yaml)
    :param unsafe: Enable unsafe experimental fixers (DANGER - requires --yes-i-know)
    :param yes_i_know: Confirmation flag required for unsafe mode
    :param dry_run: Show what would be changed without modifying files
    :param diff: Show unified diff previews (TTY-only)
    """
    import argparse  # Local import - only needed for Namespace creation

    # Resolve language filter with precedence and warning
    effective_lang = _resolve_language_filter(lang, only)

    # Create a namespace object compatible with the existing cmd_fix function
    args = argparse.Namespace(
        verbose=verbose,
        ci=ci_mode,
        only=effective_lang,
        json=use_json,
        tool=list(tool) if tool else None,
        changed_only=changed_only,
        include_fixtures=include_fixtures,
        format=output_format,
        unsafe=unsafe,
        yes_i_know=yes_i_know,
        dry_run=dry_run,
        diff=diff,
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

    See REPO-LINT-USER-MANUAL.md for detailed installation guide and OS-specific instructions.

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


@cli.command()
@click.option(
    "--ci",
    is_flag=True,
    help="CI mode: stable output, fail on any errors",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["rich", "plain", "json", "yaml"], case_sensitive=False),
    help="Output format (rich=TTY default, plain=CI default, json/yaml=structured)",
)
@click.option(
    "--report",
    type=click.Path(),
    help="Write diagnostic report to file (format auto-detected from extension)",
)
def doctor(ci, output_format, report):
    """Diagnose repo-lint installation and configuration.

    \b
    WHAT THIS DOES:
    Performs comprehensive diagnostic checks of repo-lint's environment, configuration,
    and tool availability. Reports status of each check and suggests fixes for issues.

    \b
    EXAMPLES:
    Example 1 — Most common usage:
      $ repo-lint doctor
      Check everything and show detailed status

    Example 2 — CI usage:
      $ repo-lint doctor --ci
      Fail if any check fails (non-zero exit code)

    Example 3 — Report generation:
      $ repo-lint doctor --report doctor-report.json --format json
      Generate JSON diagnostic report for troubleshooting

    \b
    CHECKS PERFORMED:
    - Repository root detection
    - Virtual environment (.venv) existence and activation
    - Python version and sys.prefix validation
    - Tool registry loading (conformance/repo-lint/*.yaml configs)
    - Tool availability (black, ruff, pylint, shellcheck, etc.)
    - PATH sanity checks
    - Config file validity (YAML syntax, required fields, schema)

    \b
    OUTPUT MODES:
    - Interactive (TTY): Rich table with green/red status indicators
    - CI mode (--ci): Stable checklist output, fails on first error
    - JSON/YAML: Structured diagnostic data for automation

    \b
    EXIT CODES:
    - 0: All checks passed (environment healthy)
    - 1: Some checks failed (issues detected)
    - 3: Internal error or exception

    \b
    TROUBLESHOOTING:
    If doctor reports issues:
    - Missing tools: Run 'repo-lint install'
    - Config errors: Check YAML syntax in conformance/repo-lint/*.yaml
    - PATH issues: Ensure venv is activated or tools are on PATH
    - Venv not found: Run from repository root

    See REPO-LINT-USER-MANUAL.md for detailed troubleshooting guide.

    :param ci: CI mode - stable output, fail on any errors
    :param output_format: Output format (rich|plain|json|yaml)
    :param report: Write diagnostic report to file
    """
    import argparse  # Local import

    from tools.repo_lint.doctor import cmd_doctor

    args = argparse.Namespace(
        ci=ci,
        format=output_format,
        report=report,
    )

    exit_code = cmd_doctor(args)
    sys.exit(exit_code)


# List-langs command
@cli.command("list-langs")
def list_langs():
    """List supported languages.

    \b
    WHAT THIS DOES:
    Prints a list of all programming languages supported by repo-lint.

    \b
    EXAMPLES:
      $ repo-lint list-langs
      python
      bash
      powershell
      perl
      yaml
      rust

    Use with --lang option: repo-lint check --lang <LANGUAGE>

    :returns: Exit code 0
    """
    from tools.repo_lint.yaml_loader import load_linting_rules

    try:
        rules = load_linting_rules()
        languages = rules.get("languages", {})

        for lang in sorted(languages.keys()):
            print(lang)

        sys.exit(0)
    except Exception as e:
        print(f"❌ Error loading language registry: {e}", file=sys.stderr)
        sys.exit(1)


# List-tools command
@cli.command("list-tools")
@click.option(
    "--lang",
    type=click.Choice(["python", "bash", "powershell", "perl", "yaml", "rust"], case_sensitive=False),
    help="Filter tools to specific language",
)
def list_tools(lang):
    """List available linting tools.

    \b
    WHAT THIS DOES:
    Prints a list of all linting tools available in repo-lint, optionally filtered
    by language. Shows tool name, description, and whether it's a formatter or linter.

    \b
    EXAMPLES:
    Example 1 — All tools:
      $ repo-lint list-tools

    Example 2 — Python tools only:
      $ repo-lint list-tools --lang python
      black: Python code formatter (fix-capable)
      ruff: Fast Python linter (fix-capable)
      pylint: Comprehensive Python code analyzer

    Use with --tool option: repo-lint check --tool <TOOL>

    :param lang: Filter tools to specific language
    :returns: Exit code 0
    """
    from tools.repo_lint.yaml_loader import load_linting_rules

    try:
        rules = load_linting_rules()
        languages = rules.get("languages", {})

        if lang:
            if lang not in languages:
                print(f"❌ Unknown language: {lang}", file=sys.stderr)
                sys.exit(1)
            languages = {lang: languages[lang]}

        for lang_name, lang_config in sorted(languages.items()):
            if not lang or lang_name == lang:
                tools = lang_config.get("tools", {})
                if tools:
                    if not lang:  # Only print language header if showing all
                        print(f"\n{lang_name}:")
                    for tool_name, tool_config in sorted(tools.items()):
                        desc = tool_config.get("description", "")
                        fix_capable = tool_config.get("fix_capable", False)
                        fix_label = " (fix-capable)" if fix_capable else ""
                        print(f"  {tool_name}: {desc}{fix_label}")

        sys.exit(0)
    except Exception as e:
        print(f"❌ Error loading tool registry: {e}", file=sys.stderr)
        sys.exit(1)


# Tool-help command
@cli.command("tool-help")
@click.argument("tool")
def tool_help(tool):
    """Show help for a specific tool.

    \b
    WHAT THIS DOES:
    Displays detailed information about a specific linting tool, including:
    - Tool description and purpose
    - Which language(s) it supports
    - Whether it can auto-fix issues
    - Configuration file location
    - Version (if pinned)

    \b
    EXAMPLES:
      $ repo-lint tool-help black
      Tool: black
      Language: python
      Description: Python code formatter
      Fix capable: Yes
      Version: 24.10.0
      Config: pyproject.toml

    :param tool: Tool name (e.g., black, ruff, shellcheck)
    :returns: Exit code 0 if tool found, 1 if not found
    """
    from tools.repo_lint.yaml_loader import load_linting_rules

    try:
        rules = load_linting_rules()
        languages = rules.get("languages", {})

        for lang_name, lang_config in languages.items():
            tools = lang_config.get("tools", {})
            if tool in tools:
                tool_config = tools[tool]
                print(f"Tool: {tool}")
                print(f"Language: {lang_name}")
                print(f"Description: {tool_config.get('description', 'N/A')}")
                print(f"Fix capable: {'Yes' if tool_config.get('fix_capable', False) else 'No'}")
                version = tool_config.get("version")
                print(f"Version: {version if version else 'System version'}")
                config_file = tool_config.get("config_file")
                if config_file:
                    print(f"Config: {config_file}")
                sys.exit(0)

        print(f"❌ Tool not found: {tool}", file=sys.stderr)
        print("\nAvailable tools: Run 'repo-lint list-tools' to see all tools", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error loading tool registry: {e}", file=sys.stderr)
        sys.exit(1)


# Dump Config command
@cli.command("dump-config")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["yaml", "json"], case_sensitive=False),
    default="yaml",
    help="Output format (yaml or json)",
)
@click.option(
    "--config",
    "config_dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Custom config directory to load from",
)
def dump_config(output_format, config_dir):
    """Print fully-resolved configuration.

    \b
    WHAT THIS DOES:
    Displays the complete resolved configuration from all YAML config files,
    including:
    - Linting rules (tools, versions, settings)
    - Naming rules (file naming conventions)
    - Docstring rules (validation requirements)
    - File patterns (in-scope and exclusions)
    - Config source (where configs are loaded from)

    \b
    USE CASES:
    - Debug configuration issues
    - Verify custom configs are loaded correctly
    - Export configs for documentation
    - Understand default values and precedence

    \b
    EXAMPLES:
      # Show default config in YAML format
      $ repo-lint dump-config

      # Show config in JSON format
      $ repo-lint dump-config --format json

      # Show config from custom directory
      $ repo-lint dump-config --config /path/to/configs

    \b
    CONFIG PRECEDENCE:
    1. --config flag (explicit path)
    2. REPO_LINT_CONFIG_DIR environment variable
    3. Default: <repo_root>/conformance/repo-lint

    :param output_format: Output format (yaml or json)
    :param config_dir: Custom config directory path
    :returns: Exit code 0 on success, 1 on error
    """
    from tools.repo_lint.yaml_loader import get_all_configs, get_config_source, set_config_directory

    try:
        # Set custom config directory if provided
        if config_dir:
            set_config_directory(config_dir)

        # Get config source and all configs
        config_source = get_config_source()
        all_configs = get_all_configs()

        # Prepare output
        output = {"config_source": config_source, "configs": all_configs}

        # Print in requested format
        if output_format == "json":
            try:
                print(json.dumps(output, indent=2))
            except (TypeError, ValueError) as e:
                print(f"❌ Error serializing config to JSON: {e}", file=sys.stderr)
                sys.exit(1)
        else:  # yaml
            print(f"# Config source: {config_source}")
            print("---")
            try:
                yaml.dump(all_configs, sys.stdout, default_flow_style=False, sort_keys=False)
            except yaml.YAMLError as e:
                print(f"❌ Error serializing config to YAML: {e}", file=sys.stderr)
                sys.exit(1)
            print("...")

        sys.exit(0)
    except Exception as e:
        print(f"❌ Error loading configuration: {e}", file=sys.stderr)
        if _is_verbose_enabled():
            import traceback

            traceback.print_exc()
        sys.exit(1)


# Validate Config command
@cli.command("validate-config")
@click.argument(
    "config_path",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
)
def validate_config(config_path):
    """Validate a YAML configuration file.

    \b
    WHAT THIS DOES:
    Validates a repo-lint YAML configuration file without running any checks.
    Checks for:
    - Required YAML document markers (--- and ...)
    - Required fields (config_type, version, languages)
    - Unknown keys (strict validation)
    - Semantic version format
    - Config-type-specific schema requirements

    \b
    USE CASES:
    - Pre-flight validation before committing config changes
    - CI/CD config validation gates
    - Verify custom configs before using with --config
    - Debug config syntax/structure errors

    \b
    EXAMPLES:
      # Validate linting rules config
      $ repo-lint validate-config conformance/repo-lint/repo-lint-linting-rules.yaml

      # Validate custom config file
      $ repo-lint validate-config /path/to/custom-config.yaml

      # Use in CI (exits 0 if valid, 1 if invalid)
      $ repo-lint validate-config my-config.yaml && echo "Config valid!"

    \b
    EXIT CODES:
      0 = Configuration valid
      1 = Configuration invalid (validation errors printed)

    :param config_path: Path to YAML config file to validate
    :returns: Exit code 0 if valid, 1 if invalid
    """
    from tools.repo_lint.config_validator import ConfigValidationError, validate_config_file

    try:
        # Load YAML to get config_type
        with open(config_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        config_type = config.get("config_type", "unknown")

        # Get config-type-specific allowed keys from centralized mapping
        allowed_keys = CONFIG_TYPE_ALLOWED_KEYS.get(config_type)

        # Validate config file
        validate_config_file(config_path, config_type, allowed_keys=allowed_keys)

        # Success
        print(f"✅ Configuration valid: {config_path}")
        print(f"   Config type: {config_type}")
        print(f"   Version: {config.get('version', 'N/A')}")
        sys.exit(0)

    except ConfigValidationError as e:
        print(f"❌ Configuration validation failed: {config_path}", file=sys.stderr)
        print(f"   {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error validating configuration: {e}", file=sys.stderr)
        if _is_verbose_enabled():
            import traceback

            traceback.print_exc()
        sys.exit(1)


def main():
    """Main entry point for Click-based CLI with error handling."""
    try:
        cli(auto_envvar_prefix="REPO_LINT")  # pylint: disable=no-value-for-parameter
    except MissingToolError as e:
        # Use safe_print to handle Windows encoding
        safe_print(f"❌ Error: {e}", f"Error: {e}")
        print("\nRun 'repo-lint install' to install missing tools", file=sys.stderr)
        sys.exit(ExitCode.MISSING_TOOLS)
    except Exception as e:
        safe_print(f"❌ Internal error: {e}", f"Internal error: {e}")
        import traceback

        # Check if verbose mode is enabled (CLI flag or environment variable)
        if _is_verbose_enabled():
            traceback.print_exc()
        sys.exit(ExitCode.INTERNAL_ERROR)


# Which command
@cli.command("which")
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine parsing",
)
def which_cmd(output_json):
    """Show repo-lint environment information.

    \b
    WHAT THIS DOES:
    Displays diagnostic information about your repo-lint installation,
    including virtual environment location, Python executable, and
    detected shell environment.

    \b
    USE CASES:
    - Debug PATH or venv configuration issues
    - Verify repo-lint installation location
    - Check which Python is being used
    - Identify current shell for completion setup

    \b
    EXAMPLES:
      # Show human-readable environment info
      $ repo-lint which

      # Get JSON output for scripting
      $ repo-lint which --json

    \b
    OUTPUT INCLUDES:
    - Repository root directory
    - Resolved virtual environment path
    - Bin/Scripts directory (where executables live)
    - Activation script path
    - repo-lint executable location
    - Python executable location
    - sys.prefix and sys.base_prefix (venv detection)
    - Detected shell (for completion setup)

    :param output_json: If True, output JSON; otherwise pretty table
    :returns: Exit code 0 on success, 1 on error
    """
    import os
    import platform
    import shutil

    from tools.repo_lint.env.venv_resolver import (
        VenvNotFoundError,
        get_activation_script,
        get_venv_bin_dir,
        is_venv_active,
        resolve_venv,
    )
    from tools.repo_lint.runners.base import find_repo_root

    try:
        # Gather environment information
        repo_root = find_repo_root()
        try:
            venv_path = resolve_venv(repo_root=repo_root)
        except VenvNotFoundError:
            venv_path = None

        bin_dir = get_venv_bin_dir(venv_path) if venv_path else None
        activation_script = get_activation_script(venv_path) if venv_path else None

        # Find repo-lint executable
        repo_lint_exe = shutil.which("repo-lint")

        # Detect shell
        shell = os.environ.get("SHELL", "")
        if not shell and platform.system() == "Windows":
            # On Windows, try to detect PowerShell vs CMD
            if os.environ.get("PSModulePath"):
                shell = "powershell"
            else:
                shell = "cmd"
        else:
            # Extract shell name from path
            shell = Path(shell).name if shell else "unknown"

        info = {
            "repo_root": str(repo_root),
            "venv_path": str(venv_path) if venv_path else None,
            "venv_active": is_venv_active(),
            "bin_dir": str(bin_dir) if bin_dir else None,
            "activation_script": str(activation_script) if activation_script else None,
            "repo_lint_executable": repo_lint_exe,
            "python_executable": sys.executable,
            "sys_prefix": sys.prefix,
            "sys_base_prefix": sys.base_prefix,
            "detected_shell": shell,
            "platform": platform.system(),
        }

        if output_json:
            # JSON output for machine parsing
            print(json.dumps(info, indent=2))
        else:
            # Human-readable table output
            from rich.console import Console
            from rich.table import Table

            console = Console()
            table = Table(title="repo-lint Environment Information", show_header=True)
            table.add_column("Setting", style="cyan", no_wrap=True)
            table.add_column("Value", style="green")

            table.add_row("Repository Root", info["repo_root"])
            table.add_row(
                "Virtual Environment",
                info["venv_path"] or "[red]Not found[/red]",
            )
            table.add_row(
                "Venv Active",
                "[green]Yes[/green]" if info["venv_active"] else "[yellow]No[/yellow]",
            )
            table.add_row("Bin/Scripts Directory", info["bin_dir"] or "[dim]N/A[/dim]")
            table.add_row(
                "Activation Script",
                info["activation_script"] or "[dim]N/A[/dim]",
            )
            table.add_row(
                "repo-lint Executable",
                info["repo_lint_executable"] or "[red]Not found in PATH[/red]",
            )
            table.add_row("Python Executable", info["python_executable"])
            table.add_row("sys.prefix", info["sys_prefix"])
            table.add_row("sys.base_prefix", info["sys_base_prefix"])
            table.add_row("Detected Shell", info["detected_shell"])
            table.add_row("Platform", info["platform"])

            console.print(table)

            # Add warnings if issues detected
            if not info["venv_path"]:
                console.print("\n[yellow]⚠️  Warning:[/yellow] No virtual environment detected.")
                console.print("   Run: python3 -m venv .venv")

            if not info["repo_lint_executable"]:
                console.print("\n[yellow]⚠️  Warning:[/yellow] repo-lint not found in PATH.")
                console.print("   Activate your venv or run: pip install -e .")

            if info["venv_path"] and not info["venv_active"]:
                console.print("\n[yellow]⚠️  Warning:[/yellow] Virtual environment exists but is not active.")
                if activation_script:
                    console.print(f"   Run: source {activation_script}")

        sys.exit(0)

    except Exception as e:
        print(f"❌ Error gathering environment information: {e}", file=sys.stderr)
        sys.exit(1)


# Env command
@cli.command("env")
@click.option(
    "--venv",
    type=click.Path(exists=False, file_okay=False, dir_okay=True, path_type=Path),
    help="Explicit virtual environment path",
)
@click.option(
    "--shell",
    type=click.Choice(["bash", "zsh", "fish", "powershell"], case_sensitive=False),
    help="Generate snippet for specific shell (auto-detected if not specified)",
)
@click.option(
    "--install",
    "install_snippet",
    is_flag=True,
    help="Write snippet to config directory (does NOT auto-edit rc files)",
)
@click.option(
    "--path-only",
    is_flag=True,
    help="Print ONLY the PATH line (for automation)",
)
def env_cmd(venv, shell, install_snippet, path_only):
    """Generate shell integration snippets for repo-lint.

    \b
    WHAT THIS DOES:
    Generates shell snippets to add repo-lint's virtual environment to your PATH.
    By design, this command DOES NOT automatically edit your shell rc files.
    You must manually add the snippet to persist across shell sessions.

    \b
    USE CASES:
    - Get instructions to make repo-lint available in your shell
    - Generate shell-specific activation snippets
    - Save snippets to config directory for easy sourcing
    - Automate PATH setup in scripts (use --path-only)

    \b
    EXAMPLES:
      # Show instructions for current shell
      $ repo-lint env

      # Generate PowerShell snippet
      $ repo-lint env --shell powershell

      # Save snippet to config directory
      $ repo-lint env --install --shell bash

      # Get just the PATH line for scripting
      $ repo-lint env --path-only

    \b
    OUTPUT MODES:
      default (no flags): Shows instructions + shell snippet
      --install: Writes snippet file + shows manual rc line to add
      --path-only: Prints ONLY PATH export line (automation-friendly)

    \b
    SNIPPET LOCATIONS:
      Linux/macOS: ~/.config/repo-lint/shell/
      Windows: %APPDATA%\\repo-lint\\shell\\

    \b
    MANUAL RC EDITING:
      After --install, you must manually add to your rc file:
        Bash: Add to ~/.bashrc
        Zsh: Add to ~/.zshrc
        Fish: Add to ~/.config/fish/config.fish
        PowerShell: Add to $PROFILE

    :param venv: Explicit venv path (optional)
    :param shell: Shell type (auto-detected if not provided)
    :param install_snippet: Write snippet to config dir
    :param path_only: Print only PATH line
    :returns: Exit code 0 on success, 1 on error
    """
    import os
    import platform
    import shlex

    from tools.repo_lint.env.venv_resolver import (
        VenvNotFoundError,
        get_venv_bin_dir,
        resolve_venv,
    )
    from tools.repo_lint.runners.base import find_repo_root

    try:
        # Resolve venv
        repo_root = find_repo_root()
        try:
            venv_path = resolve_venv(explicit_path=str(venv) if venv else None, repo_root=repo_root)
        except VenvNotFoundError as e:
            print(f"❌ {e.message}", file=sys.stderr)
            print(f"\n{e.remediation}", file=sys.stderr)
            sys.exit(1)

        bin_dir = get_venv_bin_dir(venv_path)

        # Auto-detect shell if not specified
        if not shell:
            detected = os.environ.get("SHELL", "")
            if platform.system() == "Windows":
                if os.environ.get("PSModulePath"):
                    shell = "powershell"
                else:
                    shell = "bash"  # Default to bash for Git Bash
            else:
                shell_name = Path(detected).name if detected else "bash"
                if shell_name in ("bash", "zsh", "fish"):
                    shell = shell_name
                else:
                    shell = "bash"  # Default

        shell = shell.lower()

        # Generate snippets with proper path quoting
        if shell in ("bash", "zsh"):
            # Quote the bin_dir path for shell safety
            quoted_bin_dir = shlex.quote(str(bin_dir))
            path_line = f"export PATH={quoted_bin_dir}:$PATH"
            snippet = f"# repo-lint environment setup\n{path_line}\n"
            rc_file = "~/.bashrc" if shell == "bash" else "~/.zshrc"
        elif shell == "fish":
            # Fish uses different quoting
            quoted_bin_dir = shlex.quote(str(bin_dir))
            path_line = f"set -gx PATH {quoted_bin_dir} $PATH"
            snippet = f"# repo-lint environment setup\n{path_line}\n"
            rc_file = "~/.config/fish/config.fish"
        elif shell == "powershell":
            # PowerShell uses double quotes for paths with spaces
            # Escape any double quotes in the path
            escaped_bin_dir = str(bin_dir).replace('"', '""')
            path_line = f'$env:PATH = "{escaped_bin_dir};$env:PATH"'
            snippet = f"# repo-lint environment setup\n{path_line}\n"
            rc_file = "$PROFILE"
        else:
            print(f"❌ Unsupported shell: {shell}", file=sys.stderr)
            sys.exit(1)

        # Handle output modes
        if path_only:
            # Automation mode: just the PATH line
            print(path_line)
            sys.exit(0)

        if install_snippet:
            # Write snippet to config directory
            if platform.system() == "Windows":
                appdata = os.environ.get("APPDATA")
                if not appdata:
                    print(
                        "❌ Cannot determine configuration directory: APPDATA is not set.",
                        file=sys.stderr,
                    )
                    sys.exit(1)
                config_dir = Path(appdata) / "repo-lint" / "shell"
            else:
                config_dir = Path.home() / ".config" / "repo-lint" / "shell"

            config_dir.mkdir(parents=True, exist_ok=True)
            snippet_file = config_dir / f"repo-lint.{shell}"
            snippet_file.write_text(snippet)

            print(f"✅ Snippet saved to: {snippet_file}")
            print(f"\n📝 To enable repo-lint in your shell, add this line to {rc_file}:")
            if shell == "powershell":
                load_cmd = f". {snippet_file}"
            else:
                load_cmd = f"source {snippet_file}"
            print(f"\n    {load_cmd}\n")
            sys.exit(0)

        # Default mode: show instructions
        from rich.console import Console
        from rich.panel import Panel
        from rich.syntax import Syntax

        console = Console()

        console.print(f"\n[bold]Shell Integration for repo-lint ({shell})[/bold]\n")

        # Show snippet with syntax highlighting
        syntax = Syntax(snippet, shell, theme="monokai", line_numbers=False)
        console.print(Panel(syntax, title="Shell Snippet", border_style="green"))

        # Show instructions
        console.print("\n[bold cyan]To enable repo-lint in your shell:[/bold cyan]")
        console.print(f"  1. Add the snippet above to {rc_file}")
        console.print("  2. Reload your shell or source the file\n")

        console.print("[bold cyan]Or use --install to save snippet:[/bold cyan]")
        console.print(f"  repo-lint env --install --shell {shell}\n")

        sys.exit(0)

    except Exception as e:
        print(f"❌ Error generating environment snippet: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


# Activate command
@cli.command("activate")
@click.option(
    "--venv",
    type=click.Path(exists=False, file_okay=False, dir_okay=True, path_type=Path),
    help="Explicit virtual environment path",
)
@click.option(
    "--shell",
    type=click.Choice(["bash", "zsh", "fish", "powershell", "cmd"], case_sensitive=False),
    help="Shell to launch (auto-detected if not specified)",
)
@click.option(
    "--command",
    type=str,
    help="Run single command in venv (no interactive shell)",
)
@click.option(
    "--no-rc",
    is_flag=True,
    help="Start shell without loading user rc files",
)
@click.option(
    "--print",
    "print_only",
    is_flag=True,
    help="Print exact command without executing",
)
@click.option(
    "--ci",
    is_flag=True,
    help="CI mode: disallow interactive shell, require --command",
)
# pylint: disable=too-many-arguments,too-many-positional-arguments
def activate_cmd(venv, shell, command, no_rc, print_only, ci):
    """Launch subshell with repo-lint virtual environment activated.

    \b
    WHAT THIS DOES:
    Spawns a new shell with the repo-lint virtual environment activated.
    This is a convenience wrapper that avoids manual activation steps.

    \b
    USE CASES:
    - Quickly activate venv without manual source command
    - Run single command in venv context (use --command)
    - Test venv activation in different shells
    - CI/CD automation (use --ci --command)

    \b
    EXAMPLES:
      # Launch interactive bash with venv activated
      $ repo-lint activate

      # Run single command in venv
      $ repo-lint activate --command "repo-lint check --ci"

      # Launch PowerShell with venv activated
      $ repo-lint activate --shell powershell

      # CI mode: run command without interactive shell
      $ repo-lint activate --ci --command "pytest"

      # Print command without executing
      $ repo-lint activate --print

    \b
    BEHAVIOR:
      - Interactive mode (default): Launches subshell with venv activated
      - Command mode (--command): Runs single command, exits when done
      - CI mode (--ci): Requires --command, blocks interactive shells
      - Print mode (--print): Shows command without executing

    \b
    SHELL ACTIVATION:
      Bash/Zsh: Sources activate script
      Fish: Sources activate.fish
      PowerShell: Sources Activate.ps1
      CMD: Calls activate.bat

    :param venv: Explicit venv path (optional)
    :param shell: Shell type (auto-detected if not provided)
    :param command: Single command to run (non-interactive)
    :param no_rc: Don't load user rc files
    :param print_only: Print command without executing
    :param ci: CI mode (requires --command)
    :returns: Exit code from subshell or command
    """
    import os
    import platform
    import shlex
    import subprocess

    from tools.repo_lint.env.venv_resolver import (
        VenvNotFoundError,
        get_activation_script,
        get_venv_bin_dir,
        resolve_venv,
    )
    from tools.repo_lint.runners.base import find_repo_root

    try:
        # CI mode validation
        if ci and not command:
            print("❌ CI mode requires --command flag", file=sys.stderr)
            print("   Interactive shells are not allowed in CI mode", file=sys.stderr)
            sys.exit(1)

        # Resolve venv
        repo_root = find_repo_root()
        try:
            venv_path = resolve_venv(explicit_path=str(venv) if venv else None, repo_root=repo_root)
        except VenvNotFoundError as e:
            print(f"❌ {e.message}", file=sys.stderr)
            print(f"\n{e.remediation}", file=sys.stderr)
            sys.exit(1)

        bin_dir = get_venv_bin_dir(venv_path)

        # Auto-detect shell if not specified
        if not shell:
            detected = os.environ.get("SHELL", "")
            if platform.system() == "Windows":
                if os.environ.get("PSModulePath"):
                    shell = "powershell"
                else:
                    shell = "cmd"
            else:
                shell_name = Path(detected).name if detected else "bash"
                if shell_name in ("bash", "zsh", "fish"):
                    shell = shell_name
                else:
                    shell = "bash"  # Default

        shell = shell.lower()

        # Validate shell is in allowed set to prevent injection via exec command
        allowed_shells = {"bash", "zsh", "fish", "powershell", "cmd"}
        if shell not in allowed_shells:
            print(f"❌ Unsupported shell: {shell}", file=sys.stderr)
            print(f"   Supported shells: {', '.join(sorted(allowed_shells))}", file=sys.stderr)
            sys.exit(1)

        # Build shell command
        activation_script = get_activation_script(venv_path, shell=shell)

        # Helper function for Fish shell quoting
        def _fish_shell_quote(text: str) -> str:
            """Minimal Fish-safe quoting using single quotes and split-quote pattern.
            
            :param text: The text to quote for Fish shell
            :returns: Quoted string safe for Fish shell
            """
            if text == "":
                return "''"
            return "'" + text.replace("'", "'\\''") + "'"

        if shell in ("bash", "zsh"):
            # Use shlex.quote() to prevent injection via activation_script path
            quoted_script = shlex.quote(str(activation_script))
            if command:
                # Run single command:
                # - keep the -c script constant (only sourcing the activation script and exec'ing "$@")
                # - pass the user-provided command as separate arguments to avoid shell injection
                command_args = shlex.split(command)
                shell_cmd = [
                    shell,
                    "-c",
                    f'source {quoted_script} && exec "$@"',
                    "repo-lint-activate",
                    *command_args,
                ]
            else:
                # Interactive shell: source activation script, then exec a new interactive shell
                if no_rc:
                    shell_cmd = [
                        shell,
                        "--noprofile",
                        "--norc",
                        "-i",
                        "-c",
                        f"source {quoted_script}; exec {shell} --noprofile --norc -i",
                    ]
                else:
                    shell_cmd = [
                        shell,
                        "-i",
                        "-c",
                        f"source {quoted_script}; exec {shell} -i",
                    ]

        elif shell == "fish":
            if command:
                # Use _fish_shell_quote() to prevent command injection for Fish shell
                shell_cmd = [
                    "fish",
                    "-c",
                    f"source {_fish_shell_quote(str(activation_script))}; eval {_fish_shell_quote(command)}",
                ]
            else:
                # Interactive fish shell: ensure activation script is sourced
                # so that VIRTUAL_ENV, PATH, and prompt customizations are
                # applied consistently with non-interactive usage.
                # Use _fish_shell_quote() to prevent injection via activation_script path
                quoted_script = _fish_shell_quote(str(activation_script))
                if no_rc:
                    shell_cmd = [
                        "fish",
                        "--no-config",
                        "-C",
                        f"source {quoted_script}",
                    ]
                else:
                    shell_cmd = [
                        "fish",
                        "-C",
                        f"source {quoted_script}",
                    ]

        elif shell == "powershell":
            ps_exe = "pwsh" if platform.system() != "Windows" else "powershell"
            if command:
                shell_cmd = [ps_exe]
                if no_rc:
                    shell_cmd.append("-NoProfile")
                # PowerShell command construction:
                # - The activation script path is quoted to handle spaces/special chars
                # - The user command is escaped to prevent injection via PowerShell metacharacters
                escaped_command = _escape_powershell_command(command)
                shell_cmd.extend(
                    [
                        "-Command",
                        f'. "{activation_script}"; {escaped_command}',
                    ]
                )
            else:
                shell_cmd = [ps_exe]
                if no_rc:
                    shell_cmd.append("-NoProfile")
                # Start an interactive shell that first activates the venv
                shell_cmd.extend(
                    [
                        "-NoExit",
                        "-Command",
                        f'. "{activation_script}"',
                    ]
                )

        elif shell == "cmd":
            if platform.system() != "Windows":
                print("❌ CMD shell is only supported on Windows", file=sys.stderr)
                sys.exit(1)

            if command:
                # CMD uses different quoting - the activation script path is already quoted.
                # Escape the user-supplied command to avoid injection via CMD metacharacters.
                escaped_command = _escape_cmd_argument(command)
                shell_cmd = [
                    "cmd",
                    "/C",
                    f'"{activation_script}" && {escaped_command}',
                ]
            else:
                shell_cmd = ["cmd", "/K", str(activation_script)]

        else:
            print(f"❌ Unsupported shell: {shell}", file=sys.stderr)
            sys.exit(1)

        # Print mode: show command without executing
        if print_only:
            print(" ".join(str(part) for part in shell_cmd))
            sys.exit(0)

        # Prepare environment with venv in PATH
        env = os.environ.copy()
        env["PATH"] = f"{bin_dir}{os.pathsep}{env.get('PATH', '')}"
        env["VIRTUAL_ENV"] = str(venv_path)

        # Execute command
        if command:
            # Run command and return its exit code
            result = subprocess.run(shell_cmd, env=env, check=False)
            sys.exit(result.returncode)
        else:
            # Launch interactive shell
            print(f"🚀 Launching {shell} with venv activated...")
            print(f"   Virtual environment: {venv_path}")
            print("   Type 'exit' to return to parent shell\n")
            result = subprocess.run(shell_cmd, env=env, check=False)
            sys.exit(result.returncode)

    except Exception as e:
        print(f"❌ Error activating virtual environment: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
