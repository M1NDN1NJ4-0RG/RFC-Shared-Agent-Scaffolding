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
    - which: Show repo-lint environment and PATH information
    - env: Generate shell integration snippet for repo-lint
    - activate: Launch subshell with repo-lint venv activated

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

# pylint: disable=too-many-lines

from __future__ import annotations

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

    See HOW-TO-USE-THIS-TOOL.md for detailed usage and examples.

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

    See HOW-TO-USE-THIS-TOOL.md for detailed usage, forensic reports, and examples.

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

    See HOW-TO-USE-THIS-TOOL.md for detailed troubleshooting guide.

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


# Environment & PATH Management Commands (Phase 2.8)


@cli.command("which")
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output in JSON format for machine parsing",
)
def which(output_json):
    """Show repo-lint environment and PATH information.

    \b
    WHAT THIS DOES:
    Diagnostic helper that displays detailed information about your repo-lint
    installation, Python environment, and virtual environment configuration.
    Useful for debugging PATH issues and venv confusion.

    \b
    INFORMATION DISPLAYED:
    - Repository root directory
    - Resolved virtual environment path
    - Virtual environment bin/Scripts directory
    - Virtual environment activation script path
    - Resolved repo-lint executable path
    - Python executable path
    - Python sys.prefix and sys.base_prefix
    - Detected shell type
    - Whether currently in a venv

    \b
    OUTPUT FORMATS:
    - Default: Human-readable table with colored output
    - JSON (--json): Machine-readable JSON for automation

    \b
    EXAMPLES:
      # Show environment information
      $ repo-lint which

      # Get JSON output for scripting
      $ repo-lint which --json | jq '.venv_path'

      # Debug PATH issues
      $ repo-lint which  # Check if repo-lint is from expected venv

    \b
    USE CASES:
    - Debugging "repo-lint not found" errors
    - Verifying venv activation
    - Checking if running correct repo-lint installation
    - Generating environment report for bug reports

    :param output_json: Output in JSON format instead of human-readable table
    :returns: Exit code 0
    """
    from tools.repo_lint.env_utils import (
        detect_shell,
        get_venv_activate_script,
        get_venv_bin_dir,
        is_in_venv,
        resolve_venv,
    )
    from tools.repo_lint.repo_utils import find_repo_root

    try:
        # Gather environment information
        repo_root = find_repo_root()
        shell = detect_shell()
        in_venv = is_in_venv()

        # Try to resolve venv (may fail if no venv exists)
        venv_error = None  # Initialize venv_error
        try:
            venv_path = resolve_venv()
            bin_dir = get_venv_bin_dir(venv_path)
            activate_script = get_venv_activate_script(venv_path)
        except RuntimeError as e:
            venv_path = None
            bin_dir = None
            activate_script = None
            venv_error = str(e)

        # Get repo-lint executable path
        import shutil

        repo_lint_exe = shutil.which("repo-lint")

        # Collect all information
        info = {
            "repo_root": str(repo_root),
            "venv_path": str(venv_path) if venv_path else None,
            "venv_error": venv_error if venv_path is None else None,
            "venv_bin_dir": str(bin_dir) if bin_dir else None,
            "venv_activate_script": str(activate_script) if activate_script else None,
            "repo_lint_executable": repo_lint_exe,
            "python_executable": sys.executable,
            "python_prefix": sys.prefix,
            "python_base_prefix": sys.base_prefix,
            "in_venv": in_venv,
            "detected_shell": shell,
        }

        if output_json:
            # JSON output
            print(json.dumps(info, indent=2))
        else:
            # Human-readable table
            print("\n📋 repo-lint Environment Information\n")
            print(f"  Repository root:          {info['repo_root']}")
            print(f"  Detected shell:           {info['detected_shell']}")
            print(f"  Currently in venv:        {'✅ Yes' if info['in_venv'] else '❌ No'}")
            print()

            if info["venv_path"]:
                print(f"  Virtual environment:      {info['venv_path']}")
                print(f"  Venv bin directory:       {info['venv_bin_dir']}")
                print(f"  Venv activation script:   {info['venv_activate_script']}")
            else:
                print("  Virtual environment:      ❌ Not found")
                print(f"  Error: {info['venv_error']}")

            print()
            print(f"  repo-lint executable:     {info['repo_lint_executable'] or '❌ Not in PATH'}")
            print(f"  Python executable:        {info['python_executable']}")
            print(f"  Python sys.prefix:        {info['python_prefix']}")
            print(f"  Python sys.base_prefix:   {info['python_base_prefix']}")
            print()

            # Warning if repo-lint not from expected venv
            if info["venv_path"] and info["repo_lint_executable"]:
                expected_in_venv = str(info["venv_bin_dir"]) in info["repo_lint_executable"]
                if not expected_in_venv:
                    print("  ⚠️  WARNING: repo-lint executable is not from the detected venv!")
                    print(f"     Expected in: {info['venv_bin_dir']}")
                    print(f"     Actually at: {info['repo_lint_executable']}")
                    print()

        sys.exit(0)

    except Exception as e:
        print(f"❌ Error gathering environment information: {e}", file=sys.stderr)
        if _is_verbose_enabled():
            import traceback

            traceback.print_exc()
        sys.exit(1)


