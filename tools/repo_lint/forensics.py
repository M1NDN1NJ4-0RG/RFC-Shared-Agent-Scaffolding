# noqa: EXITCODES
"""Forensics and artifact generation for unsafe fixes.

:Purpose:
    Generates patch files and detailed logs when unsafe fixes are applied.
    These artifacts provide a reviewable trail for all unsafe transformations.

:Artifacts:
    - Patch file: Unified diff of all changes made by unsafe fixers
    - Log file: Detailed record of what was changed, why, and when

:Storage:
    Artifacts are stored in logs/unsafe-fixes/ directory following repo conventions.

:Environment Variables:
    None - all configuration is hardcoded or passed as function parameters.

:Exit Codes:
    N/A - This is a library module, not an executable.

:Examples:
    Generate forensics after running unsafe fixers::

        from datetime import datetime
        from tools.repo_lint.unsafe_fixers import apply_unsafe_fixes
        from tools.repo_lint.forensics import save_forensics

        start_time = datetime.now()
        results = apply_unsafe_fixes([Path("file.py")])
        end_time = datetime.now()

        patch_path, log_path = save_forensics(results, start_time, end_time)
        print(f"Patch: {patch_path}")
        print(f"Log: {log_path}")

:See Also:
    - docs/contributing/ai-constraints.md - AI safety constraints
    - Phase 7 Item 2 (Forensics) requirements
"""

import difflib
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

from tools.repo_lint.common import safe_print
from tools.repo_lint.unsafe_fixers import UnsafeFixerResult


def get_unsafe_logs_dir() -> Path:
    """Get the directory for unsafe fix logs.

    :returns: Path to logs/unsafe-fixes/ directory
    """
    repo_root = Path(__file__).parent.parent.parent
    logs_dir = repo_root / "logs" / "unsafe-fixes"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def generate_patch(results: List[UnsafeFixerResult]) -> str:
    """Generate unified diff patch for all unsafe fix results.

    :param results: List of unsafe fixer results
    :returns: Unified diff patch as string
    """
    if not results:
        return "# No changes made by unsafe fixers\n"

    patch_lines = []
    patch_lines.append("# Unsafe Fix Patch")
    patch_lines.append(f"# Generated: {datetime.now().isoformat()}")
    patch_lines.append("#")
    patch_lines.append("# DANGER: This patch contains unsafe transformations.")
    patch_lines.append("# Review carefully before applying or committing.")
    patch_lines.append("#")
    patch_lines.append("")

    for result in results:
        # Generate unified diff for this file
        before_lines = result.before_content.splitlines(keepends=True)
        after_lines = result.after_content.splitlines(keepends=True)

        diff = difflib.unified_diff(
            before_lines,
            after_lines,
            fromfile=f"a/{result.file_path}",
            tofile=f"b/{result.file_path}",
            lineterm="",
        )

        patch_lines.extend(diff)
        patch_lines.append("")

    return "\n".join(patch_lines)


def generate_log(results: List[UnsafeFixerResult], start_time: datetime, end_time: datetime) -> str:
    """Generate detailed log of unsafe fix operations.

    :param results: List of unsafe fixer results
    :param start_time: When unsafe fix mode started
    :param end_time: When unsafe fix mode completed
    :returns: Detailed log as string
    """
    log_lines = []
    log_lines.append("# Unsafe Fix Execution Log")
    log_lines.append(f"# Start: {start_time.isoformat()}")
    log_lines.append(f"# End: {end_time.isoformat()}")
    log_lines.append(f"# Duration: {(end_time - start_time).total_seconds():.2f}s")
    log_lines.append("#")
    log_lines.append("# DANGER: Unsafe fixes can change code behavior.")
    log_lines.append("# Review all changes before committing.")
    log_lines.append("#")
    log_lines.append("")

    if not results:
        log_lines.append("## Summary")
        log_lines.append("No changes made - no files required unsafe fixes.")
        log_lines.append("")
        return "\n".join(log_lines)

    # Summary section
    log_lines.append("## Summary")
    log_lines.append(f"- Files modified: {len(results)}")
    log_lines.append(f"- Fixers applied: {len(set(r.fixer_name for r in results))}")
    log_lines.append("")

    # Fixer breakdown
    fixer_counts = {}
    for result in results:
        fixer_counts[result.fixer_name] = fixer_counts.get(result.fixer_name, 0) + 1

    log_lines.append("## Fixers Used")
    for fixer_name, count in sorted(fixer_counts.items()):
        log_lines.append(f"- {fixer_name}: {count} file(s)")
    log_lines.append("")

    # Detailed changes
    log_lines.append("## Detailed Changes")
    log_lines.append("")

    for i, result in enumerate(results, 1):
        log_lines.append(f"### {i}. {result.file_path}")
        log_lines.append(f"- **Fixer:** {result.fixer_name}")
        log_lines.append(f"- **Changes:** {result.changes_made}")
        log_lines.append(f"- **Why Unsafe:** {result.why_unsafe}")
        log_lines.append("")

    # Tool versions (placeholder - could be extended)
    log_lines.append("## Tool Versions")
    log_lines.append("- repo_lint: (version info would go here)")
    log_lines.append("- Python: (version info would go here)")
    log_lines.append("")

    return "\n".join(log_lines)


def save_forensics(results: List[UnsafeFixerResult], start_time: datetime, end_time: datetime) -> Tuple[Path, Path]:
    """Save patch and log files for unsafe fix operations.

    :param results: List of unsafe fixer results
    :param start_time: When unsafe fix mode started
    :param end_time: When unsafe fix mode completed
    :returns: Tuple of (patch_path, log_path)
    """
    logs_dir = get_unsafe_logs_dir()

    # Generate timestamp-based filename
    timestamp = start_time.strftime("%Y%m%d-%H%M%S")
    patch_path = logs_dir / f"unsafe-fix-{timestamp}.patch"
    log_path = logs_dir / f"unsafe-fix-{timestamp}.log"

    # Generate and save patch
    patch_content = generate_patch(results)
    patch_path.write_text(patch_content)

    # Generate and save log
    log_content = generate_log(results, start_time, end_time)
    log_path.write_text(log_content)

    return patch_path, log_path


def print_forensics_summary(patch_path: Path, log_path: Path, results: List[UnsafeFixerResult]) -> None:
    """Print summary of forensic artifacts to stdout.

    :param patch_path: Path to generated patch file
    :param log_path: Path to generated log file
    :param results: List of unsafe fixer results
    """
    print("")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  Unsafe Fix Forensics")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("")

    if results:
        safe_print(
            f"✓ Changes made: {len(results)} file(s) modified",
            f"Changes made: {len(results)} file(s) modified",
        )
    else:
        safe_print(
            "✓ No changes made - no files required unsafe fixes", "No changes made - no files required unsafe fixes"
        )

    print("")
    print("Forensic artifacts generated:")
    safe_print(f"  📄 Patch: {patch_path}", f"  Patch: {patch_path}")
    safe_print(f"  📋 Log:   {log_path}", f"  Log:   {log_path}")
    print("")
    safe_print("⚠️  REVIEW THESE FILES BEFORE COMMITTING!", "WARNING: REVIEW THESE FILES BEFORE COMMITTING!")
    print("")
