import os

from .utils import download_tinytex # noqa

def test_successful_download(download_tinytex): # noqa
	assert os.path.isdir(os.path.join("tests", "tinytex_distribution"))

def test_bin_is_in_distribution(download_tinytex): # noqa
	assert os.path.isdir(os.path.join("tests", "tinytex_distribution", "bin"))
