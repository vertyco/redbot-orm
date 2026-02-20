import asyncio
import importlib.util
import inspect
import os
import subprocess
import sys
import typing as t
from pathlib import Path

from discord.ext import commands
from redbot.core.data_manager import cog_data_path


def get_root(cog_instance: commands.Cog | Path) -> Path:
    """Get the root path of the cog"""
    if isinstance(cog_instance, Path):
        return cog_instance
    return Path(inspect.getfile(cog_instance.__class__)).parent


def is_unc_path(path: Path) -> bool:
    """Check if path is a UNC path"""
    return path.is_absolute() and str(path).startswith("\\\\")


def is_windows() -> bool:
    """Check if the OS is Windows"""
    return os.name == "nt"


def find_piccolo_executable() -> Path:
    """Find the piccolo executable in the system's PATH."""
    for path in os.environ["PATH"].split(os.pathsep):
        for executable_name in ["piccolo", "piccolo.exe"]:
            executable = Path(path) / executable_name
            if executable.exists():
                return executable

    # Fetch the lib path from downloader
    lib_path = cog_data_path(raw_name="Downloader") / "lib"
    if lib_path.exists():
        for folder in lib_path.iterdir():
            for executable_name in ["piccolo", "piccolo.exe"]:
                executable = folder / executable_name
                if executable.exists():
                    return executable

    # Check if lib was installed manually in the venv
    default_path = Path(sys.executable).parent / "piccolo"
    if default_path.exists():
        return default_path

    raise FileNotFoundError("Piccolo package not found!")


def get_piccolo_command() -> list[str]:
    """Get the command prefix used to execute Piccolo CLI commands.

    First tries to find a piccolo executable, then falls back to running
    piccolo as a Python module (which works when piccolo is installed via
    Red's Downloader since PYTHONPATH is injected in get_env).
    """
    try:
        return [str(find_piccolo_executable())]
    except FileNotFoundError:
        if importlib.util.find_spec("piccolo") is not None:
            return [sys.executable, "-m", "piccolo.main"]
        raise


def get_env(
    cog_instance: commands.Cog | Path,
    postgres_config: dict[str, t.Any] | None = None,
) -> dict[str, t.Any]:
    """Create mock environment for subprocess"""
    env = os.environ.copy()
    if "PICCOLO_CONF" not in env:
        # Dont want to overwrite the user's config
        env["PICCOLO_CONF"] = "db.piccolo_conf"
    env["APP_NAME"] = get_root(cog_instance).stem

    # Include Downloader lib path so subprocesses can import packages installed there
    lib_path = cog_data_path(raw_name="Downloader") / "lib"
    if lib_path.exists():
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = (
            f"{lib_path}{os.pathsep}{existing}" if existing else str(lib_path)
        )
    if isinstance(cog_instance, Path):
        env["DB_PATH"] = str(cog_instance / "db.sqlite")
    else:
        env["DB_PATH"] = str(cog_data_path(cog_instance) / "db.sqlite")
    if is_windows():
        env["PYTHONIOENCODING"] = "utf-8"
    if postgres_config is not None:
        env["POSTGRES_USER"] = postgres_config.get("user", "postgres")
        env["POSTGRES_PASSWORD"] = postgres_config.get("password", "postgres")
        env["POSTGRES_DATABASE"] = postgres_config.get("database", "postgres")
        env["POSTGRES_HOST"] = postgres_config.get("host", "localhost")
        env["POSTGRES_PORT"] = postgres_config.get("port", "5432")
    return env


def _sanitize_output(text: str) -> str:
    """Remove emojis that can cause encoding issues on some terminals"""
    replacements = {
        "👍": "[OK]",
        "🚀": "[LAUNCH]",
        "✅": "[DONE]",
        "❌": "[FAIL]",
        "⚠️": "[WARN]",
        "🔧": "[FIX]",
    }
    for emoji, replacement in replacements.items():
        text = text.replace(emoji, replacement)
    return text


async def run_shell(
    cog_instance: commands.Cog | Path,
    commands: list[str],
    is_shell: bool,
    postgres_config: dict[str, t.Any] | None = None,
) -> str:
    """Run a shell command in a separate thread"""

    def _exe() -> str:
        # When shell=True, convert list to string for cross-platform consistency
        cmd: list[str] | str = " ".join(commands) if is_shell else commands
        res = subprocess.run(
            cmd,
            stdout=sys.stdout if is_shell else subprocess.PIPE,
            stderr=sys.stdout if is_shell else subprocess.PIPE,
            shell=is_shell,
            cwd=str(get_root(cog_instance)),
            env=get_env(cog_instance, postgres_config),
        )
        if not res.stdout:
            return ""
        return _sanitize_output(res.stdout.decode(encoding="utf-8", errors="ignore"))

    return await asyncio.to_thread(_exe)
