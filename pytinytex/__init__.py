import sys
import subprocess
import glob
import os

from .tinytex_download import download_tinytex

# Global cache
__tinytex_path = getattr(os.environ, "PYTINYTEX_TINYTEX", None)

def update(package="-all"):
	path = get_tinytex_path()
	try:
		code, stdout,stderr = _run_tlmgr_command(["update", package], path, False)
		return True
	except RuntimeError:
		raise
		return False


def get_tinytex_path(base="."):
	global __tinytex_path
	if __tinytex_path is not None:
		return __tinytex_path
	
	ensure_tinytex_installed(base)
	if __tinytex_path is None:
		raise RuntimeError("TinyTeX doesn't seem to be installed. You can install TinyTeX with pytinytex.download_tinytex().")
	return __tinytex_path

def ensure_tinytex_installed(path="."):
	global __tinytex_path
	error_path = None
	try:
		if __tinytex_path is not None:
			error_path = __tinytex_path
			__tinytex_path = _resolve_path(__tinytex_path)
		else:
			error_path = path
			__tinytex_path = _resolve_path(path)
		return True
	except RuntimeError as e:
		__tinytex_path = None
		raise RuntimeError("Unable to resolve TinyTeX path. Got as far as {}".format(error_path))
		return False

def _resolve_path(path="."):
	while True:
		if _check_file(path, "tlmgr"):
			return path
		new_path = ""
		list_dir = os.listdir(path)
		if "bin" in list_dir:
			new_path = _jump_folder(os.path.join(path, "bin"))
		elif "tinytex" in list_dir:
			new_path = _jump_folder(os.path.join(path, "tinytex"))
		elif ".tinytex" in list_dir:
			new_path = _jump_folder(os.path.join(path, ".tinytex"))
		else:
			new_path = _jump_folder(path)
		if new_path is not None:
			path = new_path

def _jump_folder(path):
	dir_index = os.listdir(path)
	if len(dir_index) == 1:
		if os.path.isdir(os.path.join(path, dir_index[0])):
			return _resolve_path(os.path.join(path, dir_index[0]))
	else:
		for directory in dir_index:
			if os.path.isdir(os.path.join(path, directory)):
				try:
					return _resolve_path(os.path.join(path, directory))
				except RuntimeError:
					pass
	raise RuntimeError("Unable to resolve TinyTeX path.")

def _check_file(dir, prefix):
	try:
		for s in os.listdir(dir):
			if os.path.splitext(s)[0] == prefix and os.path.isfile(os.path.join(dir, s)):
				return True
	except FileNotFoundError:
		raise RuntimeError("Unable to resolve path.")
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
	if not (p.returncode is None):
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
