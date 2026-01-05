"""UI module for repo_lint console output and reporting.

:Purpose:
    Provides Rich-based UI rendering for repo_lint with TTY and CI mode support.

:Modules:
    - console: Single console instance with TTY/CI mode handling
    - reporter: All user-facing output rendering methods
    - theme: UI theme configuration and validation

:Environment Variables:
    - REPO_LINT_UI_THEME: Path to custom UI theme YAML file

:Exit Codes:
    This module does not define or use exit codes (UI components only):
    - 0: Not applicable (see tools.repo_lint.common.ExitCode)
    - 1: Not applicable (see tools.repo_lint.common.ExitCode)

:Examples:
    Get the configured console::

        from tools.repo_lint.ui import get_console
        console = get_console(ci_mode=False)

    Use the reporter::

        from tools.repo_lint.ui import Reporter
        reporter = Reporter(ci_mode=False)
        reporter.render_header(context)
"""

from __future__ import annotations

from tools.repo_lint.ui.console import get_console
from tools.repo_lint.ui.reporter import Reporter

__all__ = ["get_console", "Reporter"]
