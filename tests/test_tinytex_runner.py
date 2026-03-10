import pytinytex
from .utils import download_tinytex, TINYTEX_DISTRIBUTION  # noqa


def test_run_help(download_tinytex):  # noqa
    pytinytex.ensure_tinytex_installed(TINYTEX_DISTRIBUTION)
    exit_code, output = pytinytex.help()
    assert exit_code == 0
    assert "TeX Live" in output


def test_get_version(download_tinytex):  # noqa
    pytinytex.ensure_tinytex_installed(TINYTEX_DISTRIBUTION)
    version = pytinytex.get_version()
    assert isinstance(version, str)
    assert "TeX Live" in version or "tlmgr" in version
