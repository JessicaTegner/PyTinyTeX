import os

import pytest

import pytinytex
from .utils import download_tinytex, TINYTEX_DISTRIBUTION  # noqa


@pytest.mark.parametrize("download_tinytex", [1], indirect=True)
def test_get_engine_pdflatex(download_tinytex):  # noqa
    pytinytex.ensure_tinytex_installed(TINYTEX_DISTRIBUTION)
    path = pytinytex.get_engine("pdflatex")
    assert isinstance(path, str)
    assert os.path.isfile(path)
    assert "pdflatex" in path


@pytest.mark.parametrize("download_tinytex", [1], indirect=True)
def test_get_engine_xelatex(download_tinytex):  # noqa
    pytinytex.ensure_tinytex_installed(TINYTEX_DISTRIBUTION)
    path = pytinytex.get_engine("xelatex")
    assert isinstance(path, str)
    assert os.path.isfile(path)
    assert "xelatex" in path


@pytest.mark.parametrize("download_tinytex", [1], indirect=True)
def test_get_engine_lualatex(download_tinytex):  # noqa
    pytinytex.ensure_tinytex_installed(TINYTEX_DISTRIBUTION)
    path = pytinytex.get_engine("lualatex")
    assert isinstance(path, str)
    assert os.path.isfile(path)
    assert "lualatex" in path


@pytest.mark.parametrize("download_tinytex", [1], indirect=True)
def test_get_engine_convenience_functions(download_tinytex):  # noqa
    pytinytex.ensure_tinytex_installed(TINYTEX_DISTRIBUTION)
    assert pytinytex.get_pdflatex_engine() == pytinytex.get_engine("pdflatex")
    assert pytinytex.get_xelatex_engine() == pytinytex.get_engine("xelatex")
    assert pytinytex.get_lualatex_engine() == pytinytex.get_engine("lualatex")


def test_get_engine_unknown(download_tinytex):  # noqa
    pytinytex.ensure_tinytex_installed(TINYTEX_DISTRIBUTION)
    with pytest.raises(ValueError, match="Unknown engine"):
        pytinytex.get_engine("notanengine")


def test_get_engine_missing_in_variation0(download_tinytex):  # noqa
    # variation 0 has no engines, so get_engine should raise RuntimeError
    pytinytex.ensure_tinytex_installed(TINYTEX_DISTRIBUTION)
    with pytest.raises(RuntimeError, match="not found"):
        pytinytex.get_engine("pdflatex")
