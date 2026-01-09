"""repo_lint - Unified multi-language lint and docstring validation tool.

This package provides a single source of truth for repository linting and docstring
validation across all supported languages (Python, Bash, PowerShell, Perl, YAML).

:Purpose:
    Replaces ad-hoc bash linter scripts with a proper Python package + CLI that is:
    - Deterministic and strict in CI
    - Helpful locally (optional bootstrap + fix mode)
    - Modular per-language (one runner per language)
    - Aligned with repo contracts (naming, docstrings, exit codes, output format)

:Package Structure:
    - cli.py: Argument parsing and command dispatch
    - common.py: Shared types, errors, and utilities
    - reporting.py: Stable output formatting and exit codes
    - runners/: Per-language runner modules
    - install/: Bootstrap and installation helpers

:Environment Variables:
    None - all configuration via command-line arguments or pyproject.toml

:CLI Interface:
    Run in-place from repo root::

        python3 -m tools.repo_lint check
        python3 -m tools.repo_lint fix
        python3 -m tools.repo_lint install

:Examples:
    Check all files for lint violations::

        python3 -m tools.repo_lint check

    Apply automatic formatting fixes::

        python3 -m tools.repo_lint fix

    Install linting tools to repo-local venv::

        python3 -m tools.repo_lint install

:Exit Codes:
    - 0: All checks passed
    - 1: Linting/formatting violations found
    - 2: Missing tools (CI mode only)
    - 3: Internal error
"""

from __future__ import annotations

__version__: str = "0.1.0"
