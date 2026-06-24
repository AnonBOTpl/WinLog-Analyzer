import sys, os
from pathlib import Path


def _base_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


def _data_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(os.environ.get("APPDATA", Path.home())) / "WinLog Analyzer"
    return _base_path()


def resource_path(relative: str) -> Path:
    """Get absolute path to a file bundled with the application.

    In frozen mode (PyInstaller), resolves from sys.executable's directory.
    In dev mode, resolves from the project root.
    """
    return _base_path() / relative


def data_file(relative: str) -> Path:
    """Get absolute path to a user-data file (settings, database, etc.).

    In frozen mode, resolves to %APPDATA%\WinLog Analyzer.
    In dev mode, resolves to the project root.
    """
    return _data_path() / relative
