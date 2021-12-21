import shutil
import os

import pytest

from .utils import download_tinytex_2

def test_successful_download(download_tinytex_2):
	assert os.path.isdir(os.path.join("tests", "tinytex_distribution"))

def test_bin_is_in_distribution(download_tinytex_2):
	assert os.path.isdir(os.path.join("tests", "tinytex_distribution", "bin"))
