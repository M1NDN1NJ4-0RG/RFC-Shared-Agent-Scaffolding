"""UI theme configuration and validation for repo_lint.

:Purpose:
    Provides theme configuration loading, validation, and application for
    Rich UI rendering. Supports user customization while maintaining CI
    output determinism.

:Functions:
    - load_theme: Load and validate UI theme from YAML
    - get_theme: Get the active theme configuration
    - apply_theme: Apply theme settings to rendering

:Environment Variables:
    - REPO_LINT_UI_THEME: Path to custom UI theme YAML file

:Examples:
    Load default theme::

        from tools.repo_lint.ui.theme import load_theme
        theme = load_theme()

    Load custom theme::

        theme = load_theme(theme_path="/path/to/theme.yaml")
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import yaml
from rich import box


def _get_default_theme_path() -> Path:
    """Get the default theme path relative to repository root.

    :returns: Path to default theme YAML
    """
    # Try to find repository root by looking for .git
    current = Path.cwd()
    while current != current.parent:
        if (current / ".git").exists():
            return current / "conformance/repo-lint/repo-lint-ui-theme.yaml"
        current = current.parent
    # Fallback: assume we're in repo root
    return Path("conformance/repo-lint/repo-lint-ui-theme.yaml")


# Default theme file location (computed at module load time)
DEFAULT_THEME_PATH = _get_default_theme_path()


@dataclass
class ThemeColors:
    """Theme color configuration."""

    primary: str = "cyan"
    success: str = "green"
    failure: str = "red"
    warning: str = "yellow"
    info: str = "cyan"
    metadata: str = "dim"


@dataclass
class ThemeIcons:
    """Theme icon configuration."""

    pass_icon: str = "✅"
    fail: str = "❌"
    warn: str = "⚠️"
    skip: str = "⏭️"
    running: str = "⏳"


@dataclass
class InteractiveTheme:
    """Interactive (TTY) mode theme settings."""

    box_style: str = "ROUNDED"
    hyperlinks_enabled: bool = True
    colors: ThemeColors = None
    icons: ThemeIcons = None

    def __post_init__(self):
        """Initialize nested dataclasses."""
        if self.colors is None:
            self.colors = ThemeColors()
        if self.icons is None:
            self.icons = ThemeIcons()


@dataclass
class CITheme:
    """CI mode theme settings."""

    box_style: str = "SIMPLE"
    icons_enabled: bool = True


@dataclass
class HelpTheme:
    """Help output theme settings."""

    width: int = 120
    show_defaults: bool = True


@dataclass
class UITheme:
    """Complete UI theme configuration."""

    config_type: str = "repo-lint-ui-theme"
    version: str = "1"
    interactive: InteractiveTheme = None
    ci: CITheme = None
    help: HelpTheme = None

    def __post_init__(self):
        """Initialize nested dataclasses."""
        if self.interactive is None:
            self.interactive = InteractiveTheme()
        if self.ci is None:
            self.ci = CITheme()
        if self.help is None:
            self.help = HelpTheme()


# Global theme instance
_theme: Optional[UITheme] = None


class ThemeValidationError(Exception):
    """Raised when theme validation fails."""

    def __init__(self, message: str, file_path: Optional[Path] = None):
        """Initialize ThemeValidationError.

        :param message: Error message
        :param file_path: Path to theme file that failed validation
        """
        self.file_path = file_path
        if file_path:
            super().__init__(f"Theme validation failed for {file_path}: {message}")
        else:
            super().__init__(f"Theme validation failed: {message}")


def _validate_theme_structure(data: dict, file_path: Path) -> None:
    """Validate theme YAML structure and required fields.

    :param data: Parsed YAML data
    :param file_path: Path to theme file
    :raises ThemeValidationError: If validation fails
    """
    # Check required fields
    if "config_type" not in data:
        raise ThemeValidationError("Missing required field: config_type", file_path)

    if data["config_type"] != "repo-lint-ui-theme":
        raise ThemeValidationError(
            f"Invalid config_type: {data['config_type']} (expected: repo-lint-ui-theme)", file_path
        )

    if "version" not in data:
        raise ThemeValidationError("Missing required field: version", file_path)

    # Validate version format (must be simple integer or X.Y.Z format, no pre-release/build metadata)
    version_str = str(data["version"])
    # Check if it's a simple integer
    if version_str.isdigit():
        pass  # Valid: "1"
    # Check if it's X.Y.Z format (simple semver without pre-release/build)
    elif "." in version_str:
        parts = version_str.split(".")
        if not all(part.isdigit() for part in parts):
            raise ThemeValidationError(f"Invalid version format: {version_str} (expected integer or X.Y.Z)", file_path)
    else:
        raise ThemeValidationError(f"Invalid version format: {version_str} (expected integer or X.Y.Z)", file_path)

    # Check that we support this version (major version must be 1)
    major_version = version_str.split(".")[0]
    if major_version != "1":
        raise ThemeValidationError(f"Unsupported theme version: {version_str} (only version 1 supported)", file_path)


def _validate_no_unknown_keys(data: dict, allowed_keys: set, file_path: Path, context: str = "root") -> None:
    """Validate that no unknown keys exist at any nesting level.

    :param data: Dictionary to validate
    :param allowed_keys: Set of allowed keys
    :param file_path: Path to theme file
    :param context: Context string for error messages
    :raises ThemeValidationError: If unknown keys found
    """
    unknown_keys = set(data.keys()) - allowed_keys
    if unknown_keys:
        raise ThemeValidationError(f"Unknown keys in {context}: {', '.join(sorted(unknown_keys))}", file_path)


def load_theme(
    theme_path: Optional[Path] = None, ci_mode: bool = False, allow_user_override: bool = True
) -> UITheme:
    """Load and validate UI theme from YAML.

    Loads theme from (in precedence order):
    1. Explicit theme_path parameter
    2. REPO_LINT_UI_THEME environment variable (if allow_user_override=True)
    3. User config path ~/.config/repo-lint/repo-lint-ui-theme.yaml (if allow_user_override=True)
    4. Default repository theme

    In CI mode with allow_user_override=True (default), user overrides are ignored
    unless explicitly provided via theme_path parameter.

    :param theme_path: Explicit path to theme file
    :param ci_mode: If True, disable user overrides by default
    :param allow_user_override: If False, ignore env and user config paths
    :returns: Loaded and validated UITheme
    :raises ThemeValidationError: If theme validation fails
    """
    # Determine which theme file to load
    candidates = []

    if theme_path:
        candidates.append(theme_path)
    elif allow_user_override and not ci_mode:
        # Check environment variable
        env_theme = os.environ.get("REPO_LINT_UI_THEME")
        if env_theme:
            candidates.append(Path(env_theme))

        # Check user config path
        user_config = Path.home() / ".config" / "repo-lint" / "repo-lint-ui-theme.yaml"
        if user_config.exists():
            candidates.append(user_config)

    # Always fall back to default theme
    candidates.append(DEFAULT_THEME_PATH)

    # Find first existing theme file
    selected_theme = None
    for candidate in candidates:
        if Path(candidate).exists():
            selected_theme = Path(candidate)
            break

    if not selected_theme:
        # If no theme file exists, return default theme
        return UITheme()

    # Load and validate theme file
    with open(selected_theme, "r", encoding="utf-8") as f:
        content = f.read()

    # Check for required YAML markers
    if not content.strip().startswith("---"):
        raise ThemeValidationError("Missing required YAML start marker (---)", selected_theme)

    if not content.strip().endswith("..."):
        raise ThemeValidationError("Missing required YAML end marker (...)", selected_theme)

    # Parse YAML
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as e:
        raise ThemeValidationError(f"Invalid YAML: {e}", selected_theme) from e

    # Validate structure
    _validate_theme_structure(data, selected_theme)

    # Validate no unknown top-level keys
    allowed_top_level = {"config_type", "version", "interactive", "ci", "help"}
    _validate_no_unknown_keys(data, allowed_top_level, selected_theme, "root")

    # Build theme object
    theme = UITheme(config_type=data["config_type"], version=str(data["version"]))

    # Load interactive settings
    if "interactive" in data:
        interactive_data = data["interactive"]
        allowed_interactive = {"box_style", "hyperlinks_enabled", "colors", "icons"}
        _validate_no_unknown_keys(interactive_data, allowed_interactive, selected_theme, "interactive")

        colors = ThemeColors()
        if "colors" in interactive_data:
            colors_data = interactive_data["colors"]
            allowed_colors = {"primary", "success", "failure", "warning", "info", "metadata"}
            _validate_no_unknown_keys(colors_data, allowed_colors, selected_theme, "interactive.colors")
            colors = ThemeColors(**{k: v for k, v in colors_data.items() if k in allowed_colors})

        icons = ThemeIcons()
        if "icons" in interactive_data:
            icons_data = interactive_data["icons"]
            allowed_icons = {"pass", "fail", "warn", "skip", "running"}
            _validate_no_unknown_keys(icons_data, allowed_icons, selected_theme, "interactive.icons")
            # Map YAML keys to dataclass field names
            icon_mapping = {
                "pass": "pass_icon",
                "fail": "fail",
                "warn": "warn",
                "skip": "skip",
                "running": "running",
            }
            icon_kwargs = {icon_mapping[k]: v for k, v in icons_data.items() if k in allowed_icons}
            icons = ThemeIcons(**icon_kwargs)

        theme.interactive = InteractiveTheme(
            box_style=interactive_data.get("box_style", "ROUNDED"),
            hyperlinks_enabled=interactive_data.get("hyperlinks_enabled", True),
            colors=colors,
            icons=icons,
        )

    # Load CI settings
    if "ci" in data:
        ci_data = data["ci"]
        allowed_ci = {"box_style", "icons_enabled"}
        _validate_no_unknown_keys(ci_data, allowed_ci, selected_theme, "ci")
        theme.ci = CITheme(box_style=ci_data.get("box_style", "SIMPLE"), icons_enabled=ci_data.get("icons_enabled", True))

    # Load help settings
    if "help" in data:
        help_data = data["help"]
        allowed_help = {"width", "show_defaults"}
        _validate_no_unknown_keys(help_data, allowed_help, selected_theme, "help")
        theme.help = HelpTheme(width=help_data.get("width", 120), show_defaults=help_data.get("show_defaults", True))

    return theme


def get_theme(ci_mode: bool = False) -> UITheme:
    """Get the active theme configuration.

    :param ci_mode: If True, load with CI mode restrictions
    :returns: Active UITheme instance
    """
    global _theme  # pylint: disable=global-statement

    if _theme is None:
        _theme = load_theme(ci_mode=ci_mode)

    return _theme


def get_box_style(theme: UITheme, ci_mode: bool) -> box.Box:
    """Get the appropriate box style for current mode.

    :param theme: Active theme
    :param ci_mode: If True, use CI box style
    :returns: Rich box style
    """
    if ci_mode:
        style_name = theme.ci.box_style
    else:
        style_name = theme.interactive.box_style

    # Map style name to Rich box constant
    return getattr(box, style_name, box.ROUNDED if not ci_mode else box.SIMPLE)
