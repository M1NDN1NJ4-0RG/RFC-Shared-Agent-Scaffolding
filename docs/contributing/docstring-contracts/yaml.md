# YAML Docstring Contract

**Language:** YAML (`.yml`, `.yaml`)  
**Canonical style:** Top-of-file comment header using `#` prefix

## Purpose

YAML configuration files in this repository use a **top-of-file comment header** to document their purpose, usage, and behavior. This applies to GitHub Actions workflows, issue templates, and other YAML configurations.

## Required Semantic Sections

Every YAML file must include these sections (as comment headers):

1. **Workflow:** or **File:** - Name of the workflow or configuration file
2. **Purpose:** - What it does and what it does NOT do
3. **Triggers:** (for workflows) or **Usage:** (for config files) - How/when it runs
4. **Dependencies:** or **Inputs:** - What it expects (tools, actions, files, versions)
5. **Outputs:** or **Side effects:** - What it produces (artifacts, status checks, files)
6. **Notes:** - Maintainer notes, constraints, sharp edges

**For GitHub Actions Workflows specifically:**
- **Permissions:** - REQUIRED for workflow YAMLs (list GitHub Actions permissions)
- Use "Triggers:" for workflows (not "Usage:")

**For other YAML config files:**
- **Permissions:** - Optional
- Use "Usage:" for config files (not "Triggers:")

### Optional Sections

- **Environment:** - Environment configuration (matrix, jobs, runners, environment variables)
- **Platform:** - Platform requirements (e.g., "Runner: ubuntu-latest") - **Recommended**
- **References:** - Links to related docs or issues

## Formatting Rules

### Structure

```yaml
# Workflow: Workflow Name or File Purpose
#
# Purpose: Detailed description of what this workflow/file does and what it
# does NOT do. Be explicit about scope and limitations.
#
# Triggers:
# - Pull requests modifying specific paths
# - Pushes to main branch
# - Manual workflow dispatch
#
# Dependencies:
# - actions/checkout@v4
# - Rust toolchain 1.70+
# - Python 3.8+
# - Specific files: conformance/vectors.json
#
# Outputs:
# - Status check: workflow-name
# - Artifacts: test-results.xml (if failure)
# - Side effects: Creates comments on PR (if violations detected)
#
# Notes:
# - This workflow must pass before merge
# - Do not modify trigger paths without updating related workflows
# - Exit code 0 = success, non-zero = failure

name: Workflow Name

on:
  pull_request:
    paths:
      - 'path/**'
  workflow_dispatch:

# ... workflow content follows
```

### Key Rules

1. **Header first**: Comment header must be in the first 15 lines of file
2. **Section headers**: Capitalized word followed by colon (e.g., `Purpose:`)
3. **Indentation**: Use `#` for continuation lines, two spaces for sub-items with `-`
4. **Blank line separator**: One blank comment line (`#`) between sections is optional but recommended
5. **Explicit scope**: Always state what the file does NOT do if it might be ambiguous
6. **Consistent keywords**: Use the canonical section names (Workflow, Purpose, Triggers, Dependencies, Outputs, Notes)

## Section Details

### Workflow: / File:
- For GitHub Actions: `Workflow: <Name>`
- For other configs: `File: <filename.yml>` or descriptive name
- Should match the `name:` field in the YAML body (for workflows)

### Purpose:
- What problem this workflow/config solves
- What it validates, builds, tests, or deploys
- What it does NOT do (scope limitations)

### Triggers: (for GitHub Actions workflows ONLY)
- Use "Triggers:" for workflows, "Usage:" for other YAML files
- List trigger events clearly
- Mention path filters if used
- Note if manual dispatch is enabled
- Examples: `pull_request`, `push`, `workflow_dispatch`, `schedule`

### Usage: (for non-workflow YAML config files)
- How and when the config file is loaded/used
- What tool or system consumes it
- When it takes effect

### Dependencies:
- List GitHub Actions used (with versions)
- Required tools and their versions
- Required files or artifacts
- Environment requirements

### Outputs:
- Status checks created
- Artifacts uploaded
- Files created or modified
- PR comments or other side effects

### Permissions: (REQUIRED for GitHub Actions workflows)
- List all GitHub token permissions required
- Explain why each permission is needed
- Use least-privilege principle
- Example: `contents: read`, `pull-requests: write`

