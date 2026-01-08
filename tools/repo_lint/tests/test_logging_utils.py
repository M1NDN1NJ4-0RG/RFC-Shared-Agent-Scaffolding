"""Unit tests for tools.repo_lint.logging_utils module.

:Purpose:
    Comprehensive test coverage for the logging utilities module including
    TTY vs non-TTY formatting, log level filtering, and ANSI code prevention.
"""

from __future__ import annotations

import io
import logging
import os
import sys
from unittest import mock

import pytest

# Add tools directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

# pylint: disable=wrong-import-position
from tools.repo_lint.logging_utils import (
    configure_logging,
    get_logger,
    is_verbose_mode,
    log_file_operation,
    log_progress,
    log_tool_execution,
    log_tool_result,
    set_verbose_mode,
)

# pylint: enable=wrong-import-position


class TestLoggingConfiguration:
    """Test logging configuration and setup."""

    def test_configure_logging_ci_mode_uses_plain_handler(self) -> None:
        """Test that CI mode uses plain StreamHandler without Rich formatting."""
        # Reset logging state
        root = logging.getLogger()
        for handler in root.handlers[:]:
            root.removeHandler(handler)

        # Configure in CI mode
        configure_logging(ci_mode=True, level=logging.INFO)

        # Verify plain handler is used (not RichHandler)
        assert len(root.handlers) == 1
        handler = root.handlers[0]
        assert isinstance(handler, logging.StreamHandler)
        assert not hasattr(handler, "console")  # RichHandler has console attribute

    def test_configure_logging_tty_mode_uses_rich_handler(self) -> None:
        """Test that TTY mode uses RichHandler for beautiful formatting."""
        # Reset logging state
        root = logging.getLogger()
        for handler in root.handlers[:]:
            root.removeHandler(handler)

        # Mock TTY detection to return True
        with mock.patch("tools.repo_lint.logging_utils.is_tty", return_value=True):
            configure_logging(ci_mode=False, level=logging.INFO)

        # Verify RichHandler is used
        assert len(root.handlers) == 1
        handler = root.handlers[0]
        # RichHandler has these attributes
        assert hasattr(handler, "console")
        assert hasattr(handler, "rich_tracebacks")

    def test_configure_logging_non_tty_uses_plain_handler(self) -> None:
        """Test that non-TTY (even without ci_mode) uses plain handler."""
        # Reset logging state
        root = logging.getLogger()
        for handler in root.handlers[:]:
            root.removeHandler(handler)

        # Mock TTY detection to return False
        with mock.patch("tools.repo_lint.logging_utils.is_tty", return_value=False):
            configure_logging(ci_mode=False, level=logging.INFO)

        # Verify plain handler is used
        assert len(root.handlers) == 1
        handler = root.handlers[0]
        assert isinstance(handler, logging.StreamHandler)
        assert not hasattr(handler, "console")

    def test_configure_logging_removes_existing_handlers(self) -> None:
        """Test that configure_logging removes existing handlers to avoid duplicates."""
        # Reset logging state and add a dummy handler
        root = logging.getLogger()
        for handler in root.handlers[:]:
            root.removeHandler(handler)
        dummy_handler = logging.StreamHandler()
        root.addHandler(dummy_handler)

        # Configure logging
        configure_logging(ci_mode=True, level=logging.INFO)

        # Verify only one handler exists and it's not the dummy
        assert len(root.handlers) == 1
        assert root.handlers[0] is not dummy_handler

    def test_configure_logging_quiet_mode_sets_warning_level(self) -> None:
        """Test that quiet mode suppresses INFO messages."""
        # Reset logging state
        root = logging.getLogger()
        for handler in root.handlers[:]:
            root.removeHandler(handler)

        # Configure in quiet mode
        configure_logging(ci_mode=True, quiet=True)

        # Verify logging level is WARNING
        assert root.level == logging.WARNING

    def test_configure_logging_verbose_mode_sets_debug_level(self) -> None:
        """Test that verbose mode enables DEBUG level logging."""
        # Reset logging state
        root = logging.getLogger()
        for handler in root.handlers[:]:
            root.removeHandler(handler)

        # Enable verbose mode
        set_verbose_mode(True)

        # Configure logging
        configure_logging(ci_mode=True)

        # Verify logging level is DEBUG
        assert root.level == logging.DEBUG

        # Reset verbose mode
        set_verbose_mode(False)

    def test_configure_logging_explicit_level_overrides_verbose(self) -> None:
        """Test that explicit level parameter overrides verbose mode."""
        # Reset logging state
        root = logging.getLogger()
        for handler in root.handlers[:]:
            root.removeHandler(handler)

        # Enable verbose mode but pass explicit level
        set_verbose_mode(True)
        configure_logging(ci_mode=True, level=logging.WARNING)

        # Verify explicit level is used
        assert root.level == logging.WARNING

        # Reset verbose mode
        set_verbose_mode(False)


