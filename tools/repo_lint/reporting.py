"""Output formatting and reporting for repo_lint.

:Purpose:
    Provides stable, deterministic output formatting for linting results.
    Ensures consistent reporting across local development and CI environments.
    Routes all output through the new Reporter UI layer.

:Functions:
    - report_results: Format and print linting results using Reporter
    - report_results_json: Format results as JSON for CI debugging
    - report_results_yaml: Format results as YAML
    - report_results_csv: Format results as CSV files
    - report_results_xlsx: Format results as Excel workbook
    - format_violation: Format a single violation for display
    - print_summary: Print summary statistics

:Environment Variables:
    - REPO_LINT_UI_THEME: Path to custom UI theme YAML file

:Examples:
    Format linting results::

        from tools.repo_lint.reporting import report_results
        exit_code = report_results(all_results, verbose=True, ci_mode=False)

    Format results as JSON::

        from tools.repo_lint.reporting import report_results_json
        exit_code = report_results_json(all_results, verbose=True)

:Exit Codes:
    Functions return exit codes defined in common.ExitCode:
    - 0: All checks passed
    - 1: Violations found
    - 2: Missing tools
"""

import json
import sys
from typing import Any, Dict, List

from tools.repo_lint.common import ExitCode, LintResult, Violation
from tools.repo_lint.ui import Reporter


def format_violation(violation: Violation) -> str:
    """Format a single violation for display.

    :param violation: Violation to format
    :returns: Formatted violation string
    """
    if violation.line:
        return f"{violation.file}:{violation.line}: [{violation.tool}] {violation.message}"
    return f"{violation.file}: [{violation.tool}] {violation.message}"


def report_results(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    results: List[LintResult],
    verbose: bool = False,
    ci_mode: bool = False,
    summary: bool = False,
    summary_only: bool = False,
    summary_format: str = "short",
    show_files: bool = True,
    show_codes: bool = True,
    max_violations: int = None,
    output_format: str = "rich",
    report_path: str = None,
    reports_dir: str = None,
) -> int:
    """Report linting results using Reporter and return appropriate exit code.

    :param results: List of linting results from all runners
    :param verbose: Whether to print verbose output
    :param ci_mode: Whether to use CI mode output
    :param summary: Show summary after results (normal output + summary)
    :param summary_only: Show ONLY summary (no individual violations)
    :param summary_format: Summary format (short|by-tool|by-file|by-code)
    :param show_files: Whether to show per-file breakdown in violations
    :param show_codes: Whether to show tool rule IDs/codes in violations
    :param max_violations: Maximum number of violations to display (None = unlimited)
    :param output_format: Output format (rich|plain|json|yaml|csv|xlsx)
    :param report_path: Path to write consolidated report file
    :param reports_dir: Directory to write per-tool reports
    :returns: Exit code (0 for success, 1 for violations, 3 for errors)
    """
    # Handle non-rich output formats
    if output_format == "json":
        return report_results_json(results, verbose, report_path)
    elif output_format == "yaml":
        return report_results_yaml(results, verbose, report_path)
    elif output_format == "csv":
        return report_results_csv(results, report_path or "report.csv")
    elif output_format == "xlsx":
        return report_results_xlsx(results, report_path or "report.xlsx")

    # Use plain mode for CI if format is "plain"
    if output_format == "plain":
        ci_mode = True

    # Create reporter
    reporter = Reporter(ci_mode=ci_mode)

    # Determine overall status
    all_passed = True
    has_errors = False
    total_violations = 0

    for result in results:
        if result.error:
            has_errors = True
        elif not result.passed:
            all_passed = False
            total_violations += len(result.violations)

    # If summary-only mode, skip detailed output
    if not summary_only:
        # Render results table
        reporter.render_results_table(results)

        # Render failures (if any) with display controls
        reporter.render_failures(
            results,
            show_files=show_files,
            show_codes=show_codes,
            max_violations=max_violations,
        )

    # Determine exit code
    if has_errors:
        exit_code = ExitCode.INTERNAL_ERROR
    elif all_passed:
        exit_code = ExitCode.SUCCESS
    else:
        exit_code = ExitCode.VIOLATIONS

    # Render final summary (always shown, or in specific format if requested)
    if summary or summary_only:
        reporter.render_summary(results, exit_code, summary_format)
    else:
        reporter.render_final_summary(results, exit_code)

    # Write report files if requested
    if report_path:
        _write_report_file(results, report_path, output_format)

    if reports_dir:
        _write_reports_dir(results, reports_dir)

    return int(exit_code)


