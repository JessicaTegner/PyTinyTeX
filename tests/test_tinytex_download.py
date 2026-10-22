import os
import shutil
import ssl
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import certifi
import pytest
import requests

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
    assert "linux" not in sel(_ASSETS_2026_08, 1, arm64=True, musl=True)
    assert "linux" not in sel(_ASSETS_2026_03, 0, arm64=False, musl=True)
    assert "linux" not in sel(_ASSETS_2026_03, 0, arm64=True, musl=True)


@pytest.mark.parametrize(
    "assets, machine, version",
    [
        (_ASSETS_2026_08, "aarch64", "v2026.08"),
        (_ASSETS_2026_03, "x86_64", "v2026.03.02"),
    ],
)
def test_failing_download_unsupported_musl(monkeypatch, assets, machine, version):
    downloader = pytinytex.tinytex_download
    monkeypatch.setattr(downloader.sys, "platform", "linux")
    monkeypatch.setattr(downloader.platform, "machine", lambda: machine)
    monkeypatch.setattr(downloader.platform, "architecture", lambda: ("64bit", ""))
    monkeypatch.setattr(downloader, "_is_musl", lambda: True)
    monkeypatch.setattr(
        downloader,
        "_get_tinytex_urls",
        lambda v, variation: (
            downloader._select_tinytex_urls(
                assets, variation, arm64=machine == "aarch64", musl=True
            ),
            version,
        ),
    )
    with pytest.raises(RuntimeError) as exc:
        pytinytex.download_tinytex(variation=0)
    assert str(exc.value) == (
        f"No prebuilt TinyTeX variation 0 for Linux {machine} (musl) "
        f"in release {version}."
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


def test_http_get_uses_requests(monkeypatch):
    calls = []

    class _Response:
        url = "https://github.com/rstudio/tinytex-releases/releases/tag/v2026.03"
        content = b""
        headers = {"Content-Length": "4"}

        def raise_for_status(self):
            return None

        def iter_content(self, chunk_size=8192):
            yield b"data"

    def fake_get(url, timeout=None, stream=False, verify=True):
        calls.append(
            {"url": url, "timeout": timeout, "stream": stream, "verify": verify}
        )
        return _Response()

    monkeypatch.setattr(pytinytex.tinytex_download.requests, "get", fake_get)
    response = pytinytex.tinytex_download._http_get("https://example.test/asset")
    assert response.content == b""
    assert calls == [
        {
            "url": "https://example.test/asset",
            "timeout": pytinytex.tinytex_download._HTTP_TIMEOUT,
            "stream": False,
            "verify": certifi.where(),
        }
    ]
    pytinytex.tinytex_download._http_get("https://example.test/asset", stream=True)
    assert calls[-1]["stream"] is True
    assert calls[-1]["timeout"] == pytinytex.tinytex_download._DOWNLOAD_TIMEOUT


def test_missing_release_raises_runtime_error(monkeypatch):
    def fake_get(url, timeout=None, stream=False, verify=True):
        response = requests.models.Response()
        response.status_code = 404
        response.reason = "Not Found"
        response.url = url
        return response

    monkeypatch.setattr(pytinytex.tinytex_download.requests, "get", fake_get)
    with pytest.raises(RuntimeError, match="Can't find TinyTeX version"):
        pytinytex.tinytex_download._get_tinytex_urls("v1999.01", 1)


def test_http_get_uses_certifi_ca_bundle(monkeypatch):
    captured = {}

    class _Response:
        def raise_for_status(self):
            return None

    def fake_get(url, timeout=None, stream=False, verify=True):
        captured["verify"] = verify
        return _Response()

    monkeypatch.setattr(pytinytex.tinytex_download.requests, "get", fake_get)
    pytinytex.tinytex_download._http_get("https://example.test/asset")
    bundle = Path(certifi.where())
    assert bundle.is_file()
    assert captured["verify"] == str(bundle)
    assert captured["verify"] is not True
    assert captured["verify"] is not False


@pytest.mark.skipif(shutil.which("openssl") is None, reason="openssl is required to mint a test certificate")
def test_http_get_rejects_untrusted_certificate(tmp_path):
    key = tmp_path / "key.pem"
    cert = tmp_path / "cert.pem"
    subprocess.run(
        [
            "openssl",
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-keyout",
            str(key),
            "-out",
            str(cert),
            "-days",
            "1",
            "-nodes",
            "-subj",
            "/CN=localhost",
        ],
        check=True,
        capture_output=True,
    )

    class _Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")

        def log_message(self, *_args):
            return

    server = HTTPServer(("127.0.0.1", 0), _Handler)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(str(cert), str(key))
    server.socket = ctx.wrap_socket(server.socket, server_side=True)
    thread = threading.Thread(target=server.handle_request)
    thread.daemon = True
    thread.start()
    url = "https://127.0.0.1:%d/" % server.server_address[1]
    try:
        with pytest.raises(requests.exceptions.SSLError):
            pytinytex.tinytex_download._http_get(url)
    finally:
        server.server_close()
        thread.join(timeout=2)
