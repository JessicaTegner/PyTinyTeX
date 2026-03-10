import os

import pytest

import pytinytex
from .utils import TINYTEX_DISTRIBUTION, cleanup


def test_successful_download():
    try:
        pytinytex.download_tinytex(
            variation=0, target_folder=TINYTEX_DISTRIBUTION, download_folder="tests"
        )
        assert os.path.isdir(TINYTEX_DISTRIBUTION)
        assert os.path.isdir(os.path.join(TINYTEX_DISTRIBUTION, "bin"))
    finally:
        cleanup()


def test_successful_download_specific_version():
    try:
        pytinytex.download_tinytex(
            variation=0,
            version="2024.12",
            target_folder=TINYTEX_DISTRIBUTION,
            download_folder="tests",
        )
        assert os.path.isdir(TINYTEX_DISTRIBUTION)
        assert os.path.isdir(os.path.join(TINYTEX_DISTRIBUTION, "bin"))
    finally:
        cleanup()


def test_failing_download_invalid_variation():
    with pytest.raises(RuntimeError, match="Invalid TinyTeX variation 999."):
        pytinytex.download_tinytex(variation=999)


def test_failing_download_invalid_version():
    with pytest.raises(RuntimeError, match="Invalid TinyTeX version invalid."):
        pytinytex.download_tinytex(version="invalid")
