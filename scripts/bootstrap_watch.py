#!/usr/bin/env python3
"""Bootstrap Progress Watcher.

Runs the bootstrap script and filters output to show a condensed view
of progress steps and final results.

:Purpose:
    Provide filtered, focused output from the bootstrapper script by showing
    all progress lines with step indicators ([N/M]) and all output from the
    last progress step onward. This reduces noise while preserving visibility
    into step-by-step progress and any final output or errors.

:Functions:
    - main: Execute bootstrap script and filter output to show progress steps

:Outputs:
    - Filtered bootstrap output showing progress lines and final summary
    - Exit code matching the bootstrap script's exit code

:Environment Variables:
    None. This script does not read environment variables.

:Examples:
    >>> # Run from repository root
    >>> ./scripts/bootstrap_watch.py
    [bootstrap] [1/13] Parsing arguments...
    [bootstrap] ✓ [1/13] Parsing arguments (0s)
    ...
    [bootstrap] [13/13] Running verification gate...
    [bootstrap] ✓ [13/13] Running verification gate (43s)

:Exit Codes:
    This script exits with the same code as the bootstrap script it wraps.

    - 0: Bootstrap script succeeded
    - 1: Bootstrap script failed or file not found
"""

import re
import subprocess
import sys


def main():
    """Run bootstrap script and filter output to show progress steps.

    :returns: Exit code from the bootstrap script (0 = success, 1 = failure).
    :raises FileNotFoundError: If bootstrap script not found at expected path.
    :raises Exception: For any other subprocess execution errors.
    """
    # Run the bootstrap script and capture all output
    script_path = "./scripts/bootstrap-repo-lint-toolchain.sh"
    try:
        result = subprocess.run(
            [script_path],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        # Combine stdout and stderr
        output = result.stdout + result.stderr
        lines = output.splitlines()

        # Filter out tar extended header warnings (noise from macOS metadata)
        tar_warning_pattern = re.compile(
            r"^(/usr/bin/)?tar: Ignoring unknown extended header keyword 'LIBARCHIVE\.xattr\..*'"
        )
        # Filter out Go module download noise
        go_download_pattern = re.compile(r"^go: downloading ")
        lines = [
            line
            for line in lines
            if not tar_warning_pattern.match(line) and not go_download_pattern.match(line)
        ]

        # Pattern to match progress lines: [bootstrap] ... [N/M] ...
        re_prog = re.compile(r"^\[bootstrap\].*\[[0-9]+/[0-9]+\]")

        # Find all lines matching the progress pattern
        matches = [i for i, line in enumerate(lines) if re_prog.match(line)]

        if not matches:
            # No progress lines found, print everything
            print("\n".join(lines))
            return result.returncode

        # Print all progress lines except the last one
        for i in matches[:-1]:
            print(lines[i])

        # Print everything from the last progress line onward
        last = matches[-1]
        for line in lines[last:]:
            print(line)

        return result.returncode

    except FileNotFoundError:
        print(f"Error: Could not find {script_path}", file=sys.stderr)
        print("Make sure you're running from the repository root.", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
