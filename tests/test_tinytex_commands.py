import pytinytex

from .utils import download_tinytex # noqa: F401

def test_help(download_tinytex): # noqa: F811
	exit_code, output = pytinytex.help()
	assert exit_code == 0
	assert "the native TeX Live Manager".lower() in output.lower()
