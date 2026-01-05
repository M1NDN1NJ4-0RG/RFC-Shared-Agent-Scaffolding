"""Virtual environment detection and resolution.

This module provides a single source of truth for detecting and resolving
Python virtual environments used by repo-lint.

:Purpose:
    Provide consistent virtual environment resolution across all repo-lint commands.
    Implements a clear precedence hierarchy for venv detection and provides
    cross-platform support for activation scripts and bin directories.

:Resolution Precedence:
    1. Explicit --venv flag (highest priority)
    2. .venv/ directory under repository root
    3. Currently active Python virtual environment (sys.prefix)
    4. Error if none found (lowest priority)

:Functions:
    - resolve_venv: Resolve virtual environment path with precedence rules
    - get_venv_bin_dir: Get the bin/ or Scripts/ directory for a venv
    - get_activation_script: Get the activation script path for a venv
    - is_venv_active: Check if a virtual environment is currently active
    - get_current_venv: Get the currently active virtual environment, if any

:Environment Variables:
    None. This module does not read environment variables directly.

:Examples:
    >>> from tools.repo_lint.env.venv_resolver import resolve_venv
    >>> venv_path = resolve_venv(explicit_path=None, repo_root="/path/to/repo")
    >>> print(venv_path)
    /path/to/repo/.venv

:Exit Codes:
    This module raises VenvNotFoundError on failure; it does not use exit codes directly.
    Exit codes are handled by the calling CLI commands (which, env, activate).

    - 0: Not applicable (utility module raises exceptions instead)
    - 1: Not applicable (utility module raises exceptions instead)
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional


class VenvNotFoundError(Exception):
    """Raised when no virtual environment can be resolved.

    Attributes:
        message: Human-readable error message
        remediation: Suggested remediation steps
    """

    def __init__(self, message: str, remediation: str):
        """Initialize VenvNotFoundError.

        :param message: Human-readable error message
        :param remediation: Suggested remediation steps
        """
        self.message = message
        self.remediation = remediation
        super().__init__(f"{message}\n\nRemediation:\n{remediation}")


def is_venv_active() -> bool:
    """Check if a virtual environment is currently active.

    :returns: True if a virtual environment is active, False otherwise

    :Note:
        This checks if sys.prefix differs from sys.base_prefix, which is
        the standard Python mechanism for detecting venv activation.
    """
    return sys.prefix != sys.base_prefix


def get_current_venv() -> Optional[Path]:
    """Get the currently active virtual environment, if any.

    :returns: Path to the active virtual environment, or None if not in a venv

    :Note:
        This returns sys.prefix if a venv is active. sys.prefix points to
        the root of the virtual environment directory.
    """
    if is_venv_active():
        return Path(sys.prefix)
    return None


def get_venv_bin_dir(venv_path: Path) -> Path:
    """Get the bin/ or Scripts/ directory for a virtual environment.

    :param venv_path: Path to the virtual environment root directory
    :returns: Path to the bin/ (Unix) or Scripts/ (Windows) directory

    :Note:
        On Unix-like systems (Linux, macOS), the bin directory is 'bin/'.
        On Windows, the bin directory is 'Scripts/'.
    """
    if sys.platform == "win32":
        return venv_path / "Scripts"
    return venv_path / "bin"


def get_activation_script(venv_path: Path, shell: Optional[str] = None) -> Path:
    """Get the activation script path for a virtual environment.

    :param venv_path: Path to the virtual environment root directory
    :param shell: Optional shell type (bash, zsh, fish, powershell, cmd).
                  If None, uses platform default (activate on Unix, activate.bat on Windows)
    :returns: Path to the activation script
    :raises ValueError: If the shell type is unsupported

    :Note:
        Supported shells:
        - bash/zsh: activate (Unix) or activate.bat (Windows)
        - fish: activate.fish (Unix only)
        - powershell: Activate.ps1 (cross-platform)
        - cmd: activate.bat (Windows only)
    """
    bin_dir = get_venv_bin_dir(venv_path)

    # Default: platform-specific activation script
    if shell is None:
        if sys.platform == "win32":
            return bin_dir / "activate.bat"
        return bin_dir / "activate"

    # Shell-specific activation scripts
    shell = shell.lower()
    if shell in ("bash", "zsh"):
        if sys.platform == "win32":
            return bin_dir / "activate.bat"
        return bin_dir / "activate"
    elif shell == "fish":
        if sys.platform == "win32":
            raise ValueError("Fish shell is not supported on Windows")
        return bin_dir / "activate.fish"
    elif shell == "powershell":
        return bin_dir / "Activate.ps1"
    elif shell == "cmd":
        if sys.platform != "win32":
            raise ValueError("CMD is only supported on Windows")
        return bin_dir / "activate.bat"
    else:
        raise ValueError(f"Unsupported shell: {shell}. Supported: bash, zsh, fish, powershell, cmd")


def resolve_venv(
    explicit_path: Optional[str] = None,
    repo_root: Optional[Path] = None,
) -> Path:
    """Resolve virtual environment path using precedence rules.

    Resolution Precedence:
        1. explicit_path (if provided)
        2. .venv/ under repo_root (if exists)
        3. Currently active Python venv (sys.prefix)
        4. Error (no venv found)

    :param explicit_path: Explicit venv path from --venv flag (highest priority).
                         WARNING: This path is resolved and validated but not restricted
                         to specific boundaries. Users can specify any path that contains
                         a valid Python executable. This is by design to support diverse
                         development environments, but be aware of security implications
                         when accepting paths from untrusted sources.
    :param repo_root: Repository root directory (for finding .venv/)
    :returns: Resolved Path to the virtual environment
    :raises VenvNotFoundError: If no virtual environment can be resolved

    :Example:
        >>> resolve_venv(explicit_path="/custom/venv")
        Path('/custom/venv')

        >>> resolve_venv(repo_root=Path("/repo"))  # .venv exists
        Path('/repo/.venv')

        >>> resolve_venv()  # In active venv
        Path('/home/user/.venv')

    :Security Note:
        The explicit_path is resolved using Path.resolve() which normalizes the path
        and follows symlinks. While this validates the path exists and contains a
        Python executable, it does not restrict the path to specific directories.
        Users providing --venv flags are responsible for ensuring the path is safe.
    """

    def _validate_venv_structure(venv_path: Path) -> bool:
        """Check if a directory contains a valid Python virtual environment.

        :param venv_path: Path to check
        :returns: True if valid venv, False otherwise
        """
        bin_dir = get_venv_bin_dir(venv_path)
        return (
            (bin_dir / "python").exists()
            or (bin_dir / "python.exe").exists()
            or (bin_dir / "python3").exists()
            or (bin_dir / "python3.exe").exists()
        )

    # Precedence 1: Explicit --venv flag
    if explicit_path:
        venv_path = Path(explicit_path).resolve()
        if not venv_path.exists():
            raise VenvNotFoundError(
                f"Explicit venv path does not exist: {venv_path}",
                (f"Create the virtual environment or provide a valid path:\n" f"  python3 -m venv {venv_path}"),
            )
        if not _validate_venv_structure(venv_path):
            raise VenvNotFoundError(
                f"Path exists but is not a valid virtual environment: {venv_path}",
                (
                    f"The directory does not contain a Python executable.\n"
                    f"Create a virtual environment at this location:\n"
                    f"  python3 -m venv {venv_path}"
                ),
            )
        return venv_path

    # Precedence 2: .venv/ under repo root
    if repo_root:
        repo_venv = repo_root / ".venv"
        if repo_venv.exists():
            if not _validate_venv_structure(repo_venv):
                raise VenvNotFoundError(
                    f".venv directory exists at repository root but is not a valid virtual environment: {repo_venv}",
                    (
                        f"The .venv directory does not contain a Python executable.\n"
                        f"Create or recreate the virtual environment at this location:\n"
                        f"  python3 -m venv {repo_venv}"
                    ),
                )
            return repo_venv

    # Precedence 3: Currently active venv
    current_venv = get_current_venv()
    if current_venv:
        return current_venv

    # Precedence 4: Error - no venv found
    raise VenvNotFoundError(
        "No virtual environment found",
        "Try one of the following:\n"
        "  1. Activate a virtual environment: source .venv/bin/activate\n"
        "  2. Create .venv/ in your repository: python3 -m venv .venv\n"
        "  3. Specify an explicit path: repo-lint <command> --venv /path/to/venv",
    )
