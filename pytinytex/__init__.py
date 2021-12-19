import glob
import os

from .tinytex_download import download_tinytex

# Global cache
__tinytex_path = None

def get_tinytex_path(base="."):
	global __tinytex_path
	if __tinytex_path is not None:
		return __tinytex_path
	
	ensure_tinytex_installed(path)
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
		else:
			new_path = _jump_folder(path)
		if new_path is not None:
			path = new_path

def _jump_folder(path):
	print(path)
	dir_index = os.listdir(path)
	if len(dir_index) == 1:
		if os.path.isdir(os.path.join(path, dir_index[0])):
			return os.path.join(path, dir_index[0])
	else:
		for directory in dir_index:
			if os.path.isdir(os.path.join(path, directory)):
				return os.path.join(path, directory)
	raise RuntimeError("Unable to resolve TinyTeX path.")

def _check_file(dir, prefix):
	try:
		for s in os.listdir(dir):
			if os.path.splitext(s)[0] == prefix and os.path.isfile(os.path.join(dir, s)):
				return True
	except FileNotFoundError:
		raise RuntimeError("Unable to resolve TinyTeX path.")
	return False
