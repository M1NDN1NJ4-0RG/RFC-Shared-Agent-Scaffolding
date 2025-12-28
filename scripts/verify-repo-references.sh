#!/usr/bin/env bash
#
# verify-repo-references.sh - Verify that obsolete repository paths have been removed
#
# DESCRIPTION:
#   Searches the repository for references to old paths that should no longer
#   exist after the repository restructure. This helps ensure that documentation
#   and configuration files have been updated when directories are renamed or
#   relocated.
#
#   Currently checks for:
#   - documents/ (replaced by docs/)
#   - RFC-Shared-Agent-Scaffolding-Example/ (replaced by wrappers/)
#
#   The script excludes the .git directory and binary files from searches.
#   It reports line numbers and context for any found references.
#
# USAGE:
#   verify-repo-references.sh [--strict]
#
# INPUTS:
#   Arguments:
#     --strict    (Optional) Exit with non-zero code if ANY obsolete references
#                 are found. Without this flag, the script always exits 0 and
#                 only reports findings.
#
#   Environment Variables:
#     None
#
# OUTPUTS:
#   Exit Codes:
#     0    No obsolete references found, or non-strict mode with findings
#     1    Obsolete references found in strict mode
#     2    Script execution error
#
#   Stdout/Stderr:
#     Success: Summary of checks performed and results
#     Failure: Detailed list of files and line numbers with obsolete references
#
#   Side Effects:
#     None - read-only operation
#
# EXAMPLES:
#   # Run in reporting mode (always exits 0)
#   ./scripts/verify-repo-references.sh
#
#   # Run in strict mode (exits non-zero if issues found)
#   ./scripts/verify-repo-references.sh --strict
#
# NOTES:
#   - Runs from repository root (automatically changes directory)
#   - Uses git grep when available for better performance
#   - Only searches text files (md, yml, yaml, sh, py, pl, ps1, rs, toml)
#   - After M1: 'documents/' should be eliminated
#   - After M2: 'RFC-Shared-Agent-Scaffolding-Example' should be eliminated

set -euo pipefail

# Script directory and repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Parse arguments
STRICT_MODE=false
if [[ "${1:-}" == "--strict" ]]; then
    STRICT_MODE=true
fi

# Change to repo root
cd "${REPO_ROOT}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track if we found any issues
FOUND_ISSUES=false

echo "============================================"
echo "Repository Reference Verification"
echo "============================================"
echo ""

# Function to search for a pattern
search_pattern() {
    local pattern="$1"
    local description="$2"
    
    echo "Searching for: ${description}"
    echo "Pattern: ${pattern}"
    echo ""
    
    # Search for the pattern, excluding .git and binary files
    # Use git grep if available (respects .gitignore), fallback to regular grep
    local results=""
    if command -v git &> /dev/null && git rev-parse --git-dir &> /dev/null; then
        results=$(git grep -n "${pattern}" -- '*.md' '*.yml' '*.yaml' '*.sh' '*.py' '*.pl' '*.ps1' '*.rs' '*.toml' 2>/dev/null || true)
    else
        results=$(grep -rn --include='*.md' --include='*.yml' --include='*.yaml' --include='*.sh' --include='*.py' --include='*.pl' --include='*.ps1' --include='*.rs' --include='*.toml' "${pattern}" . 2>/dev/null || true)
    fi
    
    if [[ -n "${results}" ]]; then
        echo -e "${RED}✗ Found references:${NC}"
        echo "${results}" | head -20
        if [[ $(echo "${results}" | wc -l) -gt 20 ]]; then
            echo "... (showing first 20 of $(echo "${results}" | wc -l) matches)"
        fi
        echo ""
        FOUND_ISSUES=true
        return 1
    else
        echo -e "${GREEN}✓ No references found${NC}"
        echo ""
        return 0
    fi
}

# Search for obsolete patterns
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Checking for obsolete directory references"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Pattern 1: documents/ directory (after M1)
# This check is informational until M1 is complete
search_pattern "documents/" "Old 'documents/' directory references" || true

# Pattern 2: RFC-Shared-Agent-Scaffolding-Example/ directory (after M2)
# This check is informational until M2 is complete
search_pattern "RFC-Shared-Agent-Scaffolding-Example" "Old 'RFC-Shared-Agent-Scaffolding-Example/' directory references" || true

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [[ "${FOUND_ISSUES}" == "true" ]]; then
    echo -e "${YELLOW}⚠ Obsolete references found${NC}"
    echo ""
    echo "This is expected during the restructure process."
    echo "After M1: 'documents/' should be eliminated"
    echo "After M2: 'RFC-Shared-Agent-Scaffolding-Example' should be eliminated"
    
    if [[ "${STRICT_MODE}" == "true" ]]; then
        echo ""
        echo -e "${RED}Strict mode enabled: exiting with error${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ All checks passed - no obsolete references found${NC}"
fi

exit 0
