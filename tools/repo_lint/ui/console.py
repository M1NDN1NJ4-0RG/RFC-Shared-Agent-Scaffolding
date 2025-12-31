"""Single console instance management for repo_lint.

:Purpose:
    Provides a single, configured Rich Console instance per run with proper
    TTY detection and CI mode handling.

:Functions:
    - get_console: Get or create the configured Console instance
    - is_tty: Check if stdout is a TTY

:Environment Variables:
    None

:Exit Codes:
    This module does not define or use exit codes (console configuration only):
    - 0: Not applicable (see tools.repo_lint.common.ExitCode)
    - 1: Not applicable (see tools.repo_lint.common.ExitCode)

:Examples:
    Get console for interactive mode::

        from tools.repo_lint.ui.console import get_console
        console = get_console(ci_mode=False)
        console.print("[bold green]Success![/bold green]")

    Get console for CI mode::

        console = get_console(ci_mode=True)
        console.print("Success!")  # No colors in CI
"""

import sys
from typing import Dict, Optional, Tuple

from rich.console import Console


def is_tty() -> bool:
    """Check if stdout is a TTY.

    :returns: True if stdout is a TTY, False otherwise
    """
    return sys.stdout.isatty()


# Simple cache keyed by (ci_mode, force_terminal) to avoid redundant Console creation
_console_cache: Dict[Tuple[bool, Optional[bool]], Console] = {}


def get_console(ci_mode: bool = False, force_terminal: Optional[bool] = None) -> Console:
    """Get or create the configured Rich Console instance.

    Creates a Console instance with appropriate configuration for TTY or CI mode.
    In CI mode, colors and interactive features are disabled.

    Design Note: This function caches Console instances by (ci_mode, force_terminal)
    to avoid redundant creation while still allowing the same process to use different
    configurations for different operations (e.g., interactive output for user messages,
    CI output for log files).

    :param ci_mode: If True, disable colors and interactive features
    :param force_terminal: Override TTY detection (default: auto-detect)
    :returns: Configured Console instance
    """
    # Create cache key including force_terminal for correctness
    cache_key = (ci_mode, force_terminal)

    # Check cache first
    if cache_key in _console_cache:
        return _console_cache[cache_key]

    # Determine if we should force terminal mode
    if force_terminal is None:
        # In interactive mode, force terminal if TTY detected
        # In CI mode, never force terminal
        force_terminal = not ci_mode and is_tty()

    # Create console with appropriate settings
    console = Console(
        force_terminal=force_terminal,
        no_color=ci_mode,  # Disable colors in CI mode
        highlight=not ci_mode,  # Disable syntax highlighting in CI mode
        markup=True,  # Always allow Rich markup
        emoji=not ci_mode,  # Disable emoji in CI mode (some terminals don't support)
    )

    # Cache the console for reuse
    _console_cache[cache_key] = console
    return console