def print_install_instructions(missing_tools: List[str], ci_mode: bool = False) -> None:
    """Print installation instructions for missing tools.

    :param missing_tools: List of missing tool names
    :param ci_mode: Whether to use CI mode output
    """
    reporter = Reporter(ci_mode=ci_mode)

    reporter.print("\nThe following tools are required but not installed:")
    for tool in missing_tools:
        reporter.print(f"  - {tool}")
    reporter.print("\nTo install missing tools, run:")
    reporter.print("  repo-lint install")
    reporter.print("\nOr install manually following the instructions in HOW-TO-USE-THIS-TOOL.md")


def report_results_json(results: List[LintResult], verbose: bool = False, report_path: str = None) -> int:
    """Report linting results in JSON format and return appropriate exit code.

    :param results: List of linting results from all runners
    :param verbose: Whether to include verbose fields in JSON output
    :param report_path: Optional path to write JSON report to file
    :returns: Exit code (0 for success, 1 for violations, 3 for errors)

    :Notes:
        - JSON output is deterministic and contains no unstable fields
        - Verbose mode adds additional fields for debugging
        - Schema is stable across repo_lint versions
    """
    all_passed = True
    has_errors = False
    total_violations = 0

    # Build JSON output structure
    output: Dict[str, Any] = {
        "version": "1.0",  # Schema version
        "summary": {},
        "results": [],
    }

    # Process results
    for result in results:
        result_dict: Dict[str, Any] = {
            "tool": result.tool,
            "passed": result.passed,
        }

        # Add optional fields
        if result.file_count is not None:
            result_dict["file_count"] = result.file_count
        if result.duration is not None:
            result_dict["duration"] = result.duration

        if result.error:
            has_errors = True
            result_dict["error"] = result.error
        else:
            if not result.passed:
                all_passed = False
                total_violations += len(result.violations)

            # Add violations
            violations_list = []
            for violation in result.violations:
                viol_dict: Dict[str, Any] = {
                    "file": violation.file,
                    "message": violation.message,
                }
                if violation.line is not None:
                    viol_dict["line"] = violation.line

                # Verbose mode: add tool name to each violation
                if verbose:
                    viol_dict["tool"] = violation.tool

                violations_list.append(viol_dict)

            result_dict["violations"] = violations_list
            result_dict["violation_count"] = len(violations_list)

        output["results"].append(result_dict)

    # Add summary
    output["summary"] = {
        "total_tools": len(results),
        "passed": sum(1 for r in results if r.passed),
        "failed": sum(1 for r in results if not r.passed and not r.error),
        "errors": sum(1 for r in results if r.error),
        "total_violations": total_violations,
    }

    # Determine exit code
    if has_errors:
        exit_code = ExitCode.INTERNAL_ERROR
    elif all_passed:
        exit_code = ExitCode.SUCCESS
    else:
        exit_code = ExitCode.VIOLATIONS

    output["exit_code"] = int(exit_code)

    # Output JSON (to stdout or file)
    json_str = json.dumps(output, indent=2)
    if report_path:
        from pathlib import Path

        Path(report_path).write_text(json_str, encoding="utf-8")
        print(f"Report written to {report_path}", file=sys.stderr)
    else:
        print(json_str)

    return int(exit_code)


