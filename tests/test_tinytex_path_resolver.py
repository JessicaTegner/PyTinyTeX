import os
import pytest

import pytinytex
from .utils import download_tinytex, TINYTEX_DISTRIBUTION # noqa

def test_failing_resolver(download_tinytex): # noqa
	with pytest.raises(RuntimeError):
		pytinytex._resolve_path("failing")
	with pytest.raises(RuntimeError):
		pytinytex.ensure_tinytex_installed("failing")

def test_successful_resolver(download_tinytex): # noqa
	pytinytex.ensure_tinytex_installed(TINYTEX_DISTRIBUTION)
	assert isinstance(pytinytex.__tinytex_path, str)
	assert os.path.isdir(pytinytex.__tinytex_path)

def test_get_tinytex_distribution_path(download_tinytex): # noqa
	# actually resolve the path
	pytinytex.ensure_tinytex_installed(TINYTEX_DISTRIBUTION)
	assert pytinytex.__tinytex_path == pytinytex.get_tinytex_distribution_path(TINYTEX_DISTRIBUTION)

@pytest.mark.parametrize("download_tinytex", [1], indirect=True)
def test_get_pdf_latex_engine(download_tinytex): # noqa
	pytinytex.ensure_tinytex_installed(TINYTEX_DISTRIBUTION)
	assert isinstance(pytinytex.get_pdf_latex_engine(), str)
	assert os.path.isfile(pytinytex.get_pdf_latex_engine())