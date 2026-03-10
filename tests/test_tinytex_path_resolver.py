import os
import warnings

import pytest

import pytinytex
from .utils import download_tinytex, TINYTEX_DISTRIBUTION  # noqa


def test_failing_resolver(download_tinytex):  # noqa
    with pytest.raises(RuntimeError):
        pytinytex._resolve_path("failing")
    with pytest.raises(RuntimeError):
        pytinytex.ensure_tinytex_installed("failing")


def test_successful_resolver(download_tinytex):  # noqa
    pytinytex.ensure_tinytex_installed(TINYTEX_DISTRIBUTION)
    assert isinstance(pytinytex.__tinytex_path, str)
    assert os.path.isdir(pytinytex.__tinytex_path)


def test_get_tinytex_path(download_tinytex):  # noqa
    pytinytex.ensure_tinytex_installed(TINYTEX_DISTRIBUTION)
    assert pytinytex.__tinytex_path == pytinytex.get_tinytex_path(TINYTEX_DISTRIBUTION)


def test_clear_path_cache(download_tinytex):  # noqa
    pytinytex.ensure_tinytex_installed(TINYTEX_DISTRIBUTION)
    assert pytinytex.__tinytex_path is not None
    pytinytex.clear_path_cache()
    assert pytinytex.__tinytex_path is None


@pytest.mark.parametrize("download_tinytex", [1], indirect=True)
def test_get_pdflatex_engine(download_tinytex):  # noqa
    pytinytex.ensure_tinytex_installed(TINYTEX_DISTRIBUTION)
    assert isinstance(pytinytex.get_pdflatex_engine(), str)
    assert os.path.isfile(pytinytex.get_pdflatex_engine())


@pytest.mark.parametrize("download_tinytex", [1], indirect=True)
def test_get_pdf_latex_engine_deprecated(download_tinytex):  # noqa
    pytinytex.ensure_tinytex_installed(TINYTEX_DISTRIBUTION)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = pytinytex.get_pdf_latex_engine()
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "deprecated" in str(w[0].message).lower()
    assert result == pytinytex.get_pdflatex_engine()