class TestLoggerCreation:
    """Test logger creation and caching."""

    def test_get_logger_creates_logger(self) -> None:
        """Test that get_logger creates a logger instance."""
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"

    def test_get_logger_caches_loggers(self) -> None:
        """Test that get_logger caches logger instances."""
        logger1 = get_logger("test_module")
        logger2 = get_logger("test_module")
        assert logger1 is logger2  # Same instance

    def test_get_logger_creates_different_loggers_for_different_names(self) -> None:
        """Test that different names get different logger instances."""
        logger1 = get_logger("module_a")
        logger2 = get_logger("module_b")
        assert logger1 is not logger2
        assert logger1.name == "module_a"
        assert logger2.name == "module_b"


class TestVerboseMode:
    """Test verbose mode management."""

    def test_is_verbose_mode_default_false(self) -> None:
        """Test that verbose mode is False by default."""
        # Reset verbose mode
        set_verbose_mode(False)
        assert is_verbose_mode() is False

    def test_set_verbose_mode_enables(self) -> None:
        """Test that set_verbose_mode(True) enables verbose mode."""
        set_verbose_mode(True)
        assert is_verbose_mode() is True
        # Reset
        set_verbose_mode(False)

    def test_set_verbose_mode_disables(self) -> None:
        """Test that set_verbose_mode(False) disables verbose mode."""
        set_verbose_mode(True)
        set_verbose_mode(False)
        assert is_verbose_mode() is False

    def test_is_verbose_mode_checks_environment(self) -> None:
        """Test that is_verbose_mode checks REPO_LINT_VERBOSE env var."""
        set_verbose_mode(False)
        with mock.patch.dict(os.environ, {"REPO_LINT_VERBOSE": "1"}):
            assert is_verbose_mode() is True


class TestLoggingOutput:
    """Test logging output and ANSI code prevention."""

    def test_ci_mode_produces_ansi_free_output(self) -> None:
        """Test that CI mode produces output without ANSI escape codes."""
        # Reset logging state
        root = logging.getLogger()
        for handler in root.handlers[:]:
            root.removeHandler(handler)

        # Capture stderr
        stderr_capture = io.StringIO()
        with mock.patch("sys.stderr", stderr_capture):
            configure_logging(ci_mode=True, level=logging.INFO)
            logger = get_logger("test_ansi")
            logger.info("Test message")

        output = stderr_capture.getvalue()
        # Verify no ANSI escape codes (ESC character is \x1b)
        assert "\x1b" not in output
        assert "Test message" in output

    def test_info_level_filters_debug_messages(self) -> None:
        """Test that INFO level suppresses DEBUG messages."""
        # Reset logging state
        root = logging.getLogger()
        for handler in root.handlers[:]:
            root.removeHandler(handler)

        # Capture stderr
        stderr_capture = io.StringIO()
        with mock.patch("sys.stderr", stderr_capture):
            configure_logging(ci_mode=True, level=logging.INFO)
            logger = get_logger("test_filter")
            logger.debug("Debug message - should not appear")
            logger.info("Info message - should appear")

        output = stderr_capture.getvalue()
        assert "Debug message" not in output
        assert "Info message" in output

    def test_warning_level_filters_info_messages(self) -> None:
        """Test that WARNING level suppresses INFO messages."""
        # Reset logging state
        root = logging.getLogger()
        for handler in root.handlers[:]:
            root.removeHandler(handler)

        # Capture stderr
        stderr_capture = io.StringIO()
        with mock.patch("sys.stderr", stderr_capture):
            configure_logging(ci_mode=True, level=logging.WARNING)
            logger = get_logger("test_filter")
            logger.info("Info message - should not appear")
            logger.warning("Warning message - should appear")

        output = stderr_capture.getvalue()
        assert "Info message" not in output
        assert "Warning message" in output


