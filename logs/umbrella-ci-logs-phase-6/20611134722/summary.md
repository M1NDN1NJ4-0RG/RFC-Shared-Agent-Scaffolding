# Repo Lint Summary

**Workflow Run:** https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/actions/runs/20611134722
**Timestamp:** 2025-12-31 03:21:22 UTC
**Branch:** 176/merge
**Commit:** 3173ed357fdbb57652b65ae09d00137421adf323

## Job Results

| Job | Status |
|-----|--------|
| Auto-Fix: Black | success |
| Detect Changed Files | success |
| Repo Lint: Python | failure |
| Repo Lint: Bash | failure |
| Repo Lint: PowerShell | failure |
| Repo Lint: Perl | failure |
| Repo Lint: YAML | failure |
| Repo Lint: Rust | failure |
| Vector Tests: Conformance | success |

## Python Linting Failures

```
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/tools/repo_lint/__main__.py", line 25, in <module>
    from tools.repo_lint.cli import main
  File "/home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/tools/repo_lint/cli.py", line 56, in <module>
    from rich.console import Console
ModuleNotFoundError: No module named 'rich'
```

## Bash Linting Failures

```
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/tools/repo_lint/__main__.py", line 25, in <module>
    from tools.repo_lint.cli import main
  File "/home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/tools/repo_lint/cli.py", line 55, in <module>
    import click
ModuleNotFoundError: No module named 'click'
```

## PowerShell Linting Failures

```
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/tools/repo_lint/__main__.py", line 25, in <module>
    from tools.repo_lint.cli import main
  File "/home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/tools/repo_lint/cli.py", line 55, in <module>
    import click
ModuleNotFoundError: No module named 'click'
```

## Perl Linting Failures

```
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/tools/repo_lint/__main__.py", line 25, in <module>
    from tools.repo_lint.cli import main
  File "/home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/tools/repo_lint/cli.py", line 55, in <module>
    import click
ModuleNotFoundError: No module named 'click'
```

## YAML Linting Failures

```
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/tools/repo_lint/__main__.py", line 25, in <module>
    from tools.repo_lint.cli import main
  File "/home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/tools/repo_lint/cli.py", line 55, in <module>
    import click
ModuleNotFoundError: No module named 'click'
```

## Rust Linting Failures

```
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/tools/repo_lint/__main__.py", line 25, in <module>
    from tools.repo_lint.cli import main
  File "/home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/tools/repo_lint/cli.py", line 55, in <module>
    import click
ModuleNotFoundError: No module named 'click'
```

