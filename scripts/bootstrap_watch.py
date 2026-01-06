#!/usr/bin/env python3
"""Bootstrap Progress Watcher.

Runs the bootstrap script and filters output to show:
- All progress lines (steps with [N/M] format)
- All output from the last progress step onward

This provides a condensed view focusing on the step-by-step progress
and any final output/errors.
"""

import re
import subprocess
import sys


def main():
    """Run bootstrap script and filter output to show progress steps.

    Returns:
        int: Exit code from the bootstrap script.
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
