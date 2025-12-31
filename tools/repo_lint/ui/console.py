"""Single console instance management for repo_lint.

:Purpose:
    Provides a single, configured Rich Console instance per run with proper
    TTY detection and CI mode handling.

:Functions:
    - get_console: Get or create the configured Console instance
    - is_tty: Check if stdout is a TTY

:Environment Variables:
    None

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
from typing import Optional

from rich.console import Console


def is_tty() -> bool:
    """Check if stdout is a TTY.

    :returns: True if stdout is a TTY, False otherwise
    """
    return sys.stdout.isatty()


def get_console(ci_mode: bool = False, force_terminal: Optional[bool] = None) -> Console:
    """Get or create the configured Rich Console instance.

    Creates a Console instance with appropriate configuration for TTY or CI mode.
    In CI mode, colors and interactive features are disabled.

    Note: This function creates a new console each time to ensure ci_mode changes
    are respected. The previous singleton pattern cached the first console created,
    which could cause issues if the same process needed both CI and interactive modes.

    :param ci_mode: If True, disable colors and interactive features
    :param force_terminal: Override TTY detection (default: auto-detect)
    :returns: Configured Console instance
    """
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

    return console