class TestConvenienceFunctions:
    """Test convenience logging functions."""

    def test_log_tool_execution_basic(self) -> None:
        """Test log_tool_execution with basic command."""
        # Reset logging state
        root = logging.getLogger()
        for handler in root.handlers[:]:
            root.removeHandler(handler)

        # Capture stderr
        stderr_capture = io.StringIO()
        with mock.patch("sys.stderr", stderr_capture):
            configure_logging(ci_mode=True, level=logging.DEBUG)
            logger = get_logger("test_tool")
            log_tool_execution(logger, "ruff", ["ruff", "check", "file.py"])

        output = stderr_capture.getvalue()
        assert "ruff" in output
        assert "ruff check file.py" in output

    def test_log_tool_execution_with_cwd(self) -> None:
        """Test log_tool_execution with working directory."""
        # Reset logging state
        root = logging.getLogger()
        for handler in root.handlers[:]:
            root.removeHandler(handler)

        # Capture stderr
        stderr_capture = io.StringIO()
        with mock.patch("sys.stderr", stderr_capture):
            configure_logging(ci_mode=True, level=logging.DEBUG)
            logger = get_logger("test_tool")
            log_tool_execution(logger, "ruff", ["ruff", "check"], cwd="/tmp/test")

        output = stderr_capture.getvalue()
        assert "ruff" in output
        assert "/tmp/test" in output

    def test_log_tool_result_success_no_violations(self) -> None:
        """Test log_tool_result for successful execution with no violations."""
        # Reset logging state
        root = logging.getLogger()
        for handler in root.handlers[:]:
            root.removeHandler(handler)

        # Capture stderr
        stderr_capture = io.StringIO()
        with mock.patch("sys.stderr", stderr_capture):
            configure_logging(ci_mode=True, level=logging.INFO)
            logger = get_logger("test_tool")
            log_tool_result(logger, "ruff", exit_code=0, violations_count=0)

        output = stderr_capture.getvalue()
        assert "ruff" in output
        assert "No violations" in output

    def test_log_tool_result_success_with_violations(self) -> None:
        """Test log_tool_result for successful execution with violations."""
        # Reset logging state
        root = logging.getLogger()
        for handler in root.handlers[:]:
            root.removeHandler(handler)

        # Capture stderr
        stderr_capture = io.StringIO()
        with mock.patch("sys.stderr", stderr_capture):
            configure_logging(ci_mode=True, level=logging.INFO)
            logger = get_logger("test_tool")
            log_tool_result(logger, "ruff", exit_code=0, violations_count=5)

        output = stderr_capture.getvalue()
        assert "ruff" in output
        assert "5 violation(s)" in output

    def test_log_tool_result_failure(self) -> None:
        """Test log_tool_result for failed execution."""
        # Reset logging state
        root = logging.getLogger()
        for handler in root.handlers[:]:
            root.removeHandler(handler)

        # Capture stderr
        stderr_capture = io.StringIO()
        with mock.patch("sys.stderr", stderr_capture):
            configure_logging(ci_mode=True, level=logging.INFO)
            logger = get_logger("test_tool")
            log_tool_result(logger, "ruff", exit_code=2)

        output = stderr_capture.getvalue()
        assert "ruff" in output
        assert "Failed" in output
        assert "exit code 2" in output

    def test_log_file_operation_success(self) -> None:
        """Test log_file_operation for successful operation."""
        # Reset logging state
        root = logging.getLogger()
        for handler in root.handlers[:]:
            root.removeHandler(handler)

        # Capture stderr
        stderr_capture = io.StringIO()
        with mock.patch("sys.stderr", stderr_capture):
            configure_logging(ci_mode=True, level=logging.DEBUG)
            logger = get_logger("test_file")
            log_file_operation(logger, "write", "/tmp/test.txt", success=True)

        output = stderr_capture.getvalue()
        assert "Write" in output
        assert "/tmp/test.txt" in output

    def test_log_file_operation_failure(self) -> None:
        """Test log_file_operation for failed operation."""
        # Reset logging state
        root = logging.getLogger()
        for handler in root.handlers[:]:
            root.removeHandler(handler)

        # Capture stderr
        stderr_capture = io.StringIO()
        with mock.patch("sys.stderr", stderr_capture):
            configure_logging(ci_mode=True, level=logging.DEBUG)
            logger = get_logger("test_file")
            log_file_operation(logger, "read", "/tmp/test.txt", success=False)

        output = stderr_capture.getvalue()
        assert "Read failed" in output
        assert "/tmp/test.txt" in output

    def test_log_progress(self) -> None:
        """Test log_progress for progress reporting."""
        # Reset logging state
        root = logging.getLogger()
        for handler in root.handlers[:]:
            root.removeHandler(handler)

        # Capture stderr
        stderr_capture = io.StringIO()
        with mock.patch("sys.stderr", stderr_capture):
            configure_logging(ci_mode=True, level=logging.INFO)
            logger = get_logger("test_progress")
            log_progress(logger, "Processing files", current=5, total=10)

        output = stderr_capture.getvalue()
        assert "Processing files" in output
        assert "(5/10)" in output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
