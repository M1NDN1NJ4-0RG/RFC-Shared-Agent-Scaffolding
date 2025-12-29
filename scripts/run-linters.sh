#!/usr/bin/env bash
# DESCRIPTION:
#   Run all repository linters and formatters locally
#   Supports Python, Bash, PowerShell, Perl, and YAML files
#   Automatically installs missing linters
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
# Dependency Installation Helper Functions
# ============================================================================

# Check if a command exists
have_command() {
  command -v "$1" &>/dev/null
}

# Install Python tools
install_python_tools() {
  local missing_tools=()

  if ! have_command black; then
    missing_tools+=("black")
  fi
  if ! have_command flake8; then
    missing_tools+=("flake8")
  fi
  if ! have_command pylint; then
    missing_tools+=("pylint")
  fi

  if [[ ${#missing_tools[@]} -gt 0 ]]; then
    echo "📦 Installing Python tools: ${missing_tools[*]}..."
    pip install --quiet "${missing_tools[@]}"
    echo ""
  fi
}

# Install shellcheck
install_shellcheck() {
  if ! have_command shellcheck; then
    echo "📦 Installing shellcheck..."
    if have_command apt-get; then
      sudo apt-get update -qq
      sudo apt-get install -y -qq shellcheck
    elif have_command brew; then
      brew install shellcheck
    else
      echo "⚠️  Cannot install shellcheck automatically. Please install manually."
      return 1
    fi
    echo ""
  fi
  return 0
}

# Install shfmt
install_shfmt() {
  if ! have_command shfmt; then
    echo "📦 Installing shfmt..."
    if have_command go; then
      go install mvdan.cc/sh/v3/cmd/shfmt@v3.12.0
      # Add GOPATH/bin to PATH if not already there
      if [[ ":$PATH:" != *":$HOME/go/bin:"* ]]; then
        export PATH="$HOME/go/bin:$PATH"
      fi
    else
      echo "⚠️  Go not available. Skipping shfmt installation."
      return 1
    fi
    echo ""
  fi
  return 0
}

# Install PowerShell and PSScriptAnalyzer
install_powershell_tools() {
  if ! have_command pwsh; then
    echo "📦 Installing PowerShell..."
    if have_command apt-get; then
      # Install PowerShell on Ubuntu/Debian
      wget -q "https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/packages-microsoft-prod.deb" -O /tmp/packages-microsoft-prod.deb
      sudo dpkg -i /tmp/packages-microsoft-prod.deb
      rm /tmp/packages-microsoft-prod.deb
      sudo apt-get update -qq
      sudo apt-get install -y -qq powershell
    elif have_command brew; then
      brew install --cask powershell
    else
      echo "⚠️  Cannot install PowerShell automatically. Please install manually."
      return 1
    fi
    echo ""
  fi

  # Install PSScriptAnalyzer module
  if have_command pwsh; then
    echo "📦 Installing PSScriptAnalyzer..."
    pwsh -Command "if (-not (Get-Module -ListAvailable -Name PSScriptAnalyzer)) { Install-Module -Name PSScriptAnalyzer -Force -Scope CurrentUser }" 2>/dev/null || true
    echo ""
  fi
  return 0
}

# Install Perl::Critic
install_perl_critic() {
  if ! have_command perlcritic; then
    echo "📦 Installing Perl::Critic..."
    if have_command cpanm; then
      sudo cpanm --notest --quiet Perl::Critic
    elif have_command apt-get; then
      sudo apt-get update -qq
      sudo apt-get install -y -qq cpanminus
      sudo cpanm --notest --quiet Perl::Critic
    elif have_command brew; then
      cpan -T Perl::Critic
    else
      echo "⚠️  Cannot install Perl::Critic automatically. Please install manually."
      return 1
    fi
    echo ""
  fi
  return 0
}

# Install yamllint
install_yamllint() {
  if ! have_command yamllint; then
    echo "📦 Installing yamllint..."
    pip install --quiet yamllint
    echo ""
  fi
}

# ============================================================================
# Python Linting
# ============================================================================
if git ls-files '**/*.py' | grep -q .; then
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  Python Linting"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  # Install Python dependencies if needed
  install_python_tools

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
  if install_shellcheck; then
    echo "🐚 Running ShellCheck..."
    if ! git ls-files -z '**/*.sh' | xargs -0 -r shellcheck -S warning; then
      echo ""
      echo "❌ ShellCheck found issues."
      EXIT_CODE=1
    fi
    echo ""
  fi

  # shfmt
  if install_shfmt && have_command shfmt; then
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
# PowerShell Linting
# ============================================================================
if git ls-files '**/*.ps1' | grep -q .; then
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  PowerShell Linting"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  # Install PowerShell tools
  if install_powershell_tools && have_command pwsh; then
    echo "⚡ Running PSScriptAnalyzer..."
    ps_files_with_errors=0
    while IFS= read -r ps_file; do
      if ! pwsh -Command "Invoke-ScriptAnalyzer -Path '$ps_file' -Severity Error -EnableExit" 2>&1; then
        ((ps_files_with_errors++)) || true
      fi
    done < <(git ls-files '**/*.ps1')

    if [[ $ps_files_with_errors -gt 0 ]]; then
      echo ""
      echo "❌ PSScriptAnalyzer found issues in $ps_files_with_errors file(s)."
      EXIT_CODE=1
    else
      echo "✅ All PowerShell files passed PSScriptAnalyzer"
    fi
    echo ""

    # PowerShell docstring validation
    echo "📝 Running PowerShell docstring validation..."
    ps_docstring_errors=0
    while IFS= read -r -d '' ps_file; do
      if ! python3 scripts/validate_docstrings.py --file "$ps_file" 2>&1 | grep -q "✅"; then
        ((ps_docstring_errors++)) || true
      fi
    done < <(git ls-files -z '**/*.ps1')

    if [[ $ps_docstring_errors -gt 0 ]]; then
      echo ""
      echo "❌ PowerShell docstring validation failed for $ps_docstring_errors file(s)."
      EXIT_CODE=1
    else
      echo "✅ All PowerShell files conform to docstring contracts"
    fi
    echo ""
  fi
else
  echo "No PowerShell files found. Skipping PowerShell linting."
  echo ""
fi

# ============================================================================
# Perl Linting
# ============================================================================
if git ls-files '**/*.pl' '**/*.pm' | grep -q .; then
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  Perl Linting"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  # Install Perl::Critic
  if install_perl_critic && have_command perlcritic; then
    echo "🔍 Running Perl::Critic..."
    if ! git ls-files -z '**/*.pl' '**/*.pm' | xargs -0 -r perlcritic --severity 5; then
      echo ""
      echo "❌ Perl::Critic found issues."
      EXIT_CODE=1
    else
      echo "✅ All Perl files passed Perl::Critic"
    fi
    echo ""

    # Perl docstring validation
    echo "📝 Running Perl docstring validation..."
    perl_docstring_errors=0
    while IFS= read -r -d '' perl_file; do
      if ! python3 scripts/validate_docstrings.py --file "$perl_file" 2>&1 | grep -q "✅"; then
        ((perl_docstring_errors++)) || true
      fi
    done < <(git ls-files -z '**/*.pl' '**/*.pm')

    if [[ $perl_docstring_errors -gt 0 ]]; then
      echo ""
      echo "❌ Perl docstring validation failed for $perl_docstring_errors file(s)."
      EXIT_CODE=1
    else
      echo "✅ All Perl files conform to docstring contracts"
    fi
    echo ""
  fi
else
  echo "No Perl files found. Skipping Perl linting."
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
  install_yamllint

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
