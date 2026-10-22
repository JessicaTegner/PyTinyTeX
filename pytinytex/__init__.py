import logging
import os
import platform
import sys
import warnings
from collections import deque
from contextlib import suppress
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _metadata_version
from pathlib import Path

try:
    __version__ = _metadata_version("PyTinyTeX")
except PackageNotFoundError:
    __version__ = "unknown"

from .tinytex_download import download_tinytex, DEFAULT_TARGET_FOLDER  # noqa
from .log_parser import LogEntry, ParsedLog, parse_log
from .compiler import CompileResult, compile
from .doctor import DoctorCheck, DoctorResult, doctor
from .tlmgr import (  # noqa
    install,
    remove,
    list_installed,
    search,
    info,
    update,
    help,
    shell,
    get_version,
    uninstall,
    _run_tlmgr_command,
    _parse_tlmgr_list,
    _parse_tlmgr_info,
)

logger = logging.getLogger("pytinytex")
logger.addHandler(logging.NullHandler())

# Known LaTeX engines included in TinyTeX
_LATEX_ENGINES = ["pdflatex", "xelatex", "lualatex", "latex"]

# Known TeX Live platform-architecture directory names
_KNOWN_ARCHS = {
    "x86_64-linux",
    "aarch64-linux",
    "i386-linux",
    "universal-darwin",
    "x86_64-darwinlegacy",
    "windows",
}

# Global cache
__tinytex_path = None

__all__ = [
    "DEFAULT_TARGET_FOLDER",
    "CompileResult",
    "DoctorCheck",
    "DoctorResult",
    "LogEntry",
    "ParsedLog",
    "__version__",
    "clear_path_cache",
    "compile",
    "doctor",
    "download_tinytex",
    "ensure_tinytex_installed",
    "get_engine",
    "get_lualatex_engine",
    "get_pdf_latex_engine",
    "get_pdflatex_engine",
    "get_tinytex_path",
    "get_version",
    "get_xelatex_engine",
    "help",
    "info",
    "install",
    "list_installed",
    "parse_log",
    "remove",
    "search",
    "shell",
    "uninstall",
    "update",
]


# --- Path resolution ---

_HOME = Path.home()


def _xdg_data_home():
    return Path(os.getenv("XDG_DATA_HOME", _HOME / ".local/share"))


def _upstream_tinytex_dir():
    """Return the default TinyTeX install directory used by the official
    installer and by R's ``tinytex`` package (``install_tinytex``)."""
    if sys.platform == "win32":
        return Path(os.getenv("APPDATA", _HOME / "AppData/Roaming")) / "TinyTeX"
    if sys.platform == "darwin":
        return _HOME / "Library/TinyTeX"
    return _HOME / ".TinyTeX"


def candidate_tinytex_dirs():
    """Return TinyTeX install directories to search, in priority order."""
    return [
        DEFAULT_TARGET_FOLDER,
        _upstream_tinytex_dir(),
        # The XDG Base Directory Specification gives users a standard place to
        # keep an install; some move it there voluntarily.
        _xdg_data_home() / "TinyTeX",
    ]


def get_tinytex_path(base=None):
    """Return the resolved path to the TinyTeX bin directory.

    Args:
            base: Optional base directory to search in.  Falls back to the
                    ``PYTINYTEX_TINYTEX`` environment variable, then
                    DEFAULT_TARGET_FOLDER.

    Raises:
            RuntimeError: If TinyTeX is not found.
    """
    if not base and __tinytex_path:
        return __tinytex_path
    ensure_tinytex_installed(base or os.getenv("PYTINYTEX_TINYTEX"))
    return __tinytex_path


def clear_path_cache():
    """Reset the cached TinyTeX path so the next call re-resolves it."""
    global __tinytex_path
    __tinytex_path = None


def ensure_tinytex_installed(path=None):
    """Check that TinyTeX is installed and resolve the bin directory.

    Args:
            path: Path to check for TinyTeX. Defaults to the cached path or
                    automatic discovery of an existing install.

    Returns:
            True if TinyTeX is installed.

    Raises:
            RuntimeError: If TinyTeX is not found. Use
                    ``download_tinytex()`` to install it first.
    """
    global __tinytex_path
    if path:
        __tinytex_path = _resolve_tinytex([path])
    elif __tinytex_path:
        return True
    else:
        __tinytex_path = _resolve_tinytex(candidate_tinytex_dirs())
    # Ensure the resolved bin directory is on PATH for this process
    _add_to_path(__tinytex_path)
    return True


def _tinytex_path():
    """Return the current cached path (or None). Used by submodules."""
    return __tinytex_path


# --- Engine discovery ---


