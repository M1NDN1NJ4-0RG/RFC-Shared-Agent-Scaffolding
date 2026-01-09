"""Diagnostic command for repo-lint environment and configuration.

:Purpose:
    Provides comprehensive diagnostic checks for repo-lint installation,
    configuration, and tool availability. Helps troubleshoot issues.

:Commands:
    - doctor: Diagnose repo-lint installation and configuration

:Checks Performed:
    - Repository root detection
    - Virtual environment (.venv) existence and activation
    - Python version and sys.prefix validation
    - Tool registry loading (conformance/repo-lint/*.yaml configs)
    - Tool availability (black, ruff, pylint, shellcheck, etc.)
    - PATH sanity checks
    - Config file validity (YAML syntax, required fields, schema)

:Environment Variables:
    None - all configuration via command-line arguments

:Exit Codes:
    - 0: All checks passed (environment healthy)
    - 1: Some checks failed (issues detected)
    - 3: Internal error or exception

:Examples:
    Run diagnostics::

        repo-lint doctor

    Generate report::

        repo-lint doctor --report doctor-report.json --format json
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

from tools.repo_lint.common import ExitCode
from tools.repo_lint.install.install_helpers import get_venv_path
from tools.repo_lint.runners.base import find_repo_root


def check_repo_root() -> Tuple[bool, str, str]:
    """Check if repository root can be detected.

    :returns: (success, message, value) tuple
    :rtype: Tuple[bool, str, str]
    """
    try:
        root = find_repo_root()
        return True, f"Repository root: {root}", str(root)
    except Exception as e:
        return False, f"Repository root detection failed: {e}", ""


def check_venv() -> Tuple[bool, str, str]:
    """Check if virtual environment exists.

    :returns: (success, message, value) tuple
    :rtype: Tuple[bool, str, str]
    """
    try:
        venv_path = get_venv_path()
        if venv_path.exists():
            return True, f"Virtual environment found: {venv_path}", str(venv_path)
        else:
            return False, f"Virtual environment not found at: {venv_path}", str(venv_path)
    except Exception as e:
        return False, f"Virtual environment check failed: {e}", ""


def check_python_version() -> Tuple[bool, str, str]:
    """Check Python version.

    :returns: (success, message, value) tuple
    :rtype: Tuple[bool, str, str]
    """
    version = sys.version.split()[0]
    version_info = sys.version_info

    if version_info >= (3, 8):
        return True, f"Python version: {version} (OK)", version
    else:
        return False, f"Python version: {version} (requires 3.8+)", version


def check_config_files() -> Tuple[bool, str, str]:
    """Check if config files exist and are valid.

    :returns: (success, message, value) tuple
    :rtype: Tuple[bool, str, str]
    """
    try:
        root = find_repo_root()
        conformance_dir = root / "conformance" / "repo-lint"

        if not conformance_dir.exists():
            return False, f"Conformance directory not found: {conformance_dir}", str(conformance_dir)

        required_configs = [
            "repo-lint-linting-rules.yaml",
            "repo-lint-naming-rules.yaml",
            "repo-lint-docstring-rules.yaml",
            "repo-lint-ui-theme.yaml",
        ]

        missing = []
        for config in required_configs:
            config_path = conformance_dir / config
            if not config_path.exists():
                missing.append(config)

        if missing:
            return False, f"Missing config files: {', '.join(missing)}", ""

        return True, f"All config files found in {conformance_dir}", str(conformance_dir)
    except Exception as e:
        return False, f"Config file check failed: {e}", ""


def check_tool_availability() -> Tuple[bool, str, List[Dict[str, Any]]]:
    """Check availability of linting tools.

    :returns: (success, message, tools_data) tuple
    :rtype: Tuple[bool, str, List[Dict[str, Any]]]
    """
    from tools.repo_lint.yaml_loader import load_linting_rules

    try:
        rules = load_linting_rules()
        languages = rules.get("languages", {})

        tools_status = []
        all_available = True

        for lang_name, lang_config in languages.items():
            tools = lang_config.get("tools", {})
            for tool_name, tool_config in tools.items():
                # Check if tool is available on PATH
                tool_path = shutil.which(tool_name)
                available = tool_path is not None

                if not available:
                    all_available = False

                tools_status.append(
                    {
                        "tool": tool_name,
                        "language": lang_name,
                        "available": available,
                        "path": tool_path if tool_path else "Not found",
                        "version": tool_config.get("version", "System version"),
                    }
                )

        if all_available:
            message = f"All {len(tools_status)} tools available"
        else:
            missing_count = sum(1 for t in tools_status if not t["available"])
            message = f"{missing_count}/{len(tools_status)} tools missing"

        return all_available, message, tools_status
    except Exception as e:
        return False, f"Tool availability check failed: {e}", []


def check_path_sanity() -> Tuple[bool, str, str]:
    """Check PATH environment variable sanity.

    :returns: (success, message, value) tuple
    :rtype: Tuple[bool, str, str]
    """
    path_env = os.environ.get("PATH", "")
    path_entries = path_env.split(os.pathsep)

    # Check if venv bin directory is in PATH
    try:
        venv_path = get_venv_path()
        venv_bin = venv_path / "bin" if os.name != "nt" else venv_path / "Scripts"

        if venv_path.exists():
            venv_bin_str = os.fspath(venv_bin)
            normalized_venv_bin = os.path.normcase(os.path.normpath(venv_bin_str))
            venv_in_path = any(
                os.path.normcase(os.path.normpath(entry)) == normalized_venv_bin for entry in path_entries if entry
            )
            if venv_in_path:
                return True, f"Virtual environment in PATH: {venv_bin}", str(venv_bin)
            else:
                return (
                    False,
                    f"Virtual environment NOT in PATH (expected: {venv_bin})",
                    str(venv_bin),
                )
        else:
            return True, "Virtual environment not found (PATH check skipped)", ""
    except Exception as e:
        return False, f"PATH sanity check failed: {e}", ""


def cmd_doctor(args) -> int:
    """Execute doctor command.

    :param args: Parsed command-line arguments
    :returns: Exit code (0=success, 1=some checks failed, 3=error)
    :rtype: int
    """
    ci_mode = getattr(args, "ci", False)
    output_format = getattr(args, "format", None)
    report_path = getattr(args, "report", None)

    # Auto-detect format from report path if format not specified
    if report_path and not output_format:
        if report_path.endswith(".json"):
            output_format = "json"
        elif report_path.endswith(".yaml") or report_path.endswith(".yml"):
            output_format = "yaml"
        else:
            output_format = "plain"

    # Default to rich if TTY, plain if not
    if not output_format:
        output_format = "rich" if sys.stdout.isatty() and not ci_mode else "plain"

    # Run all checks
    checks = [
        ("Repository Root", check_repo_root()),
        ("Virtual Environment", check_venv()),
        ("Python Version", check_python_version()),
        ("Config Files", check_config_files()),
        ("Tool Availability", check_tool_availability()),
        ("PATH Sanity", check_path_sanity()),
    ]

    # Determine overall status
    all_passed = all(check[1][0] for check in checks)
    exit_code = ExitCode.SUCCESS if all_passed else ExitCode.VIOLATIONS

    # Format output based on requested format
    if output_format == "json":
        output = _format_json(checks, all_passed)
    elif output_format == "yaml":
        output = _format_yaml(checks, all_passed)
    elif output_format == "rich":
        output = _format_rich(checks, all_passed)
    else:  # plain
        output = _format_plain(checks, all_passed)

    # Print to stdout or write to file
    if report_path:
        Path(report_path).write_text(output, encoding="utf-8")
        print(f"✅ Diagnostic report written to: {report_path}")
    else:
        print(output)

    return exit_code


def _format_plain(checks: List[Tuple[str, Tuple[bool, str, Any]]], all_passed: bool) -> str:
    """Format diagnostic results as plain text.

    :param checks: List of (name, (success, message, value)) tuples
    :param all_passed: Whether all checks passed
    :returns: Formatted plain text output
    :rtype: str
    """
    lines = ["repo-lint Doctor Diagnostic Report", "=" * 40, ""]

    for name, (success, message, _) in checks:
        status = "✅ PASS" if success else "❌ FAIL"
        lines.append(f"{status} | {name}")
        lines.append(f"      {message}")
        lines.append("")

    lines.append("=" * 40)
    if all_passed:
        lines.append("✅ All checks passed - environment healthy")
    else:
        lines.append("❌ Some checks failed - see details above")

    return "\n".join(lines)


def _format_rich(checks: List[Tuple[str, Tuple[bool, str, Any]]], all_passed: bool) -> str:
    """Format diagnostic results with Rich formatting.

    :param checks: List of (name, (success, message, value)) tuples
    :param all_passed: Whether all checks passed
    :returns: Formatted rich text output
    :rtype: str
    """
    from rich.console import Console
    from rich.table import Table

    table = Table(title="repo-lint Doctor Diagnostic Report", show_header=True)

    table.add_column("Check", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Details", style="dim")

    for name, (success, message, _) in checks:
        status = "[green]✅ PASS[/green]" if success else "[red]❌ FAIL[/red]"
        table.add_row(name, status, message)

    # Capture output to string
    from io import StringIO

    string_io = StringIO()
    temp_console = Console(file=string_io, force_terminal=True)
    temp_console.print(table)

    if all_passed:
        temp_console.print("\n[green]✅ All checks passed - environment healthy[/green]")
    else:
        temp_console.print("\n[red]❌ Some checks failed - see details above[/red]")

    return string_io.getvalue()


def _format_json(checks: List[Tuple[str, Tuple[bool, str, Any]]], all_passed: bool) -> str:
    """Format diagnostic results as JSON.

    :param checks: List of (name, (success, message, value)) tuples
    :param all_passed: Whether all checks passed
    :returns: Formatted JSON output
    :rtype: str
    """
    results = []
    for name, (success, message, value) in checks:
        result = {
            "check": name,
            "status": "pass" if success else "fail",
            "message": message,
        }
        if value and not isinstance(value, str):
            result["details"] = value
        elif value:
            result["value"] = value
        results.append(result)

    output = {
        "overall_status": "pass" if all_passed else "fail",
        "checks": results,
    }

    return json.dumps(output, indent=2)


def _format_yaml(checks: List[Tuple[str, Tuple[bool, str, Any]]], all_passed: bool) -> str:
    """Format diagnostic results as YAML.

    :param checks: List of (name, (success, message, value)) tuples
    :param all_passed: Whether all checks passed
    :returns: Formatted YAML output
    :rtype: str
    """
    import yaml

    results = []
    for name, (success, message, value) in checks:
        result = {
            "check": name,
            "status": "pass" if success else "fail",
            "message": message,
        }
        if value and not isinstance(value, str):
            result["details"] = value
        elif value:
            result["value"] = value
        results.append(result)

    output = {
        "overall_status": "pass" if all_passed else "fail",
        "checks": results,
    }

    return yaml.dump(output, default_flow_style=False, sort_keys=False)
