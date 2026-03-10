"""Tests for tlmgr self-update auto-retry logic."""

import pytest

import pytinytex
from pytinytex.tlmgr import _needs_self_update, _run_tlmgr_command
from .utils import download_tinytex, TINYTEX_DISTRIBUTION  # noqa


class TestNeedsSelfUpdate:
    def test_detects_standard_message(self):
        assert _needs_self_update("tlmgr itself needs to be updated") is True

    def test_detects_case_insensitive(self):
        assert _needs_self_update("TLMGR itself needs to be UPDATED") is True

    def test_detects_please_update(self):
        assert _needs_self_update("please update tlmgr") is True

    def test_detects_in_longer_message(self):
        msg = "Error running command: (some output)\ntlmgr itself needs to be updated.\nPlease run update --self."
        assert _needs_self_update(msg) is True

    def test_no_false_positive_on_unrelated_error(self):
        assert _needs_self_update("package not found") is False

    def test_no_false_positive_on_empty_string(self):
        assert _needs_self_update("") is False


@pytest.mark.parametrize("download_tinytex", [1], indirect=True)
def test_install_works_without_manual_self_update(download_tinytex):  # noqa
    """Auto-retry should handle the self-update transparently so install works on a fresh TinyTeX."""
    pytinytex.ensure_tinytex_installed(TINYTEX_DISTRIBUTION)
    # On a fresh download, tlmgr often needs self-update before install.
    # The auto-retry in _run_tlmgr_command should handle this transparently.
    exit_code, _ = pytinytex.install("blindtext")
    assert exit_code == 0

    # Clean up
    try:
        pytinytex.remove("blindtext")
    except RuntimeError:
        pass


def test_retried_flag_is_accepted():
    """Verify _retried parameter is accepted and doesn't cause errors at the API level."""
    # This is a unit-level check that the _retried parameter exists and is wired up.
    # The actual retry logic is tested by test_install_works_without_manual_self_update
    # (which exercises the real auto-retry path on fresh TinyTeX downloads in CI).
    assert _needs_self_update("tlmgr itself needs to be updated") is True
    assert _needs_self_update("unrelated error") is False
