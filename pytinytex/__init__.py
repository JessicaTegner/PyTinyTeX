import sys
import os
import subprocess
import platform
from pathlib import Path

from .tinytex_download import download_tinytex, DEFAULT_TARGET_FOLDER # noqa

# Global cache
__tinytex_path = None

def update(package="-all"):
	path = get_tinytex_path()
	try:
		code, stdout,stderr = _run_tlmgr_command(["update", package], path, False)
		return True
	except RuntimeError:
		raise
		return False


def get_tinytex_path(base=None):
	if __tinytex_path:
		return __tinytex_path
	path_to_resolve = DEFAULT_TARGET_FOLDER
	if base:
		path_to_resolve = base
	if os.environ.get("PYTINYTEX_TINYTEX", None):
		path_to_resolve = os.environ["PYTINYTEX_TINYTEX"]
	
	ensure_tinytex_installed(path_to_resolve)
	return __tinytex_path

def get_pdf_latex_engine():
	if platform.system() == "Windows":
		return os.path.join(get_tinytex_path(), "pdflatex.exe")
	else:
		return os.path.join(get_tinytex_path(), "pdflatex")


def ensure_tinytex_installed(path=None):
	global __tinytex_path
	if not path:
		path = __tinytex_path
	__tinytex_path = _resolve_path(path)
	return True

def _resolve_path(path):
	try:
		if _check_file(path, "tlmgr"):
			return path
		# if there is a bin folder, go into it
		if os.path.isdir(os.path.join(path, "bin")):
			return _resolve_path(os.path.join(path, "bin"))
		# if there is only 1 folder in the path, go into it
		if len(os.listdir(path)) == 1:
			return _resolve_path(os.path.join(path, os.listdir(path)[0]))
	except FileNotFoundError:
		pass
	raise RuntimeError(f"Unable to resolve TinyTeX path.\nTried {path}.\nYou can install TinyTeX using pytinytex.download_tinytex()")

def _check_file(dir, prefix):
	try:
		for s in os.listdir(dir):
			if os.path.splitext(s)[0] == prefix and os.path.isfile(os.path.join(dir, s)):
				return True
	except FileNotFoundError:
		return False

def _get_file(dir, prefix):
	try:
		for s in os.listdir(dir):
			if os.path.splitext(s)[0] == prefix and os.path.isfile(os.path.join(dir, s)):
				return os.path.join(dir, s)
	except FileNotFoundError:
		raise RuntimeError("Unable to find {}.".format(prefix))

def _run_tlmgr_command(args, path, machine_readable=True):
	if machine_readable:
		if "--machine-readable" not in args:
			args.insert(0, "--machine-readable")
	tlmgr_executable = _get_file(path, "tlmgr")
	args.insert(0, tlmgr_executable)
	new_env = os.environ.copy()
	creation_flag = 0x08000000 if sys.platform == "win32" else 0 # set creation flag to not open TinyTeX in new console on windows
	p = subprocess.Popen(
		args,
		stdout=subprocess.PIPE,
		stderr=subprocess.PIPE,
		env=new_env,
		creationflags=creation_flag)
	# something else than 'None' indicates that the process already terminated
	if p.returncode is not None:
		raise RuntimeError(
			'TLMGR died with exitcode "%s" before receiving input: %s' % (p.returncode,
																		   p.stderr.read())
		)
	
	stdout, stderr = p.communicate()
	
	try:
		stdout = stdout.decode("utf-8")
	except UnicodeDecodeError:
		raise RuntimeError("Unable to decode stdout from TinyTeX")
	
	try:
		stderr = stderr.decode("utf-8")
	except UnicodeDecodeError:
		raise RuntimeError("Unable to decode stderr from TinyTeX")
	
	if stderr == "" and p.returncode == 0:
		return p.returncode, stdout, stderr
	else:
		raise RuntimeError("TLMGR died with the following error:\n{0}".format(stderr.strip()))
		return p.returncode, stdout, stderr
