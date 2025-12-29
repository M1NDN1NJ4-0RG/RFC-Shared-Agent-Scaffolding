"""Per-language linting runners for repo_lint.

:Purpose:
    Each module in this package implements a Runner interface for a specific
    language, handling linting, formatting, and docstring validation.

:Modules:
    - python_runner.py: Python linting (Black, Ruff, Pylint, docstrings)
    - bash_runner.py: Bash linting (ShellCheck, shfmt, docstrings)
    - powershell_runner.py: PowerShell linting (PSScriptAnalyzer, docstrings)
    - perl_runner.py: Perl linting (Perl::Critic, docstrings)
    - yaml_runner.py: YAML linting (yamllint)
"""
