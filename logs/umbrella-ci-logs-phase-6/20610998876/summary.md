# Repo Lint Summary

**Workflow Run:** https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/actions/runs/20610998876
**Timestamp:** 2025-12-31 03:07:09 UTC
**Branch:** 176/merge
**Commit:** f8ad0019d1aba58968525e713b384b3043db854d

## Job Results

| Job | Status |
|-----|--------|
| Auto-Fix: Black | success |
| Detect Changed Files | success |
| Repo Lint: Python | failure |
| Repo Lint: Bash | failure |
| Repo Lint: PowerShell | failure |
| Repo Lint: Perl | failure |
| Repo Lint: YAML | success |
| Repo Lint: Rust | failure |
| Vector Tests: Conformance | success |

## Python Linting Failures

```
🔍 Running repository linters and formatters...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Python Linting
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Linting Results
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ validate_docstrings: FAILED (2 violation(s))
   .: [validate_docstrings] ❌ Validation FAILED: 1 violation(s) in 1 file(s)
   .: [validate_docstrings] ❌ /home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/tools/repo_lint/config_validator.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ Found 2 violation(s) across 1 tool(s)
```

## Bash Linting Failures

```
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/tools/repo_lint/__main__.py", line 25, in <module>
    from tools.repo_lint.cli import main
  File "/home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/tools/repo_lint/cli.py", line 57, in <module>
    from tools.repo_lint.runners.naming_runner import NamingRunner
  File "/home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/tools/repo_lint/runners/naming_runner.py", line 32, in <module>
    from tools.repo_lint.config_validator import ConfigValidationError, load_validated_config
  File "/home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/tools/repo_lint/config_validator.py", line 30, in <module>
    import yaml
ModuleNotFoundError: No module named 'yaml'
```

## PowerShell Linting Failures

```
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/tools/repo_lint/__main__.py", line 25, in <module>
    from tools.repo_lint.cli import main
  File "/home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/tools/repo_lint/cli.py", line 57, in <module>
    from tools.repo_lint.runners.naming_runner import NamingRunner
  File "/home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/tools/repo_lint/runners/naming_runner.py", line 32, in <module>
    from tools.repo_lint.config_validator import ConfigValidationError, load_validated_config
  File "/home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/tools/repo_lint/config_validator.py", line 30, in <module>
    import yaml
ModuleNotFoundError: No module named 'yaml'
```

## Perl Linting Failures

```
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/tools/repo_lint/__main__.py", line 25, in <module>
    from tools.repo_lint.cli import main
  File "/home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/tools/repo_lint/cli.py", line 57, in <module>
    from tools.repo_lint.runners.naming_runner import NamingRunner
  File "/home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/tools/repo_lint/runners/naming_runner.py", line 32, in <module>
    from tools.repo_lint.config_validator import ConfigValidationError, load_validated_config
  File "/home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/tools/repo_lint/config_validator.py", line 30, in <module>
    import yaml
ModuleNotFoundError: No module named 'yaml'
```

## Rust Linting Failures

```
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/tools/repo_lint/__main__.py", line 25, in <module>
    from tools.repo_lint.cli import main
  File "/home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/tools/repo_lint/cli.py", line 57, in <module>
    from tools.repo_lint.runners.naming_runner import NamingRunner
  File "/home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/tools/repo_lint/runners/naming_runner.py", line 32, in <module>
    from tools.repo_lint.config_validator import ConfigValidationError, load_validated_config
  File "/home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/tools/repo_lint/config_validator.py", line 30, in <module>
    import yaml
ModuleNotFoundError: No module named 'yaml'
```

