import os

import pytest

import pytinytex
from .utils import TINYTEX_DISTRIBUTION, cleanup


def test_successful_download():
    try:
        pytinytex.download_tinytex(
            variation=0, target_folder=TINYTEX_DISTRIBUTION, download_folder="tests"
        )
        assert os.path.isdir(TINYTEX_DISTRIBUTION)
        assert os.path.isdir(os.path.join(TINYTEX_DISTRIBUTION, "bin"))
    finally:
        cleanup()


def test_successful_download_specific_version():
    try:
        pytinytex.download_tinytex(
            variation=0,
            version="2024.12",
            target_folder=TINYTEX_DISTRIBUTION,
            download_folder="tests",
        )
        assert os.path.isdir(TINYTEX_DISTRIBUTION)
        assert os.path.isdir(os.path.join(TINYTEX_DISTRIBUTION, "bin"))
    finally:
        cleanup()


def test_failing_download_invalid_variation():
    with pytest.raises(RuntimeError, match="Invalid TinyTeX variation 999."):
        pytinytex.download_tinytex(variation=999)


def test_failing_download_invalid_version():
    with pytest.raises(RuntimeError, match="Invalid TinyTeX version invalid."):
        pytinytex.download_tinytex(version="invalid")


# Asset names copied from real releases of rstudio/tinytex-releases.
_ASSETS_2026_08 = [
    "/rstudio/tinytex-releases/releases/download/v2026.08/" + n
    for n in (
        "TinyTeX-0-darwin-v2026.08.tar.xz",
        "TinyTeX-0-linux-arm64-v2026.08.tar.xz",
        "TinyTeX-0-linux-x86_64-v2026.08.tar.xz",
        "TinyTeX-0-linuxmusl-x86_64-v2026.08.tar.xz",
        "TinyTeX-0-windows-v2026.08.exe",
        "TinyTeX-1-darwin-v2026.08.tar.xz",
        "TinyTeX-1-linux-arm64-v2026.08.tar.xz",
        "TinyTeX-1-linux-x86_64-v2026.08.tar.xz",
        "TinyTeX-1-linuxmusl-x86_64-v2026.08.tar.xz",
        "TinyTeX-1-tar-v2026.08.gz",
        "TinyTeX-1-windows-v2026.08.exe",
        "TinyTeX-darwin-v2026.08.tar.xz",
        "TinyTeX-linux-arm64-v2026.08.tar.xz",
        "TinyTeX-linux-x86_64-v2026.08.tar.xz",
        "TinyTeX-linuxmusl-x86_64-v2026.08.tar.xz",
        "TinyTeX-v2026.08.tar.gz",
        "TinyTeX-v2026.08.tgz",
        "TinyTeX-v2026.08.zip",
        "TinyTeX-windows-v2026.08.exe",
        "installer-unix-v2026.08.tar.gz",
    )
]
_ASSETS_DAILY = [
    "/rstudio/tinytex-releases/releases/download/daily/" + n
    for n in (
        "TinyTeX-2-darwin.tar.xz",
        "TinyTeX-2-linux-arm64.tar.xz",
        "TinyTeX-2-linux-x86_64.tar.xz",
        "TinyTeX-2-linuxmusl-x86_64.tar.xz",
        "TinyTeX-2-windows.exe",
        "TinyTeX-linux-x86_64.tar.xz",
        "TinyTeX.tar.gz",
        "TinyTeX.tgz",
        "TinyTeX.zip",
    )
]
_ASSETS_2026_03 = [
    "/rstudio/tinytex-releases/releases/download/v2026.03.02/" + n
    for n in (
        "TinyTeX-0-arm64-v2026.03.02.tar.gz",
        "TinyTeX-0-v2026.03.02.tar.gz",
        "TinyTeX-0-v2026.03.02.tgz",
        "TinyTeX-0-v2026.03.02.zip",
        "TinyTeX-arm64-v2026.03.02.tar.gz",
        "TinyTeX-v2026.03.02.tar.gz",
        "tinitex.zip",
    )
]