def report_results_yaml(results: List[LintResult], verbose: bool = False, report_path: str = None) -> int:
    """Report linting results in YAML format.

    :param results: List of linting results from all runners
    :param verbose: Whether to include verbose fields
    :param report_path: Optional path to write YAML report to file
    :returns: Exit code (0 for success, 1 for violations, 3 for errors)
    """
    # Build the same structure as JSON
    all_passed = True
    has_errors = False
    total_violations = 0

    output: Dict[str, Any] = {
        "version": "1.0",
        "summary": {},
        "results": [],
    }

    for result in results:
        result_dict: Dict[str, Any] = {
            "tool": result.tool,
            "passed": result.passed,
        }

        if result.file_count is not None:
            result_dict["file_count"] = result.file_count
        if result.duration is not None:
            result_dict["duration"] = result.duration

        if result.error:
            has_errors = True
            result_dict["error"] = result.error
        else:
            if not result.passed:
                all_passed = False
                total_violations += len(result.violations)

            violations_list = []
            for violation in result.violations:
                viol_dict: Dict[str, Any] = {
                    "file": violation.file,
                    "message": violation.message,
                }
                if violation.line is not None:
                    viol_dict["line"] = violation.line
                if verbose:
                    viol_dict["tool"] = violation.tool
                violations_list.append(viol_dict)

            result_dict["violations"] = violations_list
            result_dict["violation_count"] = len(violations_list)

        output["results"].append(result_dict)

    output["summary"] = {
        "total_tools": len(results),
        "passed": sum(1 for r in results if r.passed),
        "failed": sum(1 for r in results if not r.passed and not r.error),
        "errors": sum(1 for r in results if r.error),
        "total_violations": total_violations,
    }

    if has_errors:
        exit_code = ExitCode.INTERNAL_ERROR
    elif all_passed:
        exit_code = ExitCode.SUCCESS
    else:
        exit_code = ExitCode.VIOLATIONS

    output["exit_code"] = int(exit_code)

    # Output YAML
    try:
        import yaml

        yaml_str = yaml.dump(output, default_flow_style=False, sort_keys=False)
        if report_path:
            from pathlib import Path

            Path(report_path).write_text(yaml_str, encoding="utf-8")
            print(f"Report written to {report_path}", file=sys.stderr)
        else:
            print(yaml_str)
    except ImportError:
        print("Error: PyYAML not installed. Install with: pip install pyyaml", file=sys.stderr)
        return int(ExitCode.INTERNAL_ERROR)

    return int(exit_code)


def report_results_csv(results: List[LintResult], report_path: str) -> int:
    """Report linting results in CSV format.

    :param results: List of linting results from all runners
    :param report_path: Path to write CSV report (without extension)
    :returns: Exit code (0 for success, 1 for violations, 3 for errors)
    """
    import csv
    from pathlib import Path

    # Create CSV files: summary.csv and violations.csv
    base_path = Path(report_path).with_suffix("")
    summary_path = base_path.with_name(f"{base_path.name}-summary.csv")
    violations_path = base_path.with_name(f"{base_path.name}-violations.csv")

    all_passed = True
    has_errors = False
    total_violations = 0

    # Write summary CSV
    with open(summary_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["tool", "passed", "violations", "files", "duration", "error"])
        writer.writeheader()
        for result in results:
            if result.error:
                has_errors = True
            elif not result.passed:
                all_passed = False
                total_violations += len(result.violations)

            writer.writerow(
                {
                    "tool": result.tool,
                    "passed": result.passed,
                    "violations": len(result.violations) if not result.error else "N/A",
                    "files": result.file_count if result.file_count is not None else "N/A",
                    "duration": result.duration if result.duration is not None else "N/A",
                    "error": result.error or "",
                }
            )

    # Write violations CSV
    with open(violations_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["tool", "file", "line", "message"])
        writer.writeheader()
        for result in results:
            if not result.error:
                for violation in result.violations:
                    writer.writerow(
                        {
                            "tool": result.tool,
                            "file": violation.file,
                            "line": violation.line or "",
                            "message": violation.message,
                        }
                    )

    print(f"Reports written to {summary_path} and {violations_path}", file=sys.stderr)

    if has_errors:
        return int(ExitCode.INTERNAL_ERROR)
    elif all_passed:
        return int(ExitCode.SUCCESS)
    else:
        return int(ExitCode.VIOLATIONS)


