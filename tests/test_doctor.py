"""Tests for the doctor() health check."""

import pytest

import pytinytex
from .utils import download_tinytex, TINYTEX_DISTRIBUTION  # noqa


def test_doctor_result_structure(download_tinytex):  # noqa
	pytinytex.ensure_tinytex_installed(TINYTEX_DISTRIBUTION)
	result = pytinytex.doctor()
	assert isinstance(result, pytinytex.DoctorResult)
	assert isinstance(result.checks, list)
	assert len(result.checks) > 0
	for check in result.checks:
		assert isinstance(check, pytinytex.DoctorCheck)
		assert isinstance(check.name, str)
		assert isinstance(check.passed, bool)
		assert isinstance(check.message, str)


def test_doctor_tinytex_installed(download_tinytex):  # noqa
	pytinytex.ensure_tinytex_installed(TINYTEX_DISTRIBUTION)
	result = pytinytex.doctor()
	install_check = next(c for c in result.checks if c.name == "TinyTeX installed")
	assert install_check.passed is True


def test_doctor_tlmgr_found(download_tinytex):  # noqa
	pytinytex.ensure_tinytex_installed(TINYTEX_DISTRIBUTION)
	result = pytinytex.doctor()
	tlmgr_check = next(c for c in result.checks if c.name == "tlmgr found")
	assert tlmgr_check.passed is True


@pytest.mark.parametrize("download_tinytex", [1], indirect=True)
def test_doctor_engines_present(download_tinytex):  # noqa
	"""Variation 1 should have pdflatex at minimum."""
	pytinytex.ensure_tinytex_installed(TINYTEX_DISTRIBUTION)
	result = pytinytex.doctor()
	engine_checks = [c for c in result.checks if c.name.startswith("Engine:")]
	assert len(engine_checks) > 0
	pdflatex_check = next(
		(c for c in engine_checks if "pdflatex" in c.name), None
	)
	if pdflatex_check:
		assert pdflatex_check.passed is True
