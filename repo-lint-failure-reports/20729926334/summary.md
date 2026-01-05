# Repo Lint Summary

**Workflow Run:** https://github.com/M1NDN1NJ4-0RG/RFC-Shared-Agent-Scaffolding/actions/runs/20729926334
**Timestamp:** 2026-01-05 21:38:43 UTC
**Branch:** 229/merge
**Commit:** e24aca6a87faa7dc442bbd0d5987b5fa64c007f7

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
  File "/home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/tools/repo_lint/__main__.py", line 27, in <module>
    from tools.repo_lint.cli import main
  File "/home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/tools/repo_lint/cli.py", line 1762
    elif shell == "fish":
    ^^^^
SyntaxError: invalid syntax
```

## Bash Linting Failures

```
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/tools/repo_lint/__main__.py", line 27, in <module>
    from tools.repo_lint.cli import main
  File "/home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/tools/repo_lint/cli.py", line 1762
    elif shell == "fish":
    ^^^^
SyntaxError: invalid syntax
```

## PowerShell Linting Failures

```
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/tools/repo_lint/__main__.py", line 27, in <module>
    from tools.repo_lint.cli import main
  File "/home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/tools/repo_lint/cli.py", line 1762
    elif shell == "fish":
    ^^^^
SyntaxError: invalid syntax
```

## Perl Linting Failures

```
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/tools/repo_lint/__main__.py", line 27, in <module>
    from tools.repo_lint.cli import main
  File "/home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/tools/repo_lint/cli.py", line 1762
    elif shell == "fish":
    ^^^^
SyntaxError: invalid syntax
```

## YAML Linting Failures

```
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/tools/repo_lint/__main__.py", line 27, in <module>
    from tools.repo_lint.cli import main
  File "/home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/tools/repo_lint/cli.py", line 1762
    elif shell == "fish":
    ^^^^
SyntaxError: invalid syntax
```

## Rust Linting Failures

```
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/tools/repo_lint/__main__.py", line 27, in <module>
    from tools.repo_lint.cli import main
  File "/home/runner/work/RFC-Shared-Agent-Scaffolding/RFC-Shared-Agent-Scaffolding/tools/repo_lint/cli.py", line 1762
    elif shell == "fish":
    ^^^^
SyntaxError: invalid syntax
```

