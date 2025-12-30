"""Auto-fix policy enforcement for repo_lint.

:Purpose:
    Implements deny-by-default auto-fix policy enforcement. Only explicitly
    allowed fix categories may run under `repo-lint fix`. This ensures that
    auto-fixes are auditable and controlled.

:Policy File:
    conformance/repo-lint/autofix-policy.json

:Policy Schema:
    {
        "version": "1.0",
        "policy": "deny_by_default",
        "allowed_categories": [
            {
                "category": "FORMAT.BLACK",
                "description": "...",
                "tool": "black",
                "safe": true,
                "mutating": true
            }
        ],
        "denied_categories": [...]
    }

:Environment Variables:
    REPO_ROOT: Repository root directory (auto-detected)

:Examples:
    Check if a fix category is allowed::

        policy = load_policy()
        if is_category_allowed(policy, "FORMAT.BLACK"):
            # Run Black formatter
            pass

    Get summary of allowed categories::

        policy = load_policy()
        summary = get_policy_summary(policy)
        print(summary)

:Exit Codes:
    Module provides utility functions and doesn't exit directly:
    - 0: Success (returned by calling code)
    - 1: Error (returned by calling code)
"""

import json
from pathlib import Path
from typing import Dict, List, Optional


def get_policy_path() -> Path:
    """Get path to auto-fix policy file.

    :returns:
        Path to conformance/repo-lint/autofix-policy.json
    """
    # Detect repo root (this file is in tools/repo_lint/policy.py)
    repo_root = Path(__file__).parent.parent.parent
    return repo_root / "conformance" / "repo-lint" / "autofix-policy.json"


def load_policy() -> Dict:
    """Load auto-fix policy from JSON file.

    :returns: Policy dictionary
    :raises FileNotFoundError: If policy file doesn't exist
    :raises json.JSONDecodeError: If policy file is invalid JSON
    """
    policy_path = get_policy_path()
    with open(policy_path, encoding="utf-8") as f:
        return json.load(f)


def is_category_allowed(policy: Dict, category: str) -> bool:
    """Check if an auto-fix category is allowed by policy.

    :param policy: Loaded policy dictionary
    :param category: Category to check (e.g., "FORMAT.BLACK", "LINT.RUFF.SAFE")
    :returns: True if category is allowed, False otherwise

    :Notes:
        Policy is deny-by-default. A category must be explicitly listed
        in "allowed_categories" to be permitted.
    """
    allowed = policy.get("allowed_categories", [])
    return any(cat.get("category") == category for cat in allowed)


def get_allowed_categories(policy: Dict) -> List[str]:
    """Get list of all allowed auto-fix categories.

    :param policy: Loaded policy dictionary
    :returns: List of allowed category names
    """
    allowed = policy.get("allowed_categories", [])
    return [cat.get("category") for cat in allowed if cat.get("category")]


def get_category_info(policy: Dict, category: str) -> Optional[Dict]:
    """Get full information about a category.

    :param policy: Loaded policy dictionary
    :param category: Category name
    :returns: Category info dictionary or None if not found
    """
    allowed = policy.get("allowed_categories", [])
    for cat in allowed:
        if cat.get("category") == category:
            return cat
    return None


def get_policy_summary(policy: Dict) -> str:
    """Generate human-readable policy summary.

    :param policy: Loaded policy dictionary
    :returns: Multi-line string summarizing policy

    :Examples:
        Auto-fix policy (deny-by-default):
        ✓ FORMAT.BLACK - Black Python code formatter
        ✓ FORMAT.SHFMT - shfmt shell script formatter
        ✓ LINT.RUFF.SAFE - Ruff safe auto-fixes only
    """
    lines = []
    lines.append(f"Auto-fix policy ({policy.get('policy', 'unknown')}):")

    allowed = policy.get("allowed_categories", [])
    if not allowed:
        lines.append("  (no categories allowed)")
    else:
        for cat in allowed:
            category = cat.get("category", "unknown")
            description = cat.get("description", "no description")
            lines.append(f"  ✓ {category} - {description}")

    return "\n".join(lines)


def validate_policy(policy: Dict) -> List[str]:
    """Validate policy structure and return any errors.

    :param policy: Policy dictionary to validate
    :returns: List of error messages (empty if valid)

    :Notes:
        Checks for:
        - Required top-level fields (version, policy, allowed_categories)
        - Valid policy mode (deny_by_default)
        - Category objects have required fields (category, tool, safe)
    """
    errors = []

    # Check required fields
    if "version" not in policy:
        errors.append("Missing required field: version")
    if "policy" not in policy:
        errors.append("Missing required field: policy")
    if "allowed_categories" not in policy:
        errors.append("Missing required field: allowed_categories")

    # Validate policy mode
    if policy.get("policy") != "deny_by_default":
        errors.append(f"Invalid policy mode: {policy.get('policy')} (must be 'deny_by_default')")

    # Validate allowed categories
    allowed = policy.get("allowed_categories", [])
    for i, cat in enumerate(allowed):
        if "category" not in cat:
            errors.append(f"allowed_categories[{i}]: Missing 'category' field")
        if "tool" not in cat:
            errors.append(f"allowed_categories[{i}]: Missing 'tool' field")
        if "safe" not in cat:
            errors.append(f"allowed_categories[{i}]: Missing 'safe' field")

    return errors
