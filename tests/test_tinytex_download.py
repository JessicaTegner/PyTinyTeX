import shutil
import os

import pytest

from .utils import download_tinytex

def test_successful_download(download_tinytex):
	assert os.path.isdir(os.path.join("tests", "tinytex_distribution"))

def test_bin_is_in_distribution(download_tinytex):
	assert os.path.isdir(os.path.join("tests", "tinytex_distribution", "bin"))
