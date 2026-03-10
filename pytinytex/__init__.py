import asyncio
import logging
import os
import platform
import shutil
import sys
import warnings
from pathlib import Path

from .tinytex_download import download_tinytex, DEFAULT_TARGET_FOLDER  # noqa

logger = logging.getLogger("pytinytex")
logger.addHandler(logging.NullHandler())

# Known LaTeX engines included in TinyTeX
_LATEX_ENGINES = ["pdflatex", "xelatex", "lualatex", "latex"]

# Global cache
__tinytex_path = None

__all__ = [
	"download_tinytex",
	"DEFAULT_TARGET_FOLDER",
	"ensure_tinytex_installed",
	"get_tinytex_path",
	"clear_path_cache",
	"get_engine",
	"get_pdflatex_engine",
	"get_xelatex_engine",
	"get_lualatex_engine",
	"get_pdf_latex_engine",
	"get_version",
	"install",
	"remove",
	"list_installed",
	"search",
	"info",
	"update",
	"uninstall",
	"help",
	"shell",
]


# --- Package management ---

def install(package):
	"""Install a TeX Live package via tlmgr.

	Args:
		package: Package name (e.g. "booktabs", "amsmath").

	Returns:
		Tuple of (exit_code, output).
	"""
	path = get_tinytex_path()
	return _run_tlmgr_command(["install", package], path, False)

def remove(package):
	"""Remove a TeX Live package via tlmgr.

	Args:
		package: Package name to remove.

	Returns:
		Tuple of (exit_code, output).
	"""
	path = get_tinytex_path()
	return _run_tlmgr_command(["remove", package], path, False)

def list_installed():
	"""List all installed TeX Live packages.

	Returns:
		List of dicts with keys such as 'name', 'installed', 'detail'.
	"""
	path = get_tinytex_path()
	_, output = _run_tlmgr_command(["list", "--only-installed"], path, True)
	return _parse_tlmgr_list(output)

def search(query):
	"""Search for TeX Live packages matching a query.

	Args:
		query: Search term (package name or keyword).

	Returns:
		List of dicts with keys such as 'name', 'description'.
	"""
	path = get_tinytex_path()
	_, output = _run_tlmgr_command(["search", query], path, True)
	return _parse_tlmgr_list(output)

def info(package):
	"""Get detailed information about a TeX Live package.

	Args:
		package: Package name.

	Returns:
		Dict with package metadata (keys vary by package, but typically
		include 'package', 'revision', 'cat-version', 'category',
		'shortdesc', 'longdesc', 'installed', 'sizes', etc.).
	"""
	path = get_tinytex_path()
	_, output = _run_tlmgr_command(["info", package], path, True)
	return _parse_tlmgr_info(output)

def update(package="-all"):
	"""Update TeX Live packages via tlmgr.

	Args:
		package: Package name to update, or "-all" (default) to update
			everything.

	Returns:
		Tuple of (exit_code, output).
	"""
	path = get_tinytex_path()
	return _run_tlmgr_command(["update", package], path, False)

def help():
	"""Display tlmgr help text.

	Returns:
		Tuple of (exit_code, output).
	"""
	path = get_tinytex_path()
	return _run_tlmgr_command(["help"], path, False)

def shell():
	"""Open an interactive tlmgr shell session."""
	path = get_tinytex_path()
	return _run_tlmgr_command(["shell"], path, False, True)

def get_version():
	"""Return the installed TeX Live / TinyTeX version string.

	Returns:
		Version string as reported by ``tlmgr --version``.
	"""
	path = get_tinytex_path()
	_, output = _run_tlmgr_command(["--version"], path, False)
	return output.strip()

def uninstall(path=None):
	"""Remove the TinyTeX installation from disk and clear the path cache.

	Args:
		path: Directory to remove.  Defaults to the currently resolved
			TinyTeX path (or DEFAULT_TARGET_FOLDER).
	"""
	global __tinytex_path
	if not path:
		path = __tinytex_path or str(DEFAULT_TARGET_FOLDER)
	# Walk up from the bin directory to the installation root.
	# __tinytex_path typically points at e.g. .pytinytex/bin/x86_64-linux,
	# but the user likely means the top-level .pytinytex folder.
	target = Path(path)
	default = Path(DEFAULT_TARGET_FOLDER)
	if default.exists() and target.is_relative_to(default):
		target = default
	if target.exists():
		shutil.rmtree(target)
		logger.info("Removed TinyTeX installation at %s", target)
	__tinytex_path = None


# --- Path resolution ---

def get_tinytex_path(base=None):
	"""Return the resolved path to the TinyTeX bin directory.

	Args:
		base: Optional base directory to search in.  Falls back to the
			``PYTINYTEX_TINYTEX`` environment variable, then
			DEFAULT_TARGET_FOLDER.
	"""
	if __tinytex_path:
		return __tinytex_path
	path_to_resolve = DEFAULT_TARGET_FOLDER
	if base:
		path_to_resolve = base
	if os.environ.get("PYTINYTEX_TINYTEX"):
		path_to_resolve = os.environ["PYTINYTEX_TINYTEX"]

	ensure_tinytex_installed(path_to_resolve)
	return __tinytex_path

