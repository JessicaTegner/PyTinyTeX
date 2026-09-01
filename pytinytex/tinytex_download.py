import glob
import logging
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.error
import zipfile
from pathlib import Path
from urllib.request import urlopen

logger = logging.getLogger("pytinytex")

DEFAULT_TARGET_FOLDER = Path.home() / ".pytinytex"


def _is_arm64():
    """Return True if running on an ARM64/aarch64 machine."""
    return platform.machine().lower() in ("aarch64", "arm64")


def _is_musl():
    """Return True if running on a musl-based Linux (e.g. Alpine)."""
    return bool(glob.glob("/lib/ld-musl-*.so.1"))


def _default_progress(downloaded, total):
    """Print download progress on a TTY."""
    if total > 0:
        pct = downloaded * 100 // total
        mb = downloaded / (1024 * 1024)
        mb_total = total / (1024 * 1024)
        sys.stdout.write(
            "\rDownloading TinyTeX: %.1f/%.1f MB (%d%%)" % (mb, mb_total, pct)
        )
        sys.stdout.flush()
        if downloaded >= total:
            sys.stdout.write("\n")


def download_tinytex(
    version="latest",
    variation=1,
    target_folder=DEFAULT_TARGET_FOLDER,
    download_folder=None,
    progress_callback=None,
):
    if variation not in [None, 0, 1, 2]:
        raise RuntimeError(
            "Invalid TinyTeX variation {}. Valid variations are None, 0, 1, 2.".format(
                variation
            )
        )
    if version == "latest" and variation == 2:
        logger.info("TinyTeX-2 is only published in the daily release, using it.")
        version = "daily"
    if re.match(r"\d{4}\.\d{2}", version):
        if variation == 2:
            raise RuntimeError(
                "TinyTeX variation 2 is only available with version='daily'."
            )
        version = "v" + version
    elif version not in ("latest", "daily"):
        raise RuntimeError(
            "Invalid TinyTeX version {}. TinyTeX version has to be in the format "
            "'latest' for the latest available version, 'daily' for the daily "
            "build, or year.month, for example: '2024.12', '2024.09' for a "
            "specific version.".format(version)
        )
    if progress_callback is None and sys.stdout.isatty():
        progress_callback = _default_progress
    pf = sys.platform
    if pf.startswith("linux"):
        pf = "linux"
        if platform.architecture()[0] != "64bit":
            raise RuntimeError("Linux TinyTeX is only compiled for 64bit.")
    # get TinyTeX
    tinytex_urls, _ = _get_tinytex_urls(version, variation)
    if pf not in tinytex_urls:
        raise RuntimeError(
            "Can't handle your platform (only Linux, Mac OS X, Windows)."
        )
    url = tinytex_urls[pf]
    filename = url.split("/")[-1]
    if download_folder:
        download_folder = Path(download_folder)
    else:
        download_folder = Path(".")
    if target_folder:
        target_folder = Path(target_folder)
    # make sure all the folders exist
    download_folder.mkdir(parents=True, exist_ok=True)
    target_folder.mkdir(parents=True, exist_ok=True)
    filename = download_folder / filename
    if filename.exists():
        logger.info("* Using already downloaded file %s", filename)
    else:
        logger.info("* Downloading TinyTeX from %s ...", url)
        response = urlopen(url)
        total_size = int(response.headers.get("Content-Length", 0))
        with open(filename, "wb") as out_file:
            downloaded = 0
            while True:
                chunk = response.read(8192)
                if not chunk:
                    break
                out_file.write(chunk)
                downloaded += len(chunk)
                if progress_callback:
                    progress_callback(downloaded, total_size)
        logger.info("* Downloaded TinyTeX, saved in %s ...", filename)

    logger.info("Extracting %s to a temporary folder...", filename)
    with tempfile.TemporaryDirectory() as tmpdirname:
        tmpdirname = Path(tmpdirname)
        if filename.suffix == ".zip":
            with zipfile.ZipFile(filename) as zf:
                zf.extractall(tmpdirname)
        elif filename.suffix == ".exe":
            # 7-Zip self-extracting archive (Windows)
            subprocess.run(
                [str(filename), "-y", "-o" + str(tmpdirname)],
                check=True,
                capture_output=True,
            )
        elif filename.suffix in (".tgz", ".gz", ".xz"):
            with tarfile.open(filename, "r:*") as tf:
                tf.extractall(tmpdirname)
        else:
            raise RuntimeError("File {0} not supported".format(filename))
        # archives contain a single "TinyTeX" (or ".TinyTeX" on Linux) folder
        tinytex_extracted = next(
            p for p in tmpdirname.iterdir() if p.name.lstrip(".") == "TinyTeX"
        )
        logger.info("Copying TinyTeX to %s...", target_folder)
        shutil.copytree(tinytex_extracted, target_folder, dirs_exist_ok=True)
    # Resolve the path and add to PATH so everything is ready to use
    from . import ensure_tinytex_installed

    ensure_tinytex_installed(target_folder)
    logger.info("Done")


