"""Environment and PATH management utilities for repo-lint.

:Purpose:
    Provides shared utilities for detecting and managing Python virtual environments,
    shell detection, and PATH management. These utilities support the env, activate,
    and which commands without automatic rc file editing.

:Functions:
    - resolve_venv: Resolve venv path with precedence rules
    - get_venv_bin_dir: Get bin/Scripts directory for a venv
    - get_venv_activate_script: Get activation script path for a venv
    - detect_shell: Detect current shell type
    - is_in_venv: Check if currently running in a venv
    - generate_shell_snippet: Generate shell-specific PATH snippet
    - get_user_config_dir: Get user config directory for repo-lint

:Precedence Rules for venv resolution:
    1. Explicit --venv flag (if provided)
    2. .venv/ directory under repository root
    3. Current Python venv (sys.prefix if in venv)
    4. Error (no venv found)

:Shell Detection:
    Detects shell type from environment variables and process information:
    - bash: BASH_VERSION or process name
    - zsh: ZSH_VERSION or process name
    - fish: FISH_VERSION or process name
    - powershell: POWERSHELL_VERSION or process name (pwsh/powershell)
    - cmd: Windows CMD (COMSPEC)

:Examples:
    Resolve venv with precedence::

        from tools.repo_lint.env_utils import resolve_venv
        venv_path = resolve_venv(explicit_venv=None)

    Detect current shell::

        from tools.repo_lint.env_utils import detect_shell
        shell = detect_shell()  # Returns "bash", "zsh", "fish", "powershell", "cmd", or "unknown"

    Generate PATH snippet::

        from tools.repo_lint.env_utils import generate_shell_snippet
        snippet = generate_shell_snippet(venv_path, shell="bash")
"""

import os
import platform
import sys
from pathlib import Path
from typing import Optional, Tuple


def temporary_test_function():
    """Temporary test function with bad formatting."""
    x = 1 + 2 + 3
    y = 4 + 5 + 6
    return x + y
    """Resolve virtual environment path using precedence rules.

    Precedence:
        1. explicit_venv parameter (if provided)
        2. .venv/ directory under repository root
        3. Current Python venv (sys.prefix if in venv)
        4. Error (no venv found)

    :param explicit_venv: Explicit venv path from --venv flag (optional)
    :returns: Resolved venv path
    :raises RuntimeError: If no venv can be found
    """
    # Precedence 1: Explicit --venv flag
    if explicit_venv:
        venv_path = Path(explicit_venv).resolve()
        if not venv_path.exists():
            raise RuntimeError(f"Specified venv does not exist: {venv_path}")
        if not _is_valid_venv(venv_path):
            raise RuntimeError(
                f"Specified path is not a valid venv: {venv_path}\n" "Expected Python executable not found."
            )
        return venv_path

    # Precedence 2: .venv/ under repo root
    from tools.repo_lint.repo_utils import find_repo_root

    repo_root = find_repo_root()
    repo_venv = repo_root / ".venv"
    if repo_venv.exists() and _is_valid_venv(repo_venv):
        return repo_venv

    # Precedence 3: Current Python venv
    if is_in_venv():
        return Path(sys.prefix)

    # Precedence 4: Error
    raise RuntimeError(
        "No virtual environment found.\n"
        "Tried:\n"
        f"  1. .venv/ under repo root: {repo_venv} (not found)\n"
        f"  2. Current Python venv: {sys.prefix} (not in venv)\n"
        "\n"
        "To fix:\n"
        "  - Create a venv: python3 -m venv .venv\n"
        "  - Activate existing venv: source .venv/bin/activate\n"
        "  - Or specify with: --venv /path/to/venv"
    )


def _is_valid_venv(venv_path: Path) -> bool:
    """Check if path is a valid Python virtual environment.

    :param venv_path: Path to check
    :returns: True if valid venv, False otherwise
    """
    if not venv_path.is_dir():
        return False

    # Check for Python executable
    if platform.system() == "Windows":
        python_exe = venv_path / "Scripts" / "python.exe"
    else:
        python_exe = venv_path / "bin" / "python"

    return python_exe.exists()


def get_venv_bin_dir(venv_path: Path) -> Path:
    """Get the bin/Scripts directory for a virtual environment.

    :param venv_path: Path to venv
    :returns: Path to bin/ (Unix) or Scripts/ (Windows)
    """
    if platform.system() == "Windows":
        return venv_path / "Scripts"
    return venv_path / "bin"


