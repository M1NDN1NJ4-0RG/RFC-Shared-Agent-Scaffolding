"""Entry point for python3 -m tools.repo_lint.

:Purpose:
    Enables running repo_lint as a Python module using the -m flag.

:Environment Variables:
    None

:Examples:
    Run lint checks::

        python3 -m tools.repo_lint check

    Apply formatting fixes::

        python3 -m tools.repo_lint fix

:Exit Codes:
    - 0: Success
    - 1: Lint violations found
    - 2: Missing tools (CI mode)
    - 3: Internal error
"""

from tools.repo_lint.cli import main

if __name__ == "__main__":
    main()
