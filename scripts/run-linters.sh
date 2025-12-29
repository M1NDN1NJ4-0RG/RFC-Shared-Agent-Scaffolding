#!/usr/bin/env bash
# DESCRIPTION:
#   Run all repository linters and formatters locally
#   Supports Python, Bash, and YAML files
#
# USAGE:
#   ./scripts/run-linters.sh [--fix]
#
# INPUTS:
#   --fix    Apply automatic fixes where possible (black formatting, shfmt)
#
# OUTPUTS:
#   Lint results printed to stdout/stderr
#   Exit code 0 if all checks pass, 1 if any fail
#
# EXAMPLES:
#   # Check code without modifying
#   ./scripts/run-linters.sh
#
#   # Auto-format and check
#   ./scripts/run-linters.sh --fix

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$REPO_ROOT"

FIX_MODE=false
if [[ "${1:-}" == "--fix" ]]; then
    FIX_MODE=true
fi

echo "🔍 Running repository linters and formatters..."
echo ""

EXIT_CODE=0

# ============================================================================
# Python Linting
# ============================================================================
if git ls-files '**/*.py' | grep -q .; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Python Linting"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Install Python dependencies if needed
    if ! command -v black &> /dev/null || ! command -v flake8 &> /dev/null || ! command -v pylint &> /dev/null; then
        echo "📦 Installing Python linting dependencies..."
        pip install --quiet black flake8 pylint
        echo ""
    fi

    # Black
    if [[ "$FIX_MODE" == "true" ]]; then
        echo "🎨 Running Black (auto-format mode)..."
        if ! black .; then
            EXIT_CODE=1
        fi
    else
        echo "🎨 Running Black (check mode)..."
        if ! black --check --diff .; then
            echo ""
            echo "❌ Black formatting check failed."
            echo "💡 Run './scripts/run-linters.sh --fix' to auto-format."
            EXIT_CODE=1
        fi
    fi
    echo ""

    # Flake8
    echo "🔎 Running Flake8..."
    if ! flake8 .; then
        echo ""
        echo "❌ Flake8 found issues."
        EXIT_CODE=1
    fi
    echo ""

    # Pylint
    echo "🔍 Running Pylint..."
    if ! git ls-files -z '**/*.py' | xargs -0 -r pylint; then
        echo ""
        echo "❌ Pylint found issues."
        EXIT_CODE=1
    fi
    echo ""

    # Python docstring validation
    echo "📝 Running Python docstring validation..."
    if ! python3 scripts/validate_docstrings.py; then
        echo ""
        echo "❌ Python docstring validation failed."
        EXIT_CODE=1
    fi
    echo ""
else
    echo "No Python files found. Skipping Python linting."
    echo ""
fi

# ============================================================================
# Bash Linting
# ============================================================================
if git ls-files '**/*.sh' | grep -q .; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Bash Linting"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # ShellCheck
    if ! command -v shellcheck &> /dev/null; then
        echo "📦 Installing shellcheck..."
        sudo apt-get update -qq
        sudo apt-get install -y -qq shellcheck
        echo ""
    fi

    echo "🐚 Running ShellCheck..."
    if ! git ls-files -z '**/*.sh' | xargs -0 -r shellcheck -S warning; then
        echo ""
        echo "❌ ShellCheck found issues."
        EXIT_CODE=1
    fi
    echo ""

    # shfmt
    if ! command -v shfmt &> /dev/null; then
        echo "📦 Installing shfmt..."
        go install mvdan.cc/sh/v3/cmd/shfmt@v3.12.0 2>/dev/null || {
            echo "⚠️  Could not install shfmt (Go not available). Skipping shfmt check."
        }
        echo ""
    fi

    if command -v shfmt &> /dev/null; then
        if [[ "$FIX_MODE" == "true" ]]; then
            echo "🎨 Running shfmt (auto-format mode)..."
            if ! git ls-files -z '**/*.sh' | xargs -0 -r shfmt -w -i 2 -ci; then
                EXIT_CODE=1
            fi
        else
            echo "🎨 Running shfmt (check mode)..."
            if ! git ls-files -z '**/*.sh' | xargs -0 -r shfmt -d -i 2 -ci; then
                echo ""
                echo "❌ shfmt formatting check failed."
                echo "💡 Run './scripts/run-linters.sh --fix' to auto-format."
                EXIT_CODE=1
            fi
        fi
        echo ""
    fi

    # Bash docstring validation
    echo "📝 Running Bash docstring validation..."
    bash_files_with_errors=0
    while IFS= read -r -d '' bash_file; do
        if ! python3 scripts/validate_docstrings.py --file "$bash_file" 2>&1 | grep -q "✅"; then
            ((bash_files_with_errors++)) || true
        fi
    done < <(git ls-files -z '**/*.sh')
    
    if [[ $bash_files_with_errors -gt 0 ]]; then
        echo ""
        echo "❌ Bash docstring validation failed for $bash_files_with_errors file(s)."
        EXIT_CODE=1
    else
        echo "✅ All Bash files conform to docstring contracts"
    fi
    echo ""
else
    echo "No Bash files found. Skipping Bash linting."
    echo ""
fi

# ============================================================================
# YAML Linting
# ============================================================================
if git ls-files '**/*.yml' '**/*.yaml' | grep -q .; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  YAML Linting"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # yamllint
    if ! command -v yamllint &> /dev/null; then
        echo "📦 Installing yamllint..."
        pip install --quiet yamllint
        echo ""
    fi

    echo "📄 Running yamllint..."
    if ! yamllint .; then
        echo ""
        echo "❌ yamllint found issues."
        EXIT_CODE=1
    fi
    echo ""
else
    echo "No YAML files found. Skipping YAML linting."
    echo ""
fi

# ============================================================================
# Summary
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [[ $EXIT_CODE -eq 0 ]]; then
    echo "✅ All linting checks passed!"
else
    echo "❌ Some linting checks failed. See output above for details."
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

exit $EXIT_CODE
