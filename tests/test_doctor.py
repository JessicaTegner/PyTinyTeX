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


@pytest.mark.parametrize("download_tinytex", [1], indirect=True)
def test_doctor_reports_healthy(download_tinytex):  # noqa
	"""Variation 1 should report a fully healthy installation."""
	pytinytex.ensure_tinytex_installed(TINYTEX_DISTRIBUTION)
	result = pytinytex.doctor()
	# All non-engine checks should pass
	core_checks = [c for c in result.checks if not c.name.startswith("Engine:")]
	for check in core_checks:
		assert check.passed is True, "Check '%s' failed: %s" % (check.name, check.message)


@pytest.mark.parametrize("download_tinytex", [1], indirect=True)
def test_doctor_path_on_path(download_tinytex):  # noqa
	"""After ensure_tinytex_installed, PATH check should pass."""
	pytinytex.ensure_tinytex_installed(TINYTEX_DISTRIBUTION)
	result = pytinytex.doctor()
	path_check = next(c for c in result.checks if c.name == "PATH configured")
	assert path_check.passed is True


@pytest.mark.parametrize("download_tinytex", [1], indirect=True)
def test_doctor_tlmgr_functional(download_tinytex):  # noqa
	"""tlmgr should be able to report its version."""
	pytinytex.ensure_tinytex_installed(TINYTEX_DISTRIBUTION)
	result = pytinytex.doctor()
	func_check = next(c for c in result.checks if c.name == "tlmgr functional")
	assert func_check.passed is True
	assert len(func_check.message) > 0


@pytest.mark.parametrize("download_tinytex", [1], indirect=True)
def test_doctor_consistent_across_runs(download_tinytex):  # noqa
	"""Doctor should return the same results on consecutive runs."""
	pytinytex.ensure_tinytex_installed(TINYTEX_DISTRIBUTION)
	result1 = pytinytex.doctor()
	result2 = pytinytex.doctor()
	assert result1.healthy == result2.healthy
	assert len(result1.checks) == len(result2.checks)
	for c1, c2 in zip(result1.checks, result2.checks):
		assert c1.name == c2.name
		assert c1.passed == c2.passed


def test_doctor_without_tinytex():
	"""Doctor should report unhealthy when TinyTeX is not installed."""
	pytinytex.clear_path_cache()
	# Point to a nonexistent path
	import os
	old_env = os.environ.get("PYTINYTEX_TINYTEX")
	os.environ["PYTINYTEX_TINYTEX"] = "/nonexistent/path/tinytex"
	try:
		result = pytinytex.doctor()
		assert result.healthy is False
		assert len(result.checks) >= 1
		install_check = result.checks[0]
		assert install_check.name == "TinyTeX installed"
		assert install_check.passed is False
	finally:
		if old_env is not None:
			os.environ["PYTINYTEX_TINYTEX"] = old_env
		else:
			os.environ.pop("PYTINYTEX_TINYTEX", None)
		pytinytex.clear_path_cache()