def report_results_xlsx(results: List[LintResult], report_path: str) -> int:
    """Report linting results in Excel (XLSX) format.

    :param results: List of linting results from all runners
    :param report_path: Path to write XLSX report
    :returns: Exit code (0 for success, 1 for violations, 3 for errors)
    """
    try:
        from openpyxl import Workbook
    except ImportError:
        print("Error: openpyxl not installed. Install with: pip install openpyxl", file=sys.stderr)
        return int(ExitCode.INTERNAL_ERROR)

    all_passed = True
    has_errors = False
    total_violations = 0

    # Create workbook
    wb = Workbook()

    # Summary sheet
    ws_summary = wb.active
    ws_summary.title = "Summary"
    ws_summary.append(["Tool", "Passed", "Violations", "Files", "Duration", "Error"])

    for result in results:
        if result.error:
            has_errors = True
        elif not result.passed:
            all_passed = False
            total_violations += len(result.violations)

        ws_summary.append(
            [
                result.tool,
                "Yes" if result.passed else "No",
                len(result.violations) if not result.error else "N/A",
                result.file_count if result.file_count is not None else "N/A",
                result.duration if result.duration is not None else "N/A",
                result.error or "",
            ]
        )

    # Violations sheet
    ws_violations = wb.create_sheet("Violations")
    ws_violations.append(["Tool", "File", "Line", "Message"])

    for result in results:
        if not result.error:
            for violation in result.violations:
                ws_violations.append(
                    [
                        result.tool,
                        violation.file,
                        violation.line or "",
                        violation.message,
                    ]
                )

    # Save workbook
    wb.save(report_path)
    print(f"Report written to {report_path}", file=sys.stderr)

    if has_errors:
        return int(ExitCode.INTERNAL_ERROR)
    elif all_passed:
        return int(ExitCode.SUCCESS)
    else:
        return int(ExitCode.VIOLATIONS)


def _write_report_file(results: List[LintResult], report_path: str, output_format: str) -> None:
    """Write consolidated report to file based on format.

    :param results: List of linting results
    :param report_path: Path to write report
    :param output_format: Output format (auto-detected from extension if not specified)
    """
    from pathlib import Path

    # Auto-detect format from file extension if format is 'rich' or 'plain'
    if output_format in ("rich", "plain"):
        ext = Path(report_path).suffix.lower()
        if ext == ".json":
            output_format = "json"
        elif ext in (".yaml", ".yml"):
            output_format = "yaml"
        elif ext == ".csv":
            output_format = "csv"
        elif ext == ".xlsx":
            output_format = "xlsx"

    # Write report (these functions handle the file writing internally)
    if output_format == "json":
        report_results_json(results, verbose=False, report_path=report_path)
    elif output_format == "yaml":
        report_results_yaml(results, verbose=False, report_path=report_path)
    elif output_format == "csv":
        report_results_csv(results, report_path)
    elif output_format == "xlsx":
        report_results_xlsx(results, report_path)


def _write_reports_dir(results: List[LintResult], reports_dir: str) -> None:
    """Write per-tool reports to directory.

    :param results: List of linting results
    :param reports_dir: Directory to write reports
    """
    from pathlib import Path

    reports_path = Path(reports_dir)
    reports_path.mkdir(parents=True, exist_ok=True)

    # Write per-tool JSON reports
    for result in results:
        tool_report_path = reports_path / f"{result.tool}.json"
        tool_data = {
            "tool": result.tool,
            "passed": result.passed,
            "violations": (
                []
                if result.error
                else [
                    {
                        "file": v.file,
                        "line": v.line,
                        "message": v.message,
                    }
                    for v in result.violations
                ]
            ),
            "error": result.error,
        }
        tool_report_path.write_text(json.dumps(tool_data, indent=2), encoding="utf-8")

    # Write index summary
    index_path = reports_path / "index.json"
    index_data = {
        "total_tools": len(results),
        "passed": sum(1 for r in results if r.passed),
        "failed": sum(1 for r in results if not r.passed and not r.error),
        "errors": sum(1 for r in results if r.error),
        "total_violations": sum(len(r.violations) for r in results if not r.error),
        "tools": [r.tool for r in results],
    }
    index_path.write_text(json.dumps(index_data, indent=2), encoding="utf-8")

    print(f"Per-tool reports written to {reports_dir}/", file=sys.stderr)
