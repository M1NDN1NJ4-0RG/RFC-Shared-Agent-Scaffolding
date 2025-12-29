"""Output formatting and reporting for repo_lint.

:Purpose:
    Provides stable, deterministic output formatting for linting results.
    Ensures consistent reporting across local development and CI environments.

:Functions:
    - report_results: Format and print linting results
    - format_violation: Format a single violation for display
    - print_summary: Print summary statistics
"""

from typing import List

from tools.repo_lint.common import LintResult, Violation


def format_violation(violation: Violation) -> str:
    """Format a single violation for display.

    :Args:
        violation: Violation to format

    :Returns:
        Formatted violation string
    """
    if violation.line:
        return f"{violation.file}:{violation.line}: [{violation.tool}] {violation.message}"
    return f"{violation.file}: [{violation.tool}] {violation.message}"


def report_results(results: List[LintResult], verbose: bool = False) -> int:
    """Report linting results and return appropriate exit code.

    :Args:
        results: List of linting results from all runners
        verbose: Whether to print verbose output

    :Returns:
        Exit code (0 for success, 1 for violations, 3 for errors)
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

    :Args:
        missing_tools: List of missing tool names
    """
    print("━" * 80)
    print("  Missing Tools")
    print("━" * 80)
    print("\nThe following tools are required but not installed:")
    for tool in missing_tools:
        print(f"  - {tool}")
    print("\nTo install missing tools, run:")
    print("  python -m tools.repo_lint install")
    print("\nOr install manually following the instructions in CONTRIBUTING.md")
    print("━" * 80)