def clear_path_cache():
	"""Reset the cached TinyTeX path so the next call re-resolves it."""
	global __tinytex_path
	__tinytex_path = None


# --- Engine discovery ---

def get_engine(engine_name):
	"""Return the full path to a LaTeX engine executable.

	Args:
		engine_name: One of 'pdflatex', 'xelatex', 'lualatex', 'latex'.

	Returns:
		Absolute path to the engine executable.

	Raises:
		ValueError: If engine_name is not a known engine.
		RuntimeError: If the engine executable is not found (e.g. TinyTeX
			variation 0 which ships no engines).
	"""
	if engine_name not in _LATEX_ENGINES:
		raise ValueError(
			f"Unknown engine '{engine_name}'. "
			f"Known engines: {', '.join(_LATEX_ENGINES)}"
		)
	path = get_tinytex_path()
	suffix = ".exe" if platform.system() == "Windows" else ""
	engine_path = os.path.join(path, engine_name + suffix)
	if not os.path.isfile(engine_path):
		raise RuntimeError(
			f"Engine '{engine_name}' not found at {engine_path}. "
			"You may need a TinyTeX variation that includes it (variation >= 1)."
		)
	return engine_path

def get_pdflatex_engine():
	"""Return the full path to the pdflatex executable."""
	return get_engine("pdflatex")

def get_xelatex_engine():
	"""Return the full path to the xelatex executable."""
	return get_engine("xelatex")

def get_lualatex_engine():
	"""Return the full path to the lualatex executable."""
	return get_engine("lualatex")

def get_pdf_latex_engine():
	"""Deprecated: Use get_pdflatex_engine() instead."""
	warnings.warn(
		"get_pdf_latex_engine() is deprecated, use get_pdflatex_engine() instead",
		DeprecationWarning,
		stacklevel=2,
	)
	return get_pdflatex_engine()


# --- Installation ---

def ensure_tinytex_installed(path=None, auto_download=True, variation=1):
	"""Ensure TinyTeX is installed, optionally downloading it if missing.

	Args:
		path: Path to check for TinyTeX. Defaults to the cached path or
			DEFAULT_TARGET_FOLDER.
		auto_download: If True, download TinyTeX when it is not found.
			Defaults to True.
		variation: TinyTeX variation to download (0, 1, or 2) when
			auto_download triggers. Defaults to 1.

	Returns:
		True if TinyTeX is installed (or was successfully downloaded).

	Raises:
		RuntimeError: If TinyTeX is not found and auto_download is False.
	"""
	global __tinytex_path
	if not path:
		path = __tinytex_path or DEFAULT_TARGET_FOLDER
	try:
		__tinytex_path = _resolve_path(path)
	except RuntimeError:
		if not auto_download:
			raise
		logger.info("TinyTeX not found — downloading automatically...")
		download_tinytex(variation=variation, target_folder=path)
		__tinytex_path = _resolve_path(path)
	return True


# --- Machine-readable output parsing ---

def _parse_tlmgr_list(output):
	"""Parse tlmgr list/search machine-readable output into structured data.

	Machine-readable list lines look like:
		i collection-basic: 1 file, 4k
	or plain lines like:
		package_name - short description

	Returns a list of dicts.
	"""
	results = []
	for line in output.splitlines():
		line = line.strip()
		if not line:
			continue
		if ":" in line:
			# e.g. "i collection-basic: 12345 1 file, 4k"
			parts = line.split(":", 1)
			left = parts[0].strip()
			right = parts[1].strip() if len(parts) > 1 else ""
			installed = left.startswith("i")
			name = left.lstrip("i").strip()
			results.append({
				"name": name,
				"installed": installed,
				"detail": right,
			})
		elif " - " in line:
			name, desc = line.split(" - ", 1)
			results.append({
				"name": name.strip(),
				"description": desc.strip(),
			})
		else:
			results.append({"name": line})
	return results

def _parse_tlmgr_info(output):
	"""Parse tlmgr info machine-readable output into a dict.

	Info output is typically key-value pairs like:
		package:    booktabs
		revision:   12345
		shortdesc:  Publication quality tables
	Multi-line values (like longdesc) are continued with leading whitespace.
	"""
	info = {}
	current_key = None
	for line in output.splitlines():
		if not line.strip():
			continue
		if ":" in line and not line[0].isspace():
			key, _, value = line.partition(":")
			key = key.strip().lower()
			value = value.strip()
			info[key] = value
			current_key = key
		elif current_key and line[0].isspace():
			info[current_key] += " " + line.strip()
	return info


