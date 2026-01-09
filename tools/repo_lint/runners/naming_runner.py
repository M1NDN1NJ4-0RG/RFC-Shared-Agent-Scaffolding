"""Naming convention enforcement runner for repo_lint.

:Purpose:
    Validates file naming conventions across all languages.
    Loads rules from external YAML config and reports violations.

:Classes:
    - NamingRunner: Check-only naming validation (no auto-renames)

:Environment Variables:
    None

:Examples:
    Run naming checks::

        from tools.repo_lint.runners.naming_runner import NamingRunner
        runner = NamingRunner()
        results = runner.check(verbose=True)

:Exit Codes:
    - 0: All naming conventions followed
    - 1: Naming violations found
    - 2: Missing tools (config file not found)
    - 3: Internal error (config validation failure)
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List

from tools.repo_lint.common import LintResult, MissingToolError, Violation
from tools.repo_lint.config_validator import ConfigValidationError, load_validated_config
from tools.repo_lint.runners.base import Runner


class NamingRunner(Runner):
    """Runner for file naming convention checks.

    :Purpose:
        Validates that file names follow language-specific naming conventions
        defined in conformance/repo-lint/repo-lint-naming-rules.yaml.
        Check-only mode - does not auto-rename files.
    """

    def __init__(self) -> None:
        """Initialize naming runner.

        :raises MissingToolError: If naming rules config file not found
        :raises ConfigValidationError: If config validation fails
        """
        super().__init__()
        self.config_file = self.repo_root / "conformance" / "repo-lint" / "repo-lint-naming-rules.yaml"

        # Load and validate config
        try:
            self.config = load_validated_config(str(self.config_file), "repo-lint-naming-rules")
        except FileNotFoundError as e:
            raise MissingToolError("naming-rules-config", f"Config not found: {self.config_file}") from e
        except ConfigValidationError as e:
            raise MissingToolError("naming-rules-config", f"Config validation failed: {e}") from e

        self.languages = self.config.get("languages", {})
        self.exclusions = self.config.get("exclusions", [])

    def has_files(self) -> bool:
        """Check if there are files to validate.

        :returns: Always True (naming checks run on all repo files)
        """
        return True

    def check_tools(self) -> List[str]:
        """Check if required tools are available.

        :returns: Empty list (naming validation requires no external tools)
        """
        return []

    def check(self, verbose: bool = False) -> List[LintResult]:
        """Check file naming conventions.

        :Purpose:
            Scans repository files and validates naming against configured rules.

        :param verbose: If True, print detailed output
        :returns: List of LintResult objects (violations only, passes not reported)
        """
        results = []
        repo_root = self.repo_root

        if verbose:
            print(f"\n{'=' * 80}")
            print("Naming Convention Validation")
            print(f"{'=' * 80}")
            print(f"Config: {self.config_file}")
            print(f"Languages: {', '.join(self.languages.keys())}")

        # Scan repository for files
        all_files = self._get_all_repo_files(repo_root)

        # Filter out exclusions
        files_to_check = self._filter_exclusions(all_files, repo_root)

        if verbose:
            print(f"Files to check: {len(files_to_check)}")
            print()

        # Check each file against applicable language rules
        for file_path in files_to_check:
            result = self._check_file_naming(file_path, repo_root, verbose=verbose)
            if result:
                results.append(result)

        if verbose:
            print(f"\n{'=' * 80}")
            if results:
                print(f"Found {len(results)} naming violations")
            else:
                print("✓ All files follow naming conventions")
            print(f"{'=' * 80}\n")

        return results

    def fix(self, policy: dict | None = None, verbose: bool = False) -> List[LintResult]:
        """Naming enforcement is check-only - no auto-rename support.

        :Purpose:
            Naming violations cannot be auto-fixed to avoid breaking git history
            and references. This method returns the same results as check().

        :param verbose: If True, print detailed output
        :returns: List of LintResult objects (same as check)
        """
        if verbose:
            print("⚠️  Naming enforcement is check-only (no auto-rename)")
            print("    Please rename files manually to fix violations")

        return self.check(verbose=verbose)

    def _get_all_repo_files(self, repo_root: Path) -> List[Path]:
        """Get all files in repository.

        :param repo_root: Repository root directory
        :returns: List of file paths
        """
        files = []
        for path in repo_root.rglob("*"):
            if path.is_file():
                files.append(path)
        return files

    def _filter_exclusions(self, files: List[Path], repo_root: Path) -> List[Path]:
        """Filter out excluded files/directories.

        :param files: List of file paths
        :param repo_root: Repository root directory
        :returns: Filtered list of file paths
        """
        filtered = []
        for file_path in files:
            relative_path = str(file_path.relative_to(repo_root))
            excluded = False

            for exclusion in self.exclusions:
                # Handle directory exclusions (trailing /)
                if exclusion.endswith("/"):
                    if relative_path.startswith(exclusion) or f"/{exclusion}" in f"/{relative_path}":
                        excluded = True
                        break
                # Handle pattern exclusions (*.ext)
                elif exclusion.startswith("*"):
                    pattern = exclusion.replace("*", ".*")
                    if re.search(pattern, relative_path):
                        excluded = True
                        break
                # Handle exact path exclusions
                elif relative_path == exclusion or relative_path.startswith(f"{exclusion}/"):
                    excluded = True
                    break

            if not excluded:
                filtered.append(file_path)

        return filtered

    def _check_file_naming(self, file_path: Path, repo_root: Path, verbose: bool = False) -> LintResult | None:
        """Check a single file against naming rules.

        :param file_path: Path to file
        :param repo_root: Repository root directory
        :param verbose: If True, print detailed output
        :returns: LintResult if violation found, None otherwise
        """
        filename = file_path.name
        extension = file_path.suffix

        # Determine which language rules apply based on file extension
        applicable_rules = self._get_applicable_rules(extension)

        if not applicable_rules:
            # No rules for this file type - skip
            return None

        # Check against all applicable patterns
        for lang, patterns in applicable_rules.items():
            for pattern_def in patterns:
                pattern = pattern_def["pattern"]

                if re.match(pattern, filename):
                    # File matches pattern - valid
                    if verbose:
                        print(f"  ✓ {file_path.relative_to(repo_root)} ({lang})")
                    return None

        # No pattern matched - violation
        relative_path = file_path.relative_to(repo_root)
        violation_msg = self._format_violation_message(filename, extension, applicable_rules)

        if verbose:
            print(f"  ✗ {relative_path}")
            print(f"     {violation_msg}")

        # Create a Violation object
        violation = Violation(tool="naming", file=str(relative_path), line=None, message=violation_msg)

        # Create a LintResult with the violation
        return LintResult(tool="naming", passed=False, violations=[violation], error=None)

    def _get_applicable_rules(self, extension: str) -> Dict[str, List[Dict]]:
        """Get naming rules applicable to a file extension.

        :param extension: File extension (e.g., '.py', '.sh')
        :returns: Dictionary mapping language to list of pattern definitions
        """
        applicable = {}

        # Map extensions to languages
        extension_map = {
            ".py": "python",
            ".sh": "bash",
            ".bash": "bash",
            ".ps1": "powershell",
            ".psm1": "powershell",
            ".pl": "perl",
            ".pm": "perl",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".md": "markdown",
            ".json": "json",
        }

        lang = extension_map.get(extension)
        if lang and lang in self.languages:
            lang_config = self.languages[lang]
            if "file_patterns" in lang_config:
                applicable[lang] = lang_config["file_patterns"]

        return applicable

    def _format_violation_message(self, filename: str, extension: str, applicable_rules: Dict[str, List[Dict]]) -> str:
        """Format a helpful violation message.

        :param filename: File name that violated rules
        :param extension: File extension
        :param applicable_rules: Applicable rules that were checked
        :returns: Formatted error message
        """
        messages = [f"Naming violation: '{filename}'"]

        for lang, patterns in applicable_rules.items():
            messages.append(f"  Expected ({lang}):")
            for pattern_def in patterns:
                description = pattern_def["description"]
                messages.append(f"    - {description}")

                # Add examples if available
                if "examples" in pattern_def:
                    examples = pattern_def["examples"]
                    if "valid" in examples and examples["valid"]:
                        valid_examples = examples["valid"][:2]  # Show max 2 examples
                        messages.append(f"      Valid: {', '.join(valid_examples)}")

        return "\n".join(messages)
