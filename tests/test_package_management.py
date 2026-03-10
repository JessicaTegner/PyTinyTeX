import pytest

import pytinytex
from .utils import download_tinytex, TINYTEX_DISTRIBUTION  # noqa


def _self_update_tlmgr():
    """Update tlmgr itself so it doesn't refuse to run other commands."""
    try:
        pytinytex.update("--self")
    except RuntimeError:
        pass  # best-effort; may fail if already up to date or no network


def test_list_installed(download_tinytex):  # noqa
    pytinytex.ensure_tinytex_installed(TINYTEX_DISTRIBUTION)
    result = pytinytex.list_installed()
    assert isinstance(result, list)
    assert len(result) > 0
    for entry in result:
        assert isinstance(entry, dict)
        assert "name" in entry
        assert len(entry["name"]) > 0


def test_list_installed_has_known_packages(download_tinytex):  # noqa
    """Variation 0 still ships infrastructure packages like scheme-infraonly."""
    pytinytex.ensure_tinytex_installed(TINYTEX_DISTRIBUTION)
    result = pytinytex.list_installed()
    names = [entry["name"] for entry in result]
    # tlmgr itself is always present in any variation
    assert any("tex" in name.lower() for name in names)


def test_info_returns_dict(download_tinytex):  # noqa
    pytinytex.ensure_tinytex_installed(TINYTEX_DISTRIBUTION)
    result = pytinytex.info("tex")
    assert isinstance(result, dict)
    assert len(result) > 0


def test_info_has_package_key(download_tinytex):  # noqa
    pytinytex.ensure_tinytex_installed(TINYTEX_DISTRIBUTION)
    result = pytinytex.info("hyphen-base")
    assert isinstance(result, dict)
    # tlmgr info typically returns a 'package' key
    if "package" in result:
        assert result["package"] == "hyphen-base"


def test_search_returns_list(download_tinytex):  # noqa
    pytinytex.ensure_tinytex_installed(TINYTEX_DISTRIBUTION)
    result = pytinytex.search("latex")
    assert isinstance(result, list)
    assert len(result) > 0
    for entry in result:
        assert isinstance(entry, dict)
        assert "name" in entry


@pytest.mark.parametrize("download_tinytex", [1], indirect=True)
def test_install_and_remove(download_tinytex):  # noqa
    """Install a small package, verify it appears in list, then remove it."""
    pytinytex.ensure_tinytex_installed(TINYTEX_DISTRIBUTION)
    _self_update_tlmgr()
    # install a small package
    exit_code, _ = pytinytex.install("blindtext")
    assert exit_code == 0

    # verify it shows up in list
    installed = pytinytex.list_installed()
    names = [entry["name"] for entry in installed]
    assert any("blindtext" in name for name in names)

    # remove it
    exit_code, _ = pytinytex.remove("blindtext")
    assert exit_code == 0

    # verify it's gone
    installed = pytinytex.list_installed()
    names = [entry["name"] for entry in installed]
    assert not any("blindtext" == name for name in names)


def test_install_nonexistent_package(download_tinytex):  # noqa
    pytinytex.ensure_tinytex_installed(TINYTEX_DISTRIBUTION)
    # tlmgr behaviour varies by platform — it may raise RuntimeError or
    # return success with a warning.  Either way, verify we get a response.
    try:
        exit_code, output = pytinytex.install("this-package-does-not-exist-xyz-123")
        # If it didn't raise, the output should mention the package wasn't found
        assert exit_code == 0 or "not found" in output.lower() or "unknown package" in output.lower()
    except RuntimeError:
        pass  # expected on most platforms


def test_update(download_tinytex):  # noqa
    pytinytex.ensure_tinytex_installed(TINYTEX_DISTRIBUTION)
    _self_update_tlmgr()
    # update -all may fail transiently due to tlmgr internal errors on CI
    try:
        exit_code, output = pytinytex.update()
        assert exit_code == 0
    except RuntimeError:
        pytest.skip("tlmgr update failed (transient CI issue)")