@cli.command("env")
@click.option(
    "--print",
    "print_snippet",
    is_flag=True,
    default=True,
    help="Print instructions and shell snippet (default)",
)
@click.option(
    "--install",
    "install_snippet",
    is_flag=True,
    help="Write snippet to user config directory",
)
@click.option(
    "--shell",
    type=click.Choice(["bash", "zsh", "fish", "powershell"], case_sensitive=False),
    help="Shell type (auto-detected if not specified)",
)
@click.option(
    "--venv",
    "venv_path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Explicit venv path (default: auto-detect)",
)
@click.option(
    "--path-only",
    is_flag=True,
    help="Print ONLY the PATH line (for automation)",
)
def env(print_snippet, install_snippet, shell, venv_path, path_only):
    """Generate shell integration snippet for repo-lint.

    \b
    WHAT THIS DOES:
    Generates shell-specific PATH snippets to make repo-lint available in your
    shell. Does NOT automatically edit rc files - you must manually add the
    snippet to your shell configuration.

    \b
    MODES:
    --print (default): Print instructions and shell snippet
    --install: Write snippet to ~/.config/repo-lint/shell/ (manual rc edit still required)
    --path-only: Print ONLY the PATH export line (for automation)

    \b
    SHELL DETECTION:
    Automatically detects your shell from environment variables. Override with --shell
    if detection is incorrect. Supported shells: bash, zsh, fish, powershell

    \b
    EXAMPLES:
      # Generate snippet for current shell (auto-detected)
      $ repo-lint env

      # Generate snippet for specific shell
      $ repo-lint env --shell bash

      # Write snippet to config directory
      $ repo-lint env --install

      # Get just the PATH line for automation
      $ repo-lint env --path-only

      # Use with explicit venv
      $ repo-lint env --venv /path/to/venv

    \b
    MANUAL INSTALLATION:
    After running --install, you must add this line to your shell rc file:
      - Bash: source ~/.config/repo-lint/shell/repo-lint.bash
      - Zsh: source ~/.config/repo-lint/shell/repo-lint.zsh
      - Fish: source ~/.config/repo-lint/shell/repo-lint.fish
      - PowerShell: . ~/.config/repo-lint/shell/repo-lint.ps1

    \b
    WHY NO AUTO-EDIT?
    This tool does NOT automatically edit rc files to avoid:
    - Accidentally breaking shell configuration
    - Creating duplicate entries
    - Modifying files without explicit user consent

    :param print_snippet: Print instructions and snippet (default: True)
    :param install_snippet: Write snippet to user config directory
    :param shell: Shell type (auto-detected if None)
    :param venv_path: Explicit venv path (auto-detected if None)
    :param path_only: Print ONLY the PATH line
    :returns: Exit code 0 on success, 1 on error
    """
    from tools.repo_lint.env_utils import (
        detect_shell,
        generate_shell_snippet,
        get_user_config_dir,
        resolve_venv,
    )

    try:
        # Detect or use provided shell
        if shell is None:
            shell = detect_shell()
            if shell == "unknown":
                print("❌ Could not detect shell type. Use --shell to specify.", file=sys.stderr)
                sys.exit(1)

        # Resolve venv
        try:
            venv = resolve_venv(explicit_venv=venv_path)
        except RuntimeError as e:
            print(f"❌ {e}", file=sys.stderr)
            sys.exit(1)

        # Generate snippet
        snippet_content, file_ext = generate_shell_snippet(venv, shell)

        # Path-only mode (for automation)
        if path_only:
            # Extract just the PATH line (first non-comment line)
            for line in snippet_content.split("\n"):
                if line and not line.strip().startswith("#") and not line.strip().startswith("REM"):
                    print(line)
                    break
            sys.exit(0)

        # Install mode
        if install_snippet:
            config_dir = get_user_config_dir()
            shell_dir = config_dir / "shell"
            shell_dir.mkdir(exist_ok=True)

            snippet_file = shell_dir / f"repo-lint{file_ext}"
            snippet_file.write_text(snippet_content, encoding="utf-8")

            print(f"✅ Snippet written to: {snippet_file}\n")
            print("To activate, add this line to your shell rc file:")
            print()

            if shell == "bash":
                print(f'  echo "source {snippet_file}" >> ~/.bashrc')
            elif shell == "zsh":
                print(f'  echo "source {snippet_file}" >> ~/.zshrc')
            elif shell == "fish":
                print(f'  echo "source {snippet_file}" >> ~/.config/fish/config.fish')
            elif shell == "powershell":
                print(f"  Add-Content $PROFILE '. {snippet_file}'")

            print()
            print("Then reload your shell or run:")
            if shell in ["bash", "zsh"]:
                print(f"  source {snippet_file}")
            elif shell == "fish":
                print(f"  source {snippet_file}")
            elif shell == "powershell":
                print(f"  . {snippet_file}")

        else:
            # Print mode (default)
            print(f"\n📝 Shell Integration Snippet for {shell}\n")
            print("Add the following to your shell configuration file:\n")
            print(snippet_content)
            print("\nConfiguration files:")
            if shell == "bash":
                print("  - ~/.bashrc (Linux)")
                print("  - ~/.bash_profile (macOS)")
            elif shell == "zsh":
                print("  - ~/.zshrc")
            elif shell == "fish":
                print("  - ~/.config/fish/config.fish")
            elif shell == "powershell":
                print("  - $PROFILE (run `$PROFILE` in PowerShell to see path)")

            print("\nAfter adding, reload your shell:")
            if shell in ["bash", "zsh"]:
                print("  source ~/.[shell]rc")
            elif shell == "fish":
                print("  source ~/.config/fish/config.fish")
            elif shell == "powershell":
                print("  . $PROFILE")

        sys.exit(0)

    except Exception as e:
        print(f"❌ Error generating shell snippet: {e}", file=sys.stderr)
        if _is_verbose_enabled():
            import traceback

            traceback.print_exc()
        sys.exit(1)


