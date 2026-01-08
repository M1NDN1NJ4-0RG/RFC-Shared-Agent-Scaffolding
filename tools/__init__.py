"""Tools package for RFC-Shared-Agent-Scaffolding repository.

:Purpose:
    Provides repository maintenance and validation tools including linting,
    formatting, and docstring validation across multiple languages.

:Subpackages:
    repo_lint
        Linting and validation infrastructure

:Environment Variables:
    None - This is a package-level module with no environment dependencies.

:Examples:
    Import submodules from this package::

        from tools.repo_lint import LintRunner
        from tools.repo_lint.common import Violation

:Exit Codes:
    0 - Success (not applicable for package-level module)
    1 - Failure (not applicable for package-level module)

:Notes:
    This __init__.py is required for Python to recognize 'tools' as a package
    and enable imports like 'from tools.repo_lint import ...'.
"""
