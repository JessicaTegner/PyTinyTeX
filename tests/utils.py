import shutil
import os

import pytest

import pytinytex

@pytest.fixture(scope="module")
def download_tinytex_0():
	yield pytinytex.download_tinytex(variation=0, target_folder=os.path.join("tests", "tinytex_distribution"), download_folder="tests")
	cleanup()


@pytest.fixture(scope="module")
def download_tinytex_1():
	yield pytinytex.download_tinytex(variation=1, target_folder=os.path.join("tests", "tinytex_distribution"), download_folder="tests")
	cleanup()


def cleanup():
	shutil.rmtree(os.path.join("tests", "tinytex_distribution"))
	for item in os.listdir("tests"):
		if item.endswith(".zip") or item.endswith(".tar.gz") or item.endswith(".tgz"):
			os.remove(os.path.join("tests", item))