### Environment: (optional but recommended)
- Matrix configuration (OS, versions, etc.)
- Job-level environment variables
- Runner specifications
- Secrets or environment-specific settings
- Example:
  ```yaml
  # Environment:
  # - Matrix: ubuntu-latest, macos-latest, windows-latest
  # - Node.js versions: 16, 18, 20
  # - Environment variables: NODE_ENV=test
  ```

### Notes:
- Constraints or invariants
- Warnings about what not to change
- Related workflows or dependencies
- Exit code meanings (if applicable)

## Templates

### Minimal Workflow Template

```yaml
# Workflow: Workflow Name
#
# Purpose: Validates that <specific thing> conforms to <contract/rule>.
# Does NOT run full tests - those run separately in test-*.yml workflows.
#
# Triggers:
# - Pull requests modifying relevant paths
# - Pushes to main
# - Manual dispatch
#
# Dependencies:
# - actions/checkout@v4
# - Tool/action name and version
#
# Outputs:
# - Status check: workflow-name
# - Artifacts: none (or specify if any)
#
# Permissions:
# - contents: read (checkout code)
# - pull-requests: read (PR metadata)
#
# Notes:
# - Must pass before merge
# - Exit 0 = pass, non-zero = fail

name: Workflow Name

on:
  pull_request:
    paths:
      - 'path/**'
  push:
    branches:
      - main
  workflow_dispatch:

permissions:
  contents: read

jobs:
  validate:
    name: Validation Job
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
      
      - name: Run validation
        run: |
          echo "Validation logic here"
```

### Full Workflow Template

```yaml
# Workflow: Comprehensive Validation Gate
#
# Purpose: Validates multiple aspects of repository health including:
# - Code style conformance
# - Documentation completeness
# - Artifact integrity
#
# This workflow does NOT:
# - Run full integration tests (see test-integration.yml)
# - Build release artifacts (see build-release.yml)
# - Deploy to production (see deploy.yml)
#
# Triggers:
# - Pull requests modifying:
#   - Source code (src/**)
#   - Documentation (docs/**)
#   - This workflow file
# - Pushes to main branch (same path filters)
# - Manual workflow dispatch (for ad-hoc validation)
#
# Dependencies:
# - actions/checkout@v4 (fetch repository)
# - actions/setup-python@v4 (Python 3.8+ for validators)
# - Custom validation script: scripts/validate.py
# - Required files: conformance/vectors.json, docs/contract.md
#
# Outputs:
# - Status check: "Comprehensive Validation Gate" (required for merge)
# - Artifacts: validation-report.txt (on failure, 1-day retention)
# - Side effects: PR comment with violation details (if failures detected)
#
# Permissions:
# - contents: read (checkout repository)
# - pull-requests: write (comment on PRs with violation details)
#
# Environment:
# - Runner: ubuntu-latest (sufficient for validation tasks)
# - Python: 3.8+ (for validation scripts)
# - Matrix: None (single configuration)
#
# Notes:
# - This is a required status check - PRs cannot merge if this fails
# - Validation failures print actionable error messages with file/line context
# - Exit code 0 = all validations pass, non-zero = violations detected
# - Do not modify trigger paths without coordinating with related workflows
# - See docs/validation-contract.md for validation rules
#
# References:
# - docs/validation-contract.md
# - rfc-shared-agent-scaffolding-v0.1.0.md

name: Comprehensive Validation Gate

on:
  pull_request:
    paths:
      - 'src/**'
      - 'docs/**'
      - '.github/workflows/validation-gate.yml'
  push:
    branches:
      - main
    paths:
      - 'src/**'
      - 'docs/**'
  workflow_dispatch:

permissions:
  contents: read
  pull-requests: write  # For commenting on PRs

jobs:
  validate:
    name: Run All Validations
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.8'
      
      - name: Run validation script
        run: |
          python3 scripts/validate.py
      
      - name: Upload validation report on failure
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: validation-report
          path: validation-report.txt
          retention-days: 1
```

### Minimal Non-Workflow YAML Template

```yaml
# File: configuration-name.yml
#
# Purpose: Configuration for <tool/system>. Defines <what it configures>.
# Does NOT: <what it doesn't configure>
#
# Usage:
# - Loaded by <tool/system> at <when>
# - Modified by <who/what process>
#
# Dependencies:
# - Tool version: <version requirement>
# - Required files: <files this config references>
#
# Outputs:
# - Affects: <what behavior this changes>
# - Side effects: <any files created or modified>
#
# Notes:
# - Do not modify <field> without updating <related file>
# - Values must conform to <schema/standard>

# Configuration content follows
setting1: value1
setting2: value2
```

