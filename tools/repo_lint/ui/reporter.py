"""Reporter for all user-facing console output in repo_lint.

:Purpose:
    Provides all rendering methods for repo_lint output using Rich formatting.
    Routes all user-facing output through a single, consistent interface.

:Classes:
    - Reporter: Main reporting interface

:Environment Variables:
    None

:Exit Codes:
    This module does not define or use exit codes (UI rendering only):
    - 0: Not applicable (see tools.repo_lint.common.ExitCode)
    - 1: Not applicable (see tools.repo_lint.common.ExitCode)

:Examples:
    Create reporter and render header::

        from tools.repo_lint.ui.reporter import Reporter
        reporter = Reporter(ci_mode=False)
        reporter.render_header({"repo_root": "/path/to/repo", "mode": "check"})

    Render results table::

        reporter.render_results_table(results)
"""

import sys
from typing import Any, Dict, List, Optional

from rich.panel import Panel
from rich.table import Table

from tools.repo_lint.common import ExitCode, LintResult
from tools.repo_lint.ui.console import get_console
from tools.repo_lint.ui.theme import UITheme, get_box_style, get_theme

# Maximum number of violations to display per tool (to avoid overwhelming output)
MAX_VIOLATIONS_PER_TOOL = 50


class Reporter:
    """Reporter for all user-facing output in repo_lint.

    All user-facing console output must go through this reporter to ensure
    consistent formatting across TTY and CI modes.
    """

    def __init__(self, ci_mode: bool = False, theme: Optional[UITheme] = None):
        """Initialize Reporter.

        :param ci_mode: If True, use CI-friendly output (no colors, no spinners)
        :param theme: Optional theme override (default: load from config)
        """
        self.ci_mode = ci_mode
        self.console = get_console(ci_mode=ci_mode)
        self.theme = theme or get_theme(ci_mode=ci_mode)

        # Create a dedicated stderr console for error messages
        # This console is configured separately to write to stderr
        from rich.console import Console

        self.stderr_console = Console(
            file=sys.stderr,
            force_terminal=self.console.is_terminal,
            no_color=ci_mode,
            highlight=not ci_mode,
            markup=True,
            emoji=not ci_mode,
        )

    def _get_icon(self, status: str) -> str:
        """Get icon for status.

        :param status: Status string (pass, fail, warn, skip, running)
        :returns: Icon string
        """
        if self.ci_mode and not self.theme.ci.icons_enabled:
            return ""

        icons = self.theme.interactive.icons
        icon_map = {
            "pass": icons.pass_icon,
            "fail": icons.fail,
            "warn": icons.warn,
            "skip": icons.skip,
            "running": icons.running,
        }
        return icon_map.get(status.lower(), "")

    def _get_color(self, color_type: str) -> str:
        """Get color for type.

        :param color_type: Color type (primary, success, failure, warning, info, metadata)
        :returns: Color string
        """
        if self.ci_mode:
            return ""  # No colors in CI mode

        colors = self.theme.interactive.colors
        color_map = {
            "primary": colors.primary,
            "success": colors.success,
            "failure": colors.failure,
            "warning": colors.warning,
            "info": colors.info,
            "metadata": colors.metadata,
        }
        return color_map.get(color_type, "")

    def _format_with_color(self, text: str, color_type: str, bold: bool = False) -> str:
        """Format text with color and optional bold.

        :param text: Text to format
        :param color_type: Color type
        :param bold: If True, make text bold
        :returns: Formatted text (with Rich markup if not CI mode)
        """
        if self.ci_mode:
            return text

        color = self._get_color(color_type)
        if bold:
            return f"[bold {color}]{text}[/bold {color}]"
        return f"[{color}]{text}[/{color}]"

    def render_header(self, context: Dict[str, Any]) -> None:
        """Render command header panel.

        :param context: Context dictionary with keys:
            - command: Command name (check/fix/install)
            - repo_root: Repository root path
            - config_files: List of loaded config files
            - mode: Output mode (TTY/CI)
            - filters: Optional filters applied (--only, etc.)
        """
        # Build header content
        lines = []
        lines.append(f"Command: {self._format_with_color(context.get('command', 'unknown'), 'primary', bold=True)}")
        lines.append(f"Repo Root: {self._format_with_color(str(context.get('repo_root', 'unknown')), 'metadata')}")

        # Config files
        config_files = context.get("config_files", [])
        if config_files:
            lines.append(f"Config Files: {self._format_with_color(', '.join(config_files), 'metadata')}")

        # Mode
        mode = "CI" if self.ci_mode else "Interactive (TTY)"
        lines.append(f"Output Mode: {self._format_with_color(mode, 'info')}")

        # Filters
        filters = context.get("filters")
        if filters:
            lines.append(f"Filters: {self._format_with_color(filters, 'warning')}")

        content = "\n".join(lines)

        # Create panel
        box_style = get_box_style(self.theme, self.ci_mode)
        title = (
            self._format_with_color("Repository Linter", "primary", bold=True)
            if not self.ci_mode
            else "Repository Linter"
        )
        border_style = self._get_color("primary") if not self.ci_mode else "white"

        panel = Panel(content, title=title, border_style=border_style, box=box_style)

        self.console.print(panel)
        self.console.print()

    def runner_started(self, name: str) -> None:
        """Report that a runner has started.

        :param name: Runner name
        """
        icon = self._get_icon("running")
        msg = f"{icon} {name}" if icon else f"Running: {name}"
        self.console.print(self._format_with_color(msg, "info"))

    def _runner_completed(self, result: LintResult) -> None:
        """Private placeholder hook for future live progress display updates.

        This is currently unused but reserved for future implementation of live
        progress displays. Made private since it's not part of the public API yet.

        :param result: LintResult from runner

        :Future:
            This could update a live Rich Progress display or spinner to show
            per-runner status as checks complete, rather than waiting until all
            runners finish.
        """
        # TODO: Implement live progress display updates  # pylint: disable=fixme
        # For now, results are batched and shown in render_results_table()
        _ = result  # Explicit unused parameter to signal this is intentional

    def render_results_table(self, results: List[LintResult]) -> None:
        """Render results summary table.

        :param results: List of LintResult objects
        """
        box_style = get_box_style(self.theme, self.ci_mode)

        # Create table
        table = Table(title="Linting Results", show_header=True, box=box_style)

        # Add columns
        table.add_column("Runner", style=self._get_color("primary") if not self.ci_mode else None, no_wrap=True)
        table.add_column("Status", no_wrap=True)
        table.add_column("Files", justify="right")
        table.add_column("Violations", justify="right")
        table.add_column("Duration", justify="right")

        # Add rows
        for result in results:
            # Status column
            if result.passed:
                icon = self._get_icon("pass")
                status = f"{icon} PASS" if icon else "PASS"
                status_formatted = self._format_with_color(status, "success")
            elif result.error:
                icon = self._get_icon("fail")
                status = f"{icon} ERROR" if icon else "ERROR"
                status_formatted = self._format_with_color(status, "failure")
            else:
                icon = self._get_icon("fail")
                status = f"{icon} FAIL" if icon else "FAIL"
                status_formatted = self._format_with_color(status, "failure")

            # Files column
            files_str = str(result.file_count) if result.file_count is not None else "-"

            # Violations column
            violations_str = str(len(result.violations))

            # Duration column
            if result.duration is not None:
                duration_str = f"{result.duration:.2f}s"
            else:
                duration_str = "-"

            table.add_row(result.tool, status_formatted, files_str, violations_str, duration_str)

        self.console.print(table)
        self.console.print()

    def render_failures(self, results: List[LintResult]) -> None:
        """Render detailed failure information.

        :param results: List of LintResult objects (only failed ones will be shown)
        """
        failed_results = [r for r in results if not r.passed]

        if not failed_results:
            return

        for result in failed_results:
            # Create failure panel header
            box_style = get_box_style(self.theme, self.ci_mode)
            title = f"{result.tool} Failures"
            title_formatted = self._format_with_color(title, "failure", bold=True) if not self.ci_mode else title
            border_style = self._get_color("failure") if not self.ci_mode else "white"

            # Render panel header
            if result.error:
                # For errors, show in a panel
                content = self._format_with_color(result.error, "failure")
                panel = Panel(content, title=title_formatted, border_style=border_style, box=box_style)
                self.console.print(panel)
            else:
                # For violations, show a panel with header and then a table
                panel_content = f"Found {len(result.violations)} violation(s)"
                panel = Panel(panel_content, title=title_formatted, border_style=border_style, box=box_style)
                self.console.print(panel)

                # Create violations table
                violations_table = Table(show_header=True, box=box_style, show_lines=False)
                violations_table.add_column("File", style=self._get_color("metadata") if not self.ci_mode else None)
                violations_table.add_column("Line", justify="right")
                violations_table.add_column("Message")

                # Add violations (limit to avoid overwhelming output)
                for violation in result.violations[:MAX_VIOLATIONS_PER_TOOL]:
                    line_str = str(violation.line) if violation.line else "-"
                    violations_table.add_row(violation.file, line_str, violation.message)

                if len(result.violations) > MAX_VIOLATIONS_PER_TOOL:
                    remaining = len(result.violations) - MAX_VIOLATIONS_PER_TOOL
                    note = self._format_with_color(f"... and {remaining} more violations", "warning")
                    violations_table.add_row("", "", note)

                # Render the table
                self.console.print(violations_table)

            self.console.print()

    def render_final_summary(self, results: List[LintResult], exit_code: ExitCode) -> None:
        """Render final summary panel.

        :param results: List of LintResult objects
        :param exit_code: Exit code for the run
        """
        # Count results
        passed = sum(1 for r in results if r.passed)
        failed = sum(1 for r in results if not r.passed and not r.error)
        errors = sum(1 for r in results if r.error)
        total_violations = sum(len(r.violations) for r in results)

        # Build summary
        lines = []
        lines.append(f"Total Runners: {len(results)}")
        lines.append(f"  {self._format_with_color('Passed', 'success')}: {passed}")
        lines.append(f"  {self._format_with_color('Failed', 'failure')}: {failed}")
        if errors > 0:
            lines.append(f"  {self._format_with_color('Errors', 'failure')}: {errors}")
        if total_violations > 0:
            lines.append(f"Total Violations: {self._format_with_color(str(total_violations), 'failure', bold=True)}")

        # Exit code meaning
        lines.append(f"\nExit Code: {self._format_with_color(str(exit_code), 'metadata')} ({exit_code.name})")

        content = "\n".join(lines)

        # Determine overall status
        if exit_code == ExitCode.SUCCESS:
            title = "Summary"
            title_formatted = self._format_with_color(title, "success", bold=True) if not self.ci_mode else title
            border_style = self._get_color("success") if not self.ci_mode else "white"
        else:
            title = "Summary"
            title_formatted = self._format_with_color(title, "failure", bold=True) if not self.ci_mode else title
            border_style = self._get_color("failure") if not self.ci_mode else "white"

        box_style = get_box_style(self.theme, self.ci_mode)
        panel = Panel(content, title=title_formatted, border_style=border_style, box=box_style)

        self.console.print(panel)

    def render_config_validation_errors(self, errors: List[str]) -> None:
        """Render configuration validation errors.

        :param errors: List of error messages
        """
        box_style = get_box_style(self.theme, self.ci_mode)
        title = "Configuration Validation Errors"
        title_formatted = self._format_with_color(title, "failure", bold=True) if not self.ci_mode else title
        border_style = self._get_color("failure") if not self.ci_mode else "white"

        # Build content
        lines = []
        for error in errors:
            icon = self._get_icon("fail")
            if icon:
                lines.append(f"{icon} {error}")
            else:
                lines.append(f"• {error}")

        content = "\n".join(lines)

        panel = Panel(content, title=title_formatted, border_style=border_style, box=box_style)
        self.console.print(panel)
        self.console.print()

    def error(self, message: str) -> None:
        """Print an error message.

        :param message: Error message
        """
        icon = self._get_icon("fail")
        if icon:
            formatted = f"{icon} {self._format_with_color(message, 'failure', bold=True)}"
        else:
            formatted = self._format_with_color(f"ERROR: {message}", "failure", bold=True)

        # Print to stderr using the pre-configured stderr console to properly render Rich markup
        self.stderr_console.print(formatted)

    def warning(self, message: str) -> None:
        """Print a warning message.

        :param message: Warning message
        """
        icon = self._get_icon("warn")
        if icon:
            formatted = f"{icon} {self._format_with_color(message, 'warning')}"
        else:
            formatted = self._format_with_color(f"WARNING: {message}", "warning")

        self.console.print(formatted)

    def info(self, message: str) -> None:
        """Print an info message.

        :param message: Info message
        """
        formatted = self._format_with_color(message, "info")
        self.console.print(formatted)

    def success(self, message: str) -> None:
        """Print a success message.

        :param message: Success message
        """
        icon = self._get_icon("pass")
        if icon:
            formatted = f"{icon} {self._format_with_color(message, 'success', bold=True)}"
        else:
            formatted = self._format_with_color(message, "success", bold=True)

        self.console.print(formatted)

    def print(self, message: str) -> None:
        """Print a plain message.

        :param message: Message to print
        """
        self.console.print(message)
