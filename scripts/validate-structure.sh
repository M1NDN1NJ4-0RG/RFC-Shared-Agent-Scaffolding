#!/usr/bin/env bash
# validate-structure.sh
# Validates that all language bundles follow the canonical directory structure
# Exit code: 0 on success, 1 on failure

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXAMPLE_DIR="$REPO_ROOT/RFC-Shared-Agent-Scaffolding-Example/scripts"

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

errors=0

echo "=== Validating Example Directory Structure ==="
echo ""

# Define expected languages
languages=("bash" "perl" "python3" "powershell")

# Define expected directory structure
expected_dirs=("scripts" "tests")

# Define expected script files (without language-specific extensions)
expected_scripts=(
  "safe-run"
  "safe-check"
  "safe-archive"
  "preflight-automerge-ruleset"
)

for lang in "${languages[@]}"; do
  echo "Checking ${lang}..."
  bundle_dir="$EXAMPLE_DIR/$lang"
  
  # Check if bundle directory exists
  if [ ! -d "$bundle_dir" ]; then
    echo -e "  ${RED}✗${NC} Bundle directory does not exist: $bundle_dir"
    errors=$((errors + 1))
    continue
  fi
  
  # Check for required directories
  for dir in "${expected_dirs[@]}"; do
    dir_path="$bundle_dir/$dir"
    if [ ! -d "$dir_path" ]; then
      echo -e "  ${RED}✗${NC} Missing required directory: $dir"
      errors=$((errors + 1))
    else
      echo -e "  ${GREEN}✓${NC} Directory exists: $dir/"
    fi
  done
  
  # Check for scripts with language-appropriate extensions
  case "$lang" in
    bash)
      ext=".sh"
      ;;
    perl)
      ext=".pl"
      ;;
    python3)
      ext=".py"
      ;;
    powershell)
      ext=".ps1"
      ;;
  esac
  
  for script in "${expected_scripts[@]}"; do
    # All languages now use kebab-case (hyphens)
    script_name="$script"
    
    script_path="$bundle_dir/scripts/${script_name}${ext}"
    if [ ! -f "$script_path" ]; then
      echo -e "  ${RED}✗${NC} Missing script: scripts/${script_name}${ext}"
      errors=$((errors + 1))
    else
      echo -e "  ${GREEN}✓${NC} Script exists: scripts/${script_name}${ext}"
    fi
  done
  
  # Check for test runner
  case "$lang" in
    bash|perl)
      test_runner="run-tests.sh"
      ;;
    python3)
      test_runner="run-tests.sh"
      ;;
    powershell)
      test_runner="run-tests.ps1"
      ;;
  esac
  
  runner_path="$bundle_dir/$test_runner"
  if [ ! -f "$runner_path" ]; then
    echo -e "  ${YELLOW}⚠${NC} Info: Optional test runner not found (this is not an error): $test_runner"
  else
    echo -e "  ${GREEN}✓${NC} Optional test runner exists: $test_runner"
  fi
  
  # Check that there are NO nested language directories (the old structure)
  if [ -d "$bundle_dir/scripts/$lang" ]; then
    echo -e "  ${RED}✗${NC} ERROR: Old nested structure detected: scripts/$lang/ should not exist"
    errors=$((errors + 1))
  fi
  
  if [ -d "$bundle_dir/tests/$lang" ]; then
    echo -e "  ${RED}✗${NC} ERROR: Old nested structure detected: tests/$lang/ should not exist"
    errors=$((errors + 1))
  fi
  
  echo ""
done

echo "=== Validation Summary ==="
if [ $errors -eq 0 ]; then
  echo -e "${GREEN}✓ All language bundles follow the canonical structure${NC}"
  exit 0
else
  echo -e "${RED}✗ Found $errors structural issue(s)${NC}"
  exit 1
fi