def _names(urls):
    return {k: v.rsplit("/", 1)[1] for k, v in urls.items()}


def test_select_urls_new_naming():
    sel = pytinytex.tinytex_download._select_tinytex_urls
    assert _names(sel(_ASSETS_2026_08, 0, arm64=False)) == {
        "darwin": "TinyTeX-0-darwin-v2026.08.tar.xz",
        "linux": "TinyTeX-0-linux-x86_64-v2026.08.tar.xz",
        "win32": "TinyTeX-0-windows-v2026.08.exe",
    }
    assert _names(sel(_ASSETS_2026_08, 1, arm64=True))["linux"] == (
        "TinyTeX-1-linux-arm64-v2026.08.tar.xz"
    )
    # community bundle: legacy archives preferred, arm64 only has tar.xz
    assert _names(sel(_ASSETS_2026_08, None, arm64=False)) == {
        "darwin": "TinyTeX-v2026.08.tgz",
        "linux": "TinyTeX-v2026.08.tar.gz",
        "win32": "TinyTeX-v2026.08.zip",
    }
    assert _names(sel(_ASSETS_2026_08, None, arm64=True))["linux"] == (
        "TinyTeX-linux-arm64-v2026.08.tar.xz"
    )
    assert sel(_ASSETS_2026_08, 2, arm64=False) == {}


def test_select_urls_musl():
    sel = pytinytex.tinytex_download._select_tinytex_urls
    assert _names(sel(_ASSETS_2026_08, 1, arm64=False, musl=True))["linux"] == (
        "TinyTeX-1-linuxmusl-x86_64-v2026.08.tar.xz"
    )
    # legacy glibc tarball must not override the musl build
    assert _names(sel(_ASSETS_2026_08, None, arm64=False, musl=True))["linux"] == (
        "TinyTeX-linuxmusl-x86_64-v2026.08.tar.xz"
    )
    # no musl arm64 build upstream: fall back to glibc arm64
    assert _names(sel(_ASSETS_2026_08, 1, arm64=True, musl=True))["linux"] == (
        "TinyTeX-1-linux-arm64-v2026.08.tar.xz"
    )
    # old releases have no musl build: fall back to glibc
    assert _names(sel(_ASSETS_2026_03, 0, arm64=False, musl=True))["linux"] == (
        "TinyTeX-0-v2026.03.02.tar.gz"
    )


def test_select_urls_daily_variation_2():
    sel = pytinytex.tinytex_download._select_tinytex_urls
    assert _names(sel(_ASSETS_DAILY, 2, arm64=True)) == {
        "darwin": "TinyTeX-2-darwin.tar.xz",
        "linux": "TinyTeX-2-linux-arm64.tar.xz",
        "win32": "TinyTeX-2-windows.exe",
    }
    assert _names(sel(_ASSETS_DAILY, None, arm64=False)) == {
        "darwin": "TinyTeX.tgz",
        "linux": "TinyTeX.tar.gz",
        "win32": "TinyTeX.zip",
    }


def test_select_urls_old_naming():
    sel = pytinytex.tinytex_download._select_tinytex_urls
    assert _names(sel(_ASSETS_2026_03, 0, arm64=False)) == {
        "darwin": "TinyTeX-0-v2026.03.02.tgz",
        "linux": "TinyTeX-0-v2026.03.02.tar.gz",
        "win32": "TinyTeX-0-v2026.03.02.zip",
    }
    assert _names(sel(_ASSETS_2026_03, 0, arm64=True))["linux"] == (
        "TinyTeX-0-arm64-v2026.03.02.tar.gz"
    )
    assert _names(sel(_ASSETS_2026_03, None, arm64=True)) == {
        "linux": "TinyTeX-arm64-v2026.03.02.tar.gz"
    }


def test_failing_download_variation_2_with_pinned_version():
    with pytest.raises(RuntimeError, match="only available with version='daily'"):
        pytinytex.download_tinytex(variation=2, version="2024.12")