def _get_tinytex_urls(version, variation):
    url = (
        "https://github.com/rstudio/tinytex-releases/releases/"
        + ("tag/" if version != "latest" else "")
        + version
    )
    try:
        response = urlopen(url)
        version_url_frags = response.url.split("/")
        version = version_url_frags[-1]
    except urllib.error.HTTPError:
        raise RuntimeError("Can't find TinyTeX version %s" % version)
    response = urlopen(
        "https://github.com/rstudio/tinytex-releases/releases/expanded_assets/"
        + version
    )
    content = response.read()
    regex = re.compile(
        r"/rstudio/tinytex-releases/releases/download/[^\"]*TinyTeX[^\"]*"
        r"\.(?:tar\.gz|tar\.xz|tgz|zip|exe)"
    )
    tinytex_urls_list = regex.findall(content.decode("utf-8"))
    tinytex_urls = _select_tinytex_urls(
        tinytex_urls_list, variation, _is_arm64(), _is_musl()
    )
    return tinytex_urls, version


_ASSET_RE = re.compile(
    r"^TinyTeX(?:-([012]))?"
    r"(?:-(darwin|linux-x86_64|linux-arm64|linuxmusl-x86_64|windows))?"
    r"(-arm64)?(?:-v[\d.]+)?\.(tar\.xz|exe|tar\.gz|tgz|zip)$"
)


def _select_tinytex_urls(asset_paths, variation, arm64, musl=False):
    """Map release asset paths to {sys.platform: url} for the given variation.

    Handles both the naming used up to v2026.03.02
    (``TinyTeX-1[-arm64]-v2026.03.tar.gz`` / ``.tgz`` / ``.zip``) and the
    naming used since (``TinyTeX-1-linux-arm64-v2026.04.tar.xz`` /
    ``TinyTeX-1-windows-v2026.04.exe``).  Legacy archives win when both exist,
    except on musl where the dedicated musl build (new naming only) is used.
    """
    new_style, old_style = {}, {}
    for path in asset_paths:
        m = _ASSET_RE.match(path.split("/")[-1])
        if not m:
            continue
        num, os_name, arm_suffix, ext = m.groups()
        if (int(num) if num else None) != variation:
            continue
        url = "https://github.com" + path
        if os_name == "darwin":
            new_style["darwin"] = url
        elif os_name == "windows":
            new_style["win32"] = url
        elif os_name == "linux-arm64" and arm64:
            new_style["linux"] = url
        elif os_name == "linux-x86_64" and not arm64 and not musl:
            new_style["linux"] = url
        elif os_name == "linuxmusl-x86_64" and not arm64 and musl:
            new_style["linux"] = url
        elif os_name is None:
            if ext == "zip":
                old_style["win32"] = url
            elif ext == "tgz":
                old_style["darwin"] = url
            elif ext == "tar.gz" and arm64 == bool(arm_suffix):
                old_style["linux"] = url
    if musl and "linux" in new_style:
        old_style.pop("linux", None)  # legacy tarballs are glibc-only
    return {**new_style, **old_style}
