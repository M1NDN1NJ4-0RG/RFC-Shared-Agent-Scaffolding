"""PEP 526 type annotation checkers for repo_lint.

:Purpose:
    Provides AST-based checkers for enforcing Python type annotation requirements
    as defined in PEP 526 (variable annotations) and PEP 484 (type hints).

:Modules:
    - pep526_checker: AST visitor for detecting missing variable annotations
    - pep526_config: Configuration handling for PEP 526 enforcement

:Examples:
    Basic usage::

        from tools.repo_lint.checkers.pep526_checker import PEP526Checker

        config = {'module_level': True, 'class_attributes': True}
        checker = PEP526Checker(config)
        violations = checker.check_file(filepath)
"""

from tools.repo_lint.checkers.pep526_checker import PEP526Checker

__all__ = ["PEP526Checker"]