# --- Internal helpers ---

def _get_platform_arch():
	"""Return the TeX Live platform-architecture directory name for the current system."""
	machine = platform.machine().lower()
	system = sys.platform
	if system == "win32":
		return "windows"
	if system == "darwin":
		if machine == "arm64":
			return "universal-darwin"
		return "universal-darwin"
	# Linux
	arch_map = {
		"x86_64": "x86_64-linux",
		"amd64": "x86_64-linux",
		"aarch64": "aarch64-linux",
		"arm64": "aarch64-linux",
		"i386": "i386-linux",
		"i686": "i386-linux",
	}
	return arch_map.get(machine, machine + "-linux")

def _resolve_path(path):
	try:
		if _find_file(path, "tlmgr"):
			return path
		if os.path.isdir(os.path.join(path, "bin")):
			return _resolve_path(os.path.join(path, "bin"))
		entries = [e for e in os.listdir(path) if os.path.isdir(os.path.join(path, e))]
		# Prefer the directory matching the current platform architecture
		expected_arch = _get_platform_arch()
		if expected_arch in entries:
			return _resolve_path(os.path.join(path, expected_arch))
		if len(entries) == 1:
			return _resolve_path(os.path.join(path, entries[0]))
	except FileNotFoundError:
		pass
	raise RuntimeError(
		f"Unable to resolve TinyTeX path.\n"
		f"Tried {path}.\n"
		f"You can install TinyTeX using pytinytex.download_tinytex()"
	)

def _find_file(dir, prefix):
	"""Find a file whose stem matches *prefix* in *dir*.

	Returns the full path if found, or None.
	"""
	try:
		for s in os.listdir(dir):
			if os.path.splitext(s)[0] == prefix and os.path.isfile(os.path.join(dir, s)):
				return os.path.join(dir, s)
	except FileNotFoundError:
		pass
	return None

def _run_tlmgr_command(args, path, machine_readable=True, interactive=False):
	if machine_readable:
		if "--machine-readable" not in args:
			args.insert(0, "--machine-readable")
	tlmgr_executable = _find_file(path, "tlmgr")
	if not tlmgr_executable:
		raise RuntimeError(f"Unable to find tlmgr in {path}")
	# resolve any symlinks
	tlmgr_executable = str(Path(tlmgr_executable).resolve(True))
	args.insert(0, tlmgr_executable)
	new_env = os.environ.copy()
	creation_flag = 0x08000000 if sys.platform == "win32" else 0

	logger.debug("Running command: %s", args)
	return asyncio.run(
		_run_command(*args, stdin=interactive, env=new_env, creationflags=creation_flag)
	)


async def _read_stdout(process, output_buffer):
	"""Read lines from process.stdout and collect them."""
	logger.debug("Reading stdout from process %s", process.pid)
	try:
		while True:
			line = await process.stdout.readline()
			if not line:
				break
			line = line.decode('utf-8', errors='replace').rstrip()
			output_buffer.append(line)
			logger.info(line)
	except Exception as e:
		logger.error("Error in _read_stdout: %s", e)
	finally:
		process._transport.close()
	return await process.wait()

async def _send_stdin(process):
	"""Read user input from sys.stdin and forward it to the process."""
	logger.debug("Sending stdin to process %s", process.pid)
	loop = asyncio.get_running_loop()
	try:
		while True:
			user_input = await loop.run_in_executor(None, sys.stdin.readline)
			if not user_input:
				break
			process.stdin.write(user_input.encode('utf-8'))
			await process.stdin.drain()
	except Exception as e:
		logger.error("Error in _send_stdin: %s", e)
	finally:
		if process.stdin:
			process._transport.close()


async def _run_command(*args, stdin=False, **kwargs):
	process = await asyncio.create_subprocess_exec(
		*args,
		stdout=asyncio.subprocess.PIPE,
		stderr=asyncio.subprocess.STDOUT,
		stdin=asyncio.subprocess.PIPE if stdin else asyncio.subprocess.DEVNULL,
		**kwargs
	)

	output_buffer = []
	stdout_task = asyncio.create_task(_read_stdout(process, output_buffer))
	stdin_task = None
	if stdin:
		stdin_task = asyncio.create_task(_send_stdin(process))

	try:
		if stdin:
			logger.debug("Waiting for stdout and stdin tasks to complete")
			await asyncio.gather(stdout_task, stdin_task)
		else:
			logger.debug("Waiting for stdout task to complete")
			await stdout_task
		exit_code = await process.wait()
	except KeyboardInterrupt:
		process.terminate()
		exit_code = await process.wait()
	finally:
		stdout_task.cancel()
		if stdin_task:
			stdin_task.cancel()
	captured_output = "\n".join(output_buffer)
	if exit_code != 0:
		raise RuntimeError(f"Error running command: {captured_output}")
	return exit_code, captured_output