def get_venv_activate_script(venv_path: Path) -> Path:
    """Get the activation script path for a virtual environment.

    :param venv_path: Path to venv
    :returns: Path to activate script
    """
    if platform.system() == "Windows":
        # PowerShell activation script
        return venv_path / "Scripts" / "Activate.ps1"
    return venv_path / "bin" / "activate"


def is_in_venv() -> bool:
    """Check if currently running in a virtual environment.

    :returns: True if in venv, False otherwise
    """
    # Standard venv detection
    return sys.prefix != sys.base_prefix


def detect_shell() -> str:
    """Detect current shell type.

    :returns: Shell name: "bash", "zsh", "fish", "powershell", "cmd", or "unknown"
    """
    # Check environment variables first (most reliable)
    if os.getenv("BASH_VERSION"):
        return "bash"
    if os.getenv("ZSH_VERSION"):
        return "zsh"
    if os.getenv("FISH_VERSION"):
        return "fish"

    # PowerShell detection
    if os.getenv("PSModulePath"):  # PowerShell sets this
        return "powershell"

    # CMD detection (Windows)
    if platform.system() == "Windows":
        comspec = os.getenv("COMSPEC", "").lower()
        if "cmd.exe" in comspec:
            return "cmd"

    # Fall back to SHELL environment variable
    shell_path = os.getenv("SHELL", "")
    if shell_path:
        shell_name = Path(shell_path).name.lower()
        if "bash" in shell_name:
            return "bash"
        if "zsh" in shell_name:
            return "zsh"
        if "fish" in shell_name:
            return "fish"

    # Try parent process name (Unix-like)
    try:
        import psutil

        parent = psutil.Process(os.getppid())
        parent_name = parent.name().lower()
        if "bash" in parent_name:
            return "bash"
        if "zsh" in parent_name:
            return "zsh"
        if "fish" in parent_name:
            return "fish"
        if "pwsh" in parent_name or "powershell" in parent_name:
            return "powershell"
        if "cmd" in parent_name:
            return "cmd"
    except (ImportError, Exception):  # pylint: disable=broad-except
        # psutil not available or process lookup failed
        pass

    return "unknown"


def generate_shell_snippet(venv_path: Path, shell: str) -> Tuple[str, str]:
    """Generate shell-specific PATH snippet for venv.

    :param venv_path: Path to venv
    :param shell: Shell type (bash, zsh, fish, powershell, cmd)
    :returns: Tuple of (snippet_content, file_extension)
    :raises ValueError: If shell type is unknown
    """
    bin_dir = get_venv_bin_dir(venv_path)

    if shell == "bash":
        snippet = f'# repo-lint venv activation\nexport PATH="{bin_dir}:$PATH"\n'
        return snippet, ".bash"

    if shell == "zsh":
        snippet = f'# repo-lint venv activation\nexport PATH="{bin_dir}:$PATH"\n'
        return snippet, ".zsh"

    if shell == "fish":
        snippet = f'# repo-lint venv activation\nset -gx PATH "{bin_dir}" $PATH\n'
        return snippet, ".fish"

    if shell == "powershell":
        snippet = f'# repo-lint venv activation\n$env:PATH = "{bin_dir};$env:PATH"\n'
        return snippet, ".ps1"

    if shell == "cmd":
        snippet = f"REM repo-lint venv activation\nSET PATH={bin_dir};%PATH%\n"
        return snippet, ".bat"

    raise ValueError(f"Unknown shell type: {shell}")


def get_user_config_dir() -> Path:
    """Get user configuration directory for repo-lint.

    :returns: Path to user config directory (creates if not exists)
    """
    if platform.system() == "Windows":
        # Windows: %APPDATA%\repo-lint
        appdata = os.getenv("APPDATA")
        if appdata:
            config_dir = Path(appdata) / "repo-lint"
        else:
            # Fallback to user home
            config_dir = Path.home() / "AppData" / "Roaming" / "repo-lint"
    else:
        # Unix-like: ~/.config/repo-lint
        xdg_config_home = os.getenv("XDG_CONFIG_HOME")
        if xdg_config_home:
            config_dir = Path(xdg_config_home) / "repo-lint"
        else:
            config_dir = Path.home() / ".config" / "repo-lint"

    # Create if not exists
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir
