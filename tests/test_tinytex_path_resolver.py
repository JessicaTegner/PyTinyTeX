import os
import pytest

from .utils import download_tinytex

import pytinytex

def test_empty_cache(download_tinytex):
	assert pytinytex.__tinytex_path is None

def test_failing_resolver(download_tinytex):
	assert pytinytex.__tinytex_path is None
	with pytest.raises(RuntimeError):
		pytinytex._resolve_path("failing")
	assert pytinytex.__tinytex_path is None
	with pytest.raises(RuntimeError):
		pytinytex.ensure_tinytex_installed("failing")
	assert pytinytex.__tinytex_path is None

def test_successful_resolver(download_tinytex):
	assert pytinytex.__tinytex_path is None
	pytinytex.ensure_tinytex_installed("tests")
	assert isinstance(pytinytex.__tinytex_path, str)
	assert os.path.isdir(pytinytex.__tinytex_path)

def test_get_tinytex_path(download_tinytex):
	pytinytex.ensure_tinytex_installed("tests")
	assert isinstance(pytinytex.get_tinytex_path(), str)
	assert pytinytex.__tinytex_path == pytinytex.get_tinytex_path("tests")
