import logging
import os
import platform
import sys
import warnings
from pathlib import Path
from importlib.metadata import version as _metadata_version, PackageNotFoundError

try:
    __version__ = _metadata_version("PyTinyTeX")
except PackageNotFoundError:
    __version__ = "unknown"

from .tinytex_download import download_tinytex, DEFAULT_TARGET_FOLDER  # noqa
from .log_parser import LogEntry, ParsedLog, parse_log  # noqa
from .compiler import CompileResult, compile  # noqa
from .doctor import DoctorCheck, DoctorResult, doctor  # noqa
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

# Global cache
__tinytex_path = None

__all__ = [
    "download_tinytex",
    "DEFAULT_TARGET_FOLDER",
    "ensure_tinytex_installed",
    "get_tinytex_path",
    "clear_path_cache",
    "get_engine",
    "get_pdflatex_engine",
    "get_xelatex_engine",
    "get_lualatex_engine",
    "get_pdf_latex_engine",
    "get_version",
    "install",
    "remove",
    "list_installed",
    "search",
    "info",
    "update",
    "uninstall",
    "help",
    "shell",
    "compile",
    "CompileResult",
    "LogEntry",
    "ParsedLog",
    "parse_log",
    "doctor",
    "DoctorResult",
    "DoctorCheck",
    "__version__",
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
    if __tinytex_path:
        return __tinytex_path
    if base:
        ensure_tinytex_installed(base)
    elif os.getenv("PYTINYTEX_TINYTEX"):
        ensure_tinytex_installed(os.environ["PYTINYTEX_TINYTEX"])
    else:
        ensure_tinytex_installed()
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
        __tinytex_path = _find_resolved([path])
    elif __tinytex_path:
        return True
    else:
        __tinytex_path = _find_resolved(candidate_tinytex_dirs())
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


def _attempt_resolve_path(path):
    if not os.path.isdir(path):
        return None  # early exit
    try:
        if _find_file(path, "tlmgr"):
            return path
        if os.path.isdir(os.path.join(path, "bin")):
            return _attempt_resolve_path(os.path.join(path, "bin"))
        entries = [e for e in os.listdir(path) if os.path.isdir(os.path.join(path, e))]
        # Prefer the directory matching the current platform architecture
        expected_arch = _get_platform_arch()
        if expected_arch in entries:
            return _attempt_resolve_path(os.path.join(path, expected_arch))
        # Only fall back to a single entry if it's not an architecture mismatch
        _known_archs = {
            "x86_64-linux",
            "aarch64-linux",
            "i386-linux",
            "universal-darwin",
            "x86_64-darwinlegacy",
            "windows",
        }
        if len(entries) == 1:
            entry = entries[0]
            if entry in _known_archs and entry != expected_arch:
                raise RuntimeError(
                    f"TinyTeX architecture mismatch: found '{entry}' but "
                    f"expected '{expected_arch}'. The wrong binary may have "
                    "been downloaded.\nYou can point at another installation "
                    "with --tinytex / PYTINYTEX_TINYTEX."
                )
            return _attempt_resolve_path(os.path.join(path, entry))
    except FileNotFoundError:
        pass
    return None


def _find_resolved(candidates):
    """Return the first resolvable TinyTeX path among candidates, else raise."""
    assert len(candidates) > 0  # sanity check, removed by -O
    found = next(filter(None, map(_attempt_resolve_path, candidates)), None)
    if found:
        return found
    tried = "\n".join(f"  - {path}" for path in candidates)
    raise RuntimeError(
        "Unable to resolve TinyTeX path.\n"
        f"Tried:\n{tried}\n"
        "You can install TinyTeX using pytinytex.download_tinytex(), "
        "or point at an existing install with --tinytex / PYTINYTEX_TINYTEX."
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
