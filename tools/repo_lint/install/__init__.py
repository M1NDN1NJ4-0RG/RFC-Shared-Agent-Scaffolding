"""Installation and bootstrap helpers for repo_lint.

:Purpose:
    Provides utilities for installing and bootstrapping required linting tools
    in a safe, deterministic manner.

:Modules:
    - install_helpers.py: Tool installation functions
    - version_pins.py: Pinned versions for deterministic installs

:Environment Variables:
    None

:Examples:
    This module is imported by repo_lint.install.install_helpers

:Exit Codes:
    Package initialization - functions return tuples with success status:
    - 0: Success (when functions return True)
    - 1: Error (when functions return False)
"""

from __future__ import annotations
