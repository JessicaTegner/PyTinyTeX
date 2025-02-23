import pytinytex
from .utils import download_tinytex, TINYTEX_DISTRIBUTION # noqa

def test_run_help(download_tinytex): # noqa
    exit_code, output = pytinytex.help()
    assert exit_code == 0
    assert "TeX Live" in output