@cli.command("activate")
@click.option(
    "--venv",
    "venv_path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Explicit venv path (default: auto-detect)",
)
@click.option(
    "--shell",
    type=click.Choice(["bash", "zsh", "fish", "powershell", "cmd"], case_sensitive=False),
    help="Shell type to launch (auto-detected if not specified)",
)
@click.option(
    "--command",
    "-c",
    help="Run single command instead of interactive shell",
)
@click.option(
    "--no-rc",
    is_flag=True,
    help="Start shell without loading user rc files",
)
@click.option(
    "--print",
    "print_command",
    is_flag=True,
    help="Print the activation command instead of executing it",
)
@click.option(
    "--ci",
    "ci_mode",
    is_flag=True,
    help="CI mode: disallow interactive shell, require --command",
)
def activate(
    venv_path, shell, command, no_rc, print_command, ci_mode
):  # pylint: disable=too-many-arguments,too-many-positional-arguments
    """Launch subshell with repo-lint venv activated.

    \b
    WHAT THIS DOES:
    Spawns a new shell with the repo-lint virtual environment activated, making
    repo-lint and all Python tools available without manual activation.

    \b
    MODES:
    Interactive (default): Launches interactive subshell with venv active
    Command mode (--command): Runs single command with venv active, then exits
    Print mode (--print): Shows the underlying command without executing

    \b
    EXAMPLES:
      # Launch interactive shell with venv active
      $ repo-lint activate

      # Run a single command with venv active
      $ repo-lint activate --command "repo-lint check"

      # Use specific venv
      $ repo-lint activate --venv /path/to/venv

      # Launch specific shell type
      $ repo-lint activate --shell bash

      # Start shell without loading rc files
      $ repo-lint activate --no-rc

      # Show the activation command (for debugging)
      $ repo-lint activate --print

      # CI mode: requires --command, no interactive shell
      $ repo-lint activate --ci --command "repo-lint check --ci"

    \b
    INTERACTIVE SHELL:
    When launched interactively, you'll be in a new shell with:
    - repo-lint available on PATH
    - All Python tools available (black, ruff, pylint, etc.)
    - Same environment as "source .venv/bin/activate"
    - Type 'exit' to return to parent shell

    \b
    CI MODE:
    When --ci is specified:
    - Interactive shells are disallowed (prevents hanging CI jobs)
    - --command is required
    - Exits with command's exit code

    :param venv_path: Explicit venv path (auto-detected if None)
    :param shell: Shell type to launch (auto-detected if None)
    :param command: Single command to run (interactive shell if None)
    :param no_rc: Start shell without loading user rc files
    :param print_command: Print command instead of executing
    :param ci_mode: CI mode (disallow interactive, require --command)
    :returns: Exit code from subshell or command
    """
    import subprocess

    from tools.repo_lint.env_utils import detect_shell, get_venv_activate_script, resolve_venv

    try:
        # CI mode validation
        if ci_mode and not command:
            print(
                "❌ Error: --ci mode requires --command (interactive shells not allowed in CI)",
                file=sys.stderr,
            )
            sys.exit(1)

        # Detect or use provided shell
        if shell is None:
            shell = detect_shell()
            if shell == "unknown":
                print("❌ Could not detect shell type. Use --shell to specify.", file=sys.stderr)
                sys.exit(1)

        # Resolve venv
        try:
            venv = resolve_venv(explicit_venv=venv_path)
        except RuntimeError as e:
            print(f"❌ {e}", file=sys.stderr)
            sys.exit(1)

        activate_script = get_venv_activate_script(venv)

        # Build activation command
        if shell in ["bash", "zsh"]:
            if command:
                # Run single command
                cmd = [shell, "-c", f'source "{activate_script}" && {command}']
            else:
                # Interactive shell
                if no_rc:
                    cmd = [shell, "--noprofile", "--norc", "-c", f'source "{activate_script}"; exec {shell}']
                else:
                    cmd = [shell, "-c", f'source "{activate_script}"; exec {shell}']

        elif shell == "fish":
            if command:
                cmd = [shell, "-c", f'source "{activate_script}"; {command}']
            else:
                if no_rc:
                    cmd = [shell, "--no-config", "-c", f'source "{activate_script}"; exec {shell}']
                else:
                    cmd = [shell, "-c", f'source "{activate_script}"; exec {shell}']

        elif shell == "powershell":
            if command:
                cmd = ["pwsh", "-Command", f'. "{activate_script}"; {command}']
            else:
                if no_rc:
                    cmd = ["pwsh", "-NoProfile", "-Command", f'. "{activate_script}"; pwsh -NoExit']
                else:
                    cmd = ["pwsh", "-Command", f'. "{activate_script}"; pwsh -NoExit']

        elif shell == "cmd":
            # Windows CMD doesn't support source, use call
            if command:
                cmd = ["cmd", "/C", f'"{activate_script}" && {command}']
            else:
                # CMD interactive with activation
                cmd = ["cmd", "/K", f'"{activate_script}"']
        else:
            print(f"❌ Unsupported shell: {shell}", file=sys.stderr)
            sys.exit(1)

        # Print mode
        if print_command:
            print(" ".join(cmd))
            sys.exit(0)

        # Execute subshell
        result = subprocess.run(cmd, check=False)
        sys.exit(result.returncode)

    except Exception as e:
        print(f"❌ Error launching subshell: {e}", file=sys.stderr)
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


if __name__ == "__main__":
    main()
