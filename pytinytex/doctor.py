"""TinyTeX installation health check."""

import dataclasses
import os
import platform
from typing import List


@dataclasses.dataclass
class DoctorCheck:
	"""A single health check result."""
	name: str
	passed: bool
	message: str

@dataclasses.dataclass
class DoctorResult:
	"""Overall health check result."""
	healthy: bool
	checks: List[DoctorCheck] = dataclasses.field(default_factory=list)


def doctor():
	"""Check the health of the TinyTeX installation.

	Returns:
		DoctorResult with individual check outcomes.
	"""
	from . import get_tinytex_path, _LATEX_ENGINES, _find_file, _is_on_path
	from .tlmgr import get_version

	checks = []

	# 1. TinyTeX installed?
	try:
		path = get_tinytex_path()
		checks.append(DoctorCheck("TinyTeX installed", True, "Found at %s" % path))
	except RuntimeError as e:
		checks.append(DoctorCheck("TinyTeX installed", False, str(e)))
		return DoctorResult(healthy=False, checks=checks)

	# 2. TinyTeX on PATH?
	if _is_on_path(path):
		checks.append(DoctorCheck("PATH configured", True, "TinyTeX bin directory is on PATH"))
	else:
		checks.append(DoctorCheck("PATH configured", False,
			"TinyTeX bin directory (%s) is not on PATH" % path))

	# 3. tlmgr available?
	tlmgr = _find_file(path, "tlmgr")
	if tlmgr:
		checks.append(DoctorCheck("tlmgr found", True, tlmgr))
	else:
		checks.append(DoctorCheck("tlmgr found", False, "tlmgr not found in %s" % path))

	# 4. tlmgr functional?
	if tlmgr:
		try:
			version = get_version()
			checks.append(DoctorCheck("tlmgr functional", True, version.split("\n")[0]))
		except RuntimeError as e:
			checks.append(DoctorCheck("tlmgr functional", False, str(e)))

	# 5. Engines available?
	suffix = ".exe" if platform.system() == "Windows" else ""
	for engine_name in _LATEX_ENGINES:
		engine_path = os.path.join(path, engine_name + suffix)
		if os.path.isfile(engine_path):
			checks.append(DoctorCheck("Engine: %s" % engine_name, True, engine_path))
		else:
			checks.append(DoctorCheck("Engine: %s" % engine_name, False,
				"Not found (requires TinyTeX variation >= 1)"))

	healthy = all(c.passed for c in checks)
	return DoctorResult(healthy=healthy, checks=checks)
