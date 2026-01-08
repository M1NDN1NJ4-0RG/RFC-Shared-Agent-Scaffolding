"""Centralized logging configuration with Rich integration for repo_lint.

:Purpose:
    Provides a unified logging infrastructure that integrates Python's logging
    module with Rich formatting for beautiful console output in TTY contexts
    while falling back to plain logging in CI/non-TTY environments.

:Functions:
    - get_logger: Get or create a configured logger instance
    - configure_logging: Set global logging configuration (level, handlers)
    - is_verbose_mode: Check if verbose logging is enabled
    - set_verbose_mode: Enable/disable verbose logging

:Environment Variables:
    - REPO_LINT_VERBOSE: If set to "1", enables DEBUG level logging

:Exit Codes:
    This module does not define or use exit codes (logging configuration only):
    - 0: Not applicable (see tools.repo_lint.common.ExitCode)
    - 1: Not applicable (see tools.repo_lint.common.ExitCode)

:Examples:
    Get logger for a module::

        from tools.repo_lint.logging_utils import get_logger
        logger = get_logger(__name__)
        logger.info("Starting validation")
        logger.debug("Processing file: %s", file_path)

    Configure verbose logging::

        from tools.repo_lint.logging_utils import configure_logging, set_verbose_mode
        set_verbose_mode(True)  # Enable DEBUG level
        configure_logging()  # Apply changes

    Use in CI mode (no Rich formatting)::

        from tools.repo_lint.logging_utils import configure_logging
        configure_logging(ci_mode=True)
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Dict, Optional

from rich.console import Console
from rich.logging import RichHandler

# Global state for logging configuration
_verbose_mode: bool = False
_loggers_cache: Dict[str, logging.Logger] = {}
_handlers_configured: bool = False


def is_tty() -> bool:
    """Check if stdout is a TTY.

    :returns: True if stdout is a TTY, False otherwise
    """
    return sys.stdout.isatty()


def is_verbose_mode() -> bool:
    """Check if verbose logging is enabled.

    :returns: True if verbose mode (DEBUG level) is enabled, False otherwise
    """
    return _verbose_mode or os.environ.get("REPO_LINT_VERBOSE") == "1"


def set_verbose_mode(enabled: bool) -> None:
    """Enable or disable verbose logging.

    :param enabled: If True, sets logging level to DEBUG; if False, to INFO
    """
    global _verbose_mode  # pylint: disable=global-statement
    _verbose_mode = enabled


def get_logger(name: str) -> logging.Logger:
    """Get or create a configured logger instance.

    Creates a logger with the specified name. Loggers are cached to avoid
    redundant creation. The logger will use the handlers configured via
    configure_logging().

    :param name: Logger name (typically __name__ from calling module)
    :returns: Configured Logger instance

    :Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing started")
        >>> logger.debug("File path: %s", path)
    """
    # Check cache first
    if name in _loggers_cache:
        return _loggers_cache[name]

    # Create logger
    logger = logging.getLogger(name)

    # Ensure handlers are configured
    if not _handlers_configured:
        configure_logging()

    # Cache the logger for reuse
    _loggers_cache[name] = logger
    return logger


def configure_logging(
    ci_mode: bool = False,
    level: Optional[int] = None,
    quiet: bool = False,
) -> None:
    """Configure global logging settings with Rich or plain handlers.

    This function sets up the root logger with appropriate handlers based on
    the execution context:
    - TTY mode: Uses RichHandler for beautiful formatted logs
    - CI mode: Uses StreamHandler for plain, ANSI-free logs
    - Quiet mode: Suppresses INFO level logs, shows only warnings and errors

    Design Note: This function should be called once at application startup
    (e.g., in main CLI entry point) before any logging occurs.

    :param ci_mode: If True, use plain logging without Rich formatting
    :param level: Logging level (default: DEBUG if verbose, INFO otherwise)
    :param quiet: If True, set level to WARNING to suppress info messages

    :Example:
        >>> # In main CLI entry point
        >>> from tools.repo_lint.logging_utils import configure_logging
        >>> configure_logging(ci_mode=args.ci, quiet=args.quiet)
    """
    global _handlers_configured  # pylint: disable=global-statement

    # Determine logging level
    if quiet:
        effective_level = logging.WARNING
    elif level is not None:
        effective_level = level
    elif is_verbose_mode():
        effective_level = logging.DEBUG
    else:
        effective_level = logging.INFO

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(effective_level)

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Choose handler based on context
    if ci_mode or not is_tty():
        # Use plain StreamHandler for CI or non-TTY contexts
        handler = logging.StreamHandler(sys.stderr)
        formatter = logging.Formatter(
            fmt="[%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
    else:
        # Use RichHandler for interactive TTY contexts
        console = Console(
            stderr=True,  # Log to stderr to keep stdout clean for data
            force_terminal=True,
            no_color=False,
            highlight=True,
            markup=True,
            emoji=True,
        )
        handler = RichHandler(
            console=console,
            show_time=True,
            show_path=False,  # Module name is sufficient, full path is verbose
            rich_tracebacks=True,
            tracebacks_show_locals=is_verbose_mode(),  # Show locals only in verbose mode
            markup=True,
        )
        # Rich handles its own formatting, so use minimal log record formatting
        handler.setFormatter(logging.Formatter("%(message)s"))

    # Add handler to root logger
    root_logger.addHandler(handler)

    # Mark handlers as configured
    _handlers_configured = True


# Convenience functions for common logging patterns


def log_tool_execution(
    logger: logging.Logger,
    tool_name: str,
    command: list[str],
    cwd: Optional[str] = None,
) -> None:
    """Log tool execution details.

    :param logger: Logger instance to use
    :param tool_name: Name of the tool being executed
    :param command: Command and arguments being executed
    :param cwd: Working directory (optional)
    """
    if cwd:
        logger.debug("Executing %s: %s (cwd: %s)", tool_name, " ".join(command), cwd)
    else:
        logger.debug("Executing %s: %s", tool_name, " ".join(command))


def log_tool_result(
    logger: logging.Logger,
    tool_name: str,
    exit_code: int,
    violations_count: int = 0,
) -> None:
    """Log tool execution result.

    :param logger: Logger instance to use
    :param tool_name: Name of the tool that executed
    :param exit_code: Exit code from the tool
    :param violations_count: Number of violations found (if applicable)
    """
    if exit_code == 0:
        if violations_count > 0:
            logger.info("%s: Found %d violation(s)", tool_name, violations_count)
        else:
            logger.info("%s: ✓ No violations", tool_name)
    else:
        logger.warning("%s: Failed with exit code %d", tool_name, exit_code)


def log_file_operation(
    logger: logging.Logger,
    operation: str,
    file_path: str,
    success: bool = True,
) -> None:
    """Log file operation (read, write, delete, etc.).

    :param logger: Logger instance to use
    :param operation: Operation type (e.g., "read", "write", "delete")
    :param file_path: Path to the file
    :param success: Whether the operation succeeded
    """
    if success:
        logger.debug("%s: %s", operation.capitalize(), file_path)
    else:
        logger.error("%s failed: %s", operation.capitalize(), file_path)


def log_progress(
    logger: logging.Logger,
    message: str,
    current: int,
    total: int,
) -> None:
    """Log progress for long-running operations.

    :param logger: Logger instance to use
    :param message: Progress message template
    :param current: Current item number
    :param total: Total items to process
    """
    logger.info("%s (%d/%d)", message, current, total)