## Examples (Existing Files)

### Example 1: Full Workflow
**File:** `.github/workflows/conformance.yml`

This file demonstrates:
- Complete header with all required sections
- Clear purpose statement with negation ("does NOT run...")
- Detailed trigger conditions
- Dependencies listing actions and file requirements
- Outputs including status checks
- Notes with constraints

### Example 2: Drift Detection Workflow
**File:** `.github/workflows/drift-detection.yml`

This file demonstrates:
- Purpose explaining what drift means
- Platform notes (Linux runner)
- Clear separation of concerns (vs. other workflows)
- Notes about related workflows

### Example 3: Test Workflow
**File:** `.github/workflows/test-bash.yml`

This demonstrates:
- Language-specific workflow documentation
- Dependencies on language runtimes
- Platform requirements

## Validation

The validator checks for:
- Presence of comment header in first 15 lines
- Presence of section keywords: `Workflow:` or `File:`, `Purpose:`, `Triggers:` or `Usage:`, `Dependencies:` or `Inputs:`, `Outputs:` or `Side effects:`, `Notes:` or `Note:`
- At least one trigger listed (for GitHub Actions workflows)

The validator does NOT check:
- YAML syntax validity (use `yamllint` for that)
- GitHub Actions schema compliance
- Content quality or accuracy
- Grammar or spelling

## Common Mistakes

❌ **Wrong:** No header documentation
```yaml
name: My Workflow

on:
  pull_request:
```

✅ **Correct:** Header comes first
```yaml
# Workflow: My Workflow
#
# Purpose: Does something specific.
#
# Triggers:
# - Pull requests
#
# Dependencies:
# - actions/checkout@v4
#
# Outputs:
# - Status check: my-workflow
#
# Notes:
# - Required for merge

name: My Workflow

on:
  pull_request:
```

❌ **Wrong:** Vague purpose
```yaml
# Workflow: Tests
#
# Purpose: Runs tests
```

✅ **Correct:** Specific purpose with scope
```yaml
# Workflow: Bash Unit Tests
#
# Purpose: Runs unit tests for Bash wrapper scripts in
# wrappers/bash/tests/.
# Does NOT run integration tests or other language tests.
```

❌ **Wrong:** Missing Dependencies section
```yaml
# Workflow: Build
#
# Purpose: Builds the project
#
# Triggers:
# - Push to main
```

✅ **Correct:** Document dependencies
```yaml
# Workflow: Build
#
# Purpose: Builds the project
#
# Triggers:
# - Push to main
#
# Dependencies:
# - actions/checkout@v4
# - actions/setup-rust@v1
# - Rust 1.70+
#
# Outputs:
# - Artifacts: dist/binary
```

❌ **Wrong:** No Notes section
```yaml
# Workflow: Deploy
#
# Purpose: Deploys to production
# ...other sections...
```

✅ **Correct:** Include Notes for maintainers
```yaml
# Workflow: Deploy
#
# Purpose: Deploys to production
# ...other sections...
#
# Notes:
# - Only runs on main branch
# - Requires manual approval
# - Do not modify without consulting team
```

## GitHub Actions Specifics

### Trigger Documentation
Be explicit about trigger conditions:

```yaml
# Triggers:
# - Pull requests modifying:
#   - Source code (src/**)
#   - Tests (tests/**)
#   - This workflow file
# - Pushes to main (same paths)
# - Manual dispatch (workflow_dispatch)
# - Scheduled: Daily at 00:00 UTC (cron)

on:
  pull_request:
    paths:
      - 'src/**'
      - 'tests/**'
      - '.github/workflows/this-workflow.yml'
  push:
    branches:
      - main
    paths:
      - 'src/**'
      - 'tests/**'
  workflow_dispatch:
  schedule:
    - cron: '0 0 * * *'
```

### Permission Documentation
Document permissions when not default:

```yaml
# Workflow: PR Commenter
#
# ...
#
# Permissions:
# - contents: read (checkout code)
# - pull-requests: write (add PR comments)
# - issues: write (update issue labels)

permissions:
  contents: read
  pull-requests: write
  issues: write
```

## References

- [README.md](./README.md) - Overview of docstring contracts
- [exit-codes-contract.md](./exit-codes-contract.md) - Canonical exit code meanings
- [GitHub Actions Syntax](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
- [YAML Specification](https://yaml.org/spec/)
- [Conformance Contract](../../usage/conformance-contract.md) - Behavior contract
