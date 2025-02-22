import pytinytex

from .utils import download_tinytex

def test_help(download_tinytex):
	exit_code, output = pytinytex.help()
	assert exit_code == 0
	assert "the native TeX Live Manager".lower() in output.lower()
