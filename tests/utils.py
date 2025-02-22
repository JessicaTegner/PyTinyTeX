import shutil
import os

import pytest

import pytinytex

TINYTEX_DISTRIBUTION = os.path.join("tests", "tinytex_distribution")

@pytest.fixture(scope="module")
def download_tinytex(request):
	try:
		variation = request.param
	except AttributeError:
		variation = 0
	yield pytinytex.download_tinytex(variation=variation, target_folder=TINYTEX_DISTRIBUTION, download_folder="tests")
	cleanup()


def cleanup():
	shutil.rmtree(os.path.join("tests", "tinytex_distribution"))
	for item in os.listdir("tests"):
		if item.endswith(".zip") or item.endswith(".tar.gz") or item.endswith(".tgz"):
			os.remove(os.path.join("tests", item))
