import os
import shutil
import pytest

import pytinytex

def test_successful_download(): # noqa
	pytinytex.download_tinytex(variation=0, target_folder="tests/tinytex_distribution", download_folder="tests")
	assert os.path.isdir(os.path.join("tests", "tinytex_distribution"))
	assert os.path.isdir(os.path.join("tests", "tinytex_distribution", "bin"))
	shutil.rmtree(os.path.join("tests", "tinytex_distribution"))
	for item in os.listdir("tests"):
		if item.endswith(".zip") or item.endswith(".tar.gz") or item.endswith(".tgz"):
			os.remove(os.path.join("tests", item))

def test_successful_download_specific_version():
	pytinytex.download_tinytex(variation=0, version="2024.12", target_folder="tests/tinytex_distribution", download_folder="tests")
	assert os.path.isdir(os.path.join("tests", "tinytex_distribution"))
	assert os.path.isdir(os.path.join("tests", "tinytex_distribution", "bin"))
	shutil.rmtree(os.path.join("tests", "tinytex_distribution"))
	# delete any files in the test dir that ends with zip, gz or tgz
	for item in os.listdir("tests"):
		if item.endswith(".zip") or item.endswith(".tar.gz") or item.endswith(".tgz"):
			os.remove(os.path.join("tests", item))

def test_failing_download_invalid_variation():
	with pytest.raises(RuntimeError, match="Invalid TinyTeX variation 999."):
		pytinytex.download_tinytex(variation=999)

def test_failing_download_invalid_version():
	with pytest.raises(RuntimeError, match="Invalid TinyTeX version invalid."):
		pytinytex.download_tinytex(version="invalid")
