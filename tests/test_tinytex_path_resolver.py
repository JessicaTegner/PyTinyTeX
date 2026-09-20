import os
import random
import string
import warnings
from pathlib import Path

import pytest

import pytinytex
from .utils import download_tinytex, TINYTEX_DISTRIBUTION  # noqa


def test_failing_resolver(download_tinytex):  # noqa
    with pytest.raises(RuntimeError, match="Unable to resolve TinyTeX path"):
        pytinytex._find_resolved(["failing"])
    with pytest.raises(RuntimeError, match="Unable to resolve TinyTeX path"):
        pytinytex.ensure_tinytex_installed("failing")


def test_successful_resolver(download_tinytex):  # noqa
    pytinytex.ensure_tinytex_installed(TINYTEX_DISTRIBUTION)
    assert isinstance(pytinytex.__tinytex_path, str)
    assert os.path.isdir(pytinytex.__tinytex_path)


def test_get_tinytex_path(download_tinytex):  # noqa
    pytinytex.ensure_tinytex_installed(TINYTEX_DISTRIBUTION)
    assert pytinytex.__tinytex_path == pytinytex.get_tinytex_path(TINYTEX_DISTRIBUTION)


def test_clear_path_cache(download_tinytex):  # noqa
    pytinytex.ensure_tinytex_installed(TINYTEX_DISTRIBUTION)
    assert pytinytex.__tinytex_path is not None
    pytinytex.clear_path_cache()
    assert pytinytex.__tinytex_path is None


@pytest.mark.parametrize("download_tinytex", [1], indirect=True)
def test_get_pdflatex_engine(download_tinytex):  # noqa
    pytinytex.ensure_tinytex_installed(TINYTEX_DISTRIBUTION)
    assert isinstance(pytinytex.get_pdflatex_engine(), str)
    assert os.path.isfile(pytinytex.get_pdflatex_engine())


@pytest.mark.parametrize("download_tinytex", [1], indirect=True)
def test_get_pdf_latex_engine_deprecated(download_tinytex):  # noqa
    pytinytex.ensure_tinytex_installed(TINYTEX_DISTRIBUTION)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = pytinytex.get_pdf_latex_engine()
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "deprecated" in str(w[0].message).lower()
    assert result == pytinytex.get_pdflatex_engine()


def test_candidate_tinytex_dirs_order(monkeypatch):
    monkeypatch.setattr(pytinytex, "_xdg_data_home", lambda: Path("/tmp/xdg"))
    monkeypatch.setattr(pytinytex, "_upstream_tinytex_dir", lambda: Path("/tmp/upstream"))
    assert pytinytex.candidate_tinytex_dirs() == [
        pytinytex.DEFAULT_TARGET_FOLDER,
        Path("/tmp/upstream"),
        Path("/tmp/xdg/TinyTeX"),
    ]


def test_xdg_data_home_env(monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", "/tmp/custom/data")
    assert pytinytex._xdg_data_home() == Path("/tmp/custom/data")


def test_xdg_data_home_default(monkeypatch):
    fake_home = Path("/tmp/fake-home")
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    monkeypatch.setattr(pytinytex, "_HOME", fake_home)
    assert pytinytex._xdg_data_home() == fake_home / ".local/share"


def test_upstream_tinytex_dir(monkeypatch):
    fake_home = Path("/tmp/fake-home")
    fake_appdata = Path("/tmp/fake-appdata/AppData/Roaming")
    monkeypatch.setattr(pytinytex, "_HOME", fake_home)
    monkeypatch.setattr("sys.platform", "darwin", raising=False)
    assert pytinytex._upstream_tinytex_dir() == fake_home / "Library/TinyTeX"
    monkeypatch.setattr("sys.platform", "linux", raising=False)
    assert pytinytex._upstream_tinytex_dir() == fake_home / ".TinyTeX"
    monkeypatch.setattr("sys.platform", "win32", raising=False)
    monkeypatch.setenv("APPDATA", os.fspath(fake_appdata))
    assert pytinytex._upstream_tinytex_dir() == fake_appdata / "TinyTeX"


def test_ensure_discovers_existing(monkeypatch, tmp_path):
    pytinytex.clear_path_cache()
    found = tmp_path / "tinytex"
    found.mkdir()
    (found / "bin").mkdir()
    (found / "bin/tlmgr").write_text("")
    missing = tmp_path / "missing"
    monkeypatch.setattr(
        pytinytex, "candidate_tinytex_dirs", lambda: [missing, found]
    )
    assert pytinytex.ensure_tinytex_installed() is True
    assert pytinytex.__tinytex_path == os.fspath(found / "bin")


def test_ensure_failure_lists_path(monkeypatch, tmp_path):
    pytinytex.clear_path_cache()
    rng = random.Random(0)
    dirs = [tmp_path / "".join(rng.choices(string.ascii_lowercase, k=5)) for _ in range(10)]
    monkeypatch.setattr(pytinytex, "candidate_tinytex_dirs", lambda: dirs)
    with pytest.raises(RuntimeError, match="Unable to resolve TinyTeX path") as exc:
        pytinytex.ensure_tinytex_installed()
    for d in dirs:
        assert os.fspath(d) in str(exc.value)


def test_get_tinytex_path_explicit_beats_env(monkeypatch, tmp_path):
    pytinytex.clear_path_cache()
    explicit = tmp_path / "explicit"
    explicit.mkdir()
    (explicit / "bin").mkdir()
    (explicit / "bin/tlmgr").write_text("")
    monkeypatch.setenv("PYTINYTEX_TINYTEX", os.fspath(tmp_path / "inexistent"))
    assert pytinytex.get_tinytex_path(base=explicit) == os.fspath(explicit / "bin")


def test_get_tinytex_path_inexistent_explicit_raises(monkeypatch, tmp_path):
    pytinytex.clear_path_cache()
    with pytest.raises(RuntimeError, match="Unable to resolve TinyTeX path"):
        pytinytex.get_tinytex_path(base=os.fspath(tmp_path / "inexistent"))


@pytest.mark.parametrize(
    "tlmgr_path",
    [
        "bin/tlmgr",
        "bin/{arch}/tlmgr",
        "nested/bin/tlmgr",
        "nested/bin/{arch}/tlmgr",
    ],
)
def test_get_tinytex_path_discovers_default(monkeypatch, tmp_path, tlmgr_path):
    pytinytex.clear_path_cache()
    found = tmp_path / "tinytex"
    monkeypatch.setattr(pytinytex, "_get_platform_arch", lambda: "fakearch")
    monkeypatch.setattr(pytinytex, "candidate_tinytex_dirs", lambda: [found])
    monkeypatch.delenv("PYTINYTEX_TINYTEX", raising=False)
    tlmgr = found / tlmgr_path.format(arch="fakearch")
    tlmgr.parent.mkdir(parents=True)
    tlmgr.write_text("")
    assert pytinytex.get_tinytex_path() == os.fspath(tlmgr.parent)


def test_architecture_mismatch_raises(monkeypatch, tmp_path):
    pytinytex.clear_path_cache()
    monkeypatch.setattr(pytinytex, "_get_platform_arch", lambda: "universal-darwin")
    d = tmp_path / "wrong"
    d.mkdir()
    (d / "x86_64-linux").mkdir()
    with pytest.raises(RuntimeError, match="architecture mismatch"):
        pytinytex._find_resolved([d])