def get_engine(engine_name):
    """Return the full path to a LaTeX engine executable.

    Args:
            engine_name: One of 'pdflatex', 'xelatex', 'lualatex', 'latex'.

    Returns:
            Absolute path to the engine executable.

    Raises:
            ValueError: If engine_name is not a known engine.
            RuntimeError: If the engine executable is not found (e.g. TinyTeX
                    variation 0 which ships no engines).
    """
    if engine_name not in _LATEX_ENGINES:
        raise ValueError(
            f"Unknown engine '{engine_name}'. "
            f"Known engines: {', '.join(_LATEX_ENGINES)}"
        )
    path = get_tinytex_path()
    suffix = ".exe" if platform.system() == "Windows" else ""
    engine_path = os.path.join(path, engine_name + suffix)
    if not os.path.isfile(engine_path):
        raise RuntimeError(
            f"Engine '{engine_name}' not found at {engine_path}. "
            "You may need a TinyTeX variation that includes it (variation >= 1)."
        )
    return engine_path


def get_pdflatex_engine():
    """Return the full path to the pdflatex executable."""
    return get_engine("pdflatex")


def get_xelatex_engine():
    """Return the full path to the xelatex executable."""
    return get_engine("xelatex")


def get_lualatex_engine():
    """Return the full path to the lualatex executable."""
    return get_engine("lualatex")


def get_pdf_latex_engine():
    """Deprecated: Use get_pdflatex_engine() instead."""
    warnings.warn(
        "get_pdf_latex_engine() is deprecated, use get_pdflatex_engine() instead",
        DeprecationWarning,
        stacklevel=2,
    )
    return get_pdflatex_engine()


# --- Internal helpers ---


def _is_on_path(directory):
    """Check if a directory is on the system PATH, with proper normalization."""
    norm_dir = os.path.normcase(os.path.normpath(directory))
    for entry in os.environ.get("PATH", "").split(os.pathsep):
        if os.path.normcase(os.path.normpath(entry)) == norm_dir:
            return True
    return False


def _add_to_path(directory):
    """Add a directory to the system PATH for this process if not already there."""
    if not _is_on_path(directory):
        os.environ["PATH"] = directory + os.pathsep + os.environ.get("PATH", "")


def _get_platform_arch():
    """Return the TeX Live platform-architecture directory name for the current system."""
    machine = platform.machine().lower()
    system = sys.platform
    if system == "win32":
        return "windows"
    if system == "darwin":
        if machine == "arm64":
            return "universal-darwin"
        return "universal-darwin"
    # Linux
    arch_map = {
        "x86_64": "x86_64-linux",
        "amd64": "x86_64-linux",
        "aarch64": "aarch64-linux",
        "arm64": "aarch64-linux",
        "i386": "i386-linux",
        "i686": "i386-linux",
    }
    return arch_map.get(machine, machine + "-linux")


_ARCH_MISMATCH = (
    "TinyTeX architecture mismatch. The wrong binary may have "
    "been downloaded.\n{0}\nYou can point at another installation "
    "with --tinytex / PYTINYTEX_TINYTEX."
)


def _scan_candidates(paths):
    issues = {}
    pending = deque(paths)
    while pending:
        path = pending.popleft()
        if not os.path.isdir(path):
            continue  # early exit
        if _find_file(path, "tlmgr"):
            return path, issues
        if os.path.isdir(os.path.join(path, "bin")):
            pending.appendleft(os.path.join(path, "bin"))
            continue
        entries = []
        with suppress(FileNotFoundError):
            entries = [
                e for e in os.listdir(path) if os.path.isdir(os.path.join(path, e))
            ]
        # Prefer the directory matching the current platform architecture
        expected_arch = _get_platform_arch()
        if expected_arch in entries:
            pending.appendleft(os.path.join(path, expected_arch))
            continue
        # Only fall back to a single entry if it's not an architecture mismatch
        if len(entries) == 1:
            entry = entries[0]
            if entry in _KNOWN_ARCHS and entry != expected_arch:
                message = f"found '{entry}' but expected '{expected_arch}' at {path}"
                issues.setdefault(_ARCH_MISMATCH, []).append(message)
                continue
            pending.appendleft(os.path.join(path, entry))
    return None, issues


def _resolve_tinytex(candidates):
    """Return the first resolvable TinyTeX path among candidates, else raise."""
    assert len(candidates) > 0  # sanity check, removed by -O
    found, issues = _scan_candidates(candidates)
    message = _render_issues(issues)
    tried = "\n".join(f"  - {path}" for path in candidates)
    generic = (
        "Unable to resolve TinyTeX path.\n"
        f"Tried:\n{tried}\n"
        "You can install TinyTeX using pytinytex.download_tinytex(), "
        "or point at an existing install with --tinytex / PYTINYTEX_TINYTEX."
    )
    if found and message:
        logger.warning(message)
    if not found:
        raise RuntimeError(message or generic)
    return found


def _render_issues(issues):
    return "\n\n".join(
        category.format("\n".join(f"  - {detail}" for detail in details))
        for category, details in issues.items()
    )


def _find_file(dir, prefix):
    """Find a file whose stem matches *prefix* in *dir*.

    Returns the full path if found, or None.
    """
    try:
        for s in os.listdir(dir):
            if os.path.splitext(s)[0] == prefix and os.path.isfile(
                os.path.join(dir, s)
            ):
                return os.path.join(dir, s)
    except FileNotFoundError:
        pass
    return None
