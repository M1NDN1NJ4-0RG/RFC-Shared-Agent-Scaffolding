"""Output formatting and reporting for repo_lint.

:Purpose:
    Provides stable, deterministic output formatting for linting results.
    Ensures consistent reporting across local development and CI environments.

:Functions:
    - report_results: Format and print linting results
    - report_results_json: Format results as JSON for CI debugging
    - format_violation: Format a single violation for display
    - print_summary: Print summary statistics

:Environment Variables:
    None

:Examples:
    Format linting results::

        from tools.repo_lint.reporting import report_results
        exit_code = report_results(all_results, verbose=True)

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
from typing import Any, Dict, List

from tools.repo_lint.common import LintResult, Violation


def format_violation(violation: Violation) -> str:
    """Format a single violation for display.

    :param violation: Violation to format
    :returns: Formatted violation string
    """
    if violation.line:
        return f"{violation.file}:{violation.line}: [{violation.tool}] {violation.message}"
    return f"{violation.file}: [{violation.tool}] {violation.message}"


def report_results(results: List[LintResult], verbose: bool = False) -> int:
    """Report linting results and return appropriate exit code.

    :param results: List of linting results from all runners
    :param verbose: Whether to print verbose output
    :returns: Exit code (0 for success, 1 for violations, 3 for errors)
    """
    all_passed = True
    has_errors = False
    total_violations = 0

    print("━" * 80)
    print("  Linting Results")
    print("━" * 80)

    for result in results:
        if result.error:
            has_errors = True
            print(f"\n❌ {result.tool}: ERROR")
            print(f"   {result.error}")
            continue

        if result.passed:
            if verbose:
                print(f"✅ {result.tool}: PASSED")
        else:
            all_passed = False
            total_violations += len(result.violations)
            print(f"\n❌ {result.tool}: FAILED ({len(result.violations)} violation(s))")

            # Print violations
            for violation in result.violations:
                print(f"   {format_violation(violation)}")

    # Summary
    print("\n" + "━" * 80)
    if has_errors:
        print("❌ Some linters encountered errors. See output above for details.")
        return 3
    elif all_passed:
        print("✅ All linting checks passed!")
        return 0
    else:
        print(f"❌ Found {total_violations} violation(s) across {len([r for r in results if not r.passed])} tool(s)")
        return 1


def print_install_instructions(missing_tools: List[str]) -> None:
    """Print installation instructions for missing tools.

    :param missing_tools: List of missing tool names
    """
    print("━" * 80)
    print("  Missing Tools")
    print("━" * 80)
    print("\nThe following tools are required but not installed:")
    for tool in missing_tools:
        print(f"  - {tool}")
    print("\nTo install missing tools, run:")
    print("  python3 -m tools.repo_lint install")
    print("\nOr install manually following the instructions in CONTRIBUTING.md")
    print("━" * 80)


def report_results_json(results: List[LintResult], verbose: bool = False) -> int:
    """Report linting results in JSON format and return appropriate exit code.

    :param results: List of linting results from all runners
    :param verbose: Whether to include verbose fields in JSON output
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
        "passed": all_passed and not has_errors,
        "total_violations": total_violations,
        "failed_tools": len([r for r in results if not r.passed]),
        "errored_tools": len([r for r in results if r.error]),
    }

    # Verbose mode: add tool names in summary
    if verbose:
        output["summary"]["tools_run"] = [r.tool for r in results]
        output["summary"]["failed_tool_names"] = [r.tool for r in results if not r.passed]
        output["summary"]["errored_tool_names"] = [r.tool for r in results if r.error]

    # Print JSON output
    print(json.dumps(output, indent=2, sort_keys=True))

    # Return appropriate exit code
    if has_errors:
        return 3
    elif all_passed:
        return 0
    else:
        return 1
