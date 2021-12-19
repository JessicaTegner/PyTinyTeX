import os
import pytest

from .utils import download_tinytex_0

import pytinytex

def test_empty_cache(download_tinytex_0):
	assert pytinytex.__tinytex_path is None

def test_failing_resolver(download_tinytex_0):
	assert pytinytex.__tinytex_path is None
	with pytest.raises(RuntimeError):
		pytinytex._resolve_path("failing")
	assert pytinytex.__tinytex_path is None
	pytinytex.ensure_tinytex_installed("failing")
	assert pytinytex.__tinytex_path is None

def test_successful_resolver(download_tinytex_0):
	assert pytinytex.__tinytex_path is None
	pytinytex.ensure_tinytex_installed()
	assert isinstance(pytinytex.__tinytex_path, str)
	assert os.path.isdir(pytinytex.__tinytex_path)
