import sys
import os
import asyncio
import platform

from .tinytex_download import download_tinytex, DEFAULT_TARGET_FOLDER # noqa

# Global cache
__tinytex_path = None

def update(package="-all", machine_readable=False):
	path = get_tinytex_path()
	return _run_tlmgr_command(["update", package], path, machine_readable=machine_readable)

def shell():
	path = get_tinytex_path()
	return _run_tlmgr_command(["shell"], path, machine_readable=False, interactive=True)

def help(*args, **kwargs):
	path = get_tinytex_path()
	return _run_tlmgr_command(["help"], path, *args, **kwargs)


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

def _run_tlmgr_command(args, path, machine_readable=True, interactive=False):
	if machine_readable:
		if "--machine-readable" not in args:
			args.insert(0, "--machine-readable")
	tlmgr_executable = _get_file(path, "tlmgr")
	args.insert(0, tlmgr_executable)
	new_env = os.environ.copy()
	creation_flag = 0x08000000 if sys.platform == "win32" else 0

	try:
		return asyncio.run(_run_command(*args, stdin=interactive, env=new_env, creationflags=creation_flag))
	except Exception:
		raise

async def read_stdout(process, output_buffer):
	"""Read lines from process.stdout and print them."""
	try:
		while True:
			line = await process.stdout.readline()
			if not line:  # EOF reached
				break
			line = line.decode('utf-8').rstrip()
			output_buffer.append(line)
	except Exception as e:
		print("Error in read_stdout:", e)
	finally:
		process._transport.close()
	return await process.wait()


async def send_stdin(process):
	"""Read user input from sys.stdin and send it to process.stdin."""
	loop = asyncio.get_running_loop()
	try:
		while True:
			# Offload the blocking sys.stdin.readline() call to the executor.
			user_input = await loop.run_in_executor(None, sys.stdin.readline)
			if not user_input:  # EOF (e.g. Ctrl-D)
				break
			process.stdin.write(user_input.encode('utf-8'))
			await process.stdin.drain()
	except Exception as e:
		print("Error in send_stdin:", e)
	finally:
		if process.stdin:
			process._transport.close()


async def _run_command(*args, stdin=False, **kwargs):
	# Create the subprocess with pipes for stdout and stdin.
	process = await asyncio.create_subprocess_exec(
		*args,
		stdout=asyncio.subprocess.PIPE,
		stderr=asyncio.subprocess.STDOUT,
		stdin=asyncio.subprocess.PIPE if stdin else asyncio.subprocess.DEVNULL,
		**kwargs
	)

	output_buffer = []
	# Create tasks to read stdout and send stdin concurrently.
	stdout_task = asyncio.create_task(read_stdout(process, output_buffer))
	stdin_task  = None
	if stdin:
		stdin_task  = asyncio.create_task(send_stdin(process))
	
	try:
		if stdin:
			# Wait for both tasks to complete.
			await asyncio.gather(stdout_task, stdin_task)
		else:
			# Wait for the stdout task to complete.
			await stdout_task
		# Return the process return code.
		exit_code = await process.wait()
	except KeyboardInterrupt:
		print("\nKeyboardInterrupt detected, terminating subprocess...")
		process.terminate()  # Gracefully terminate the subprocess.
		exit_code = await process.wait()
	finally:
		# Cancel tasks that are still running.
		stdout_task.cancel()
		if stdin_task:
			stdin_task.cancel()
	captured_output = "\n".join(output_buffer)
	if exit_code != 0:
		raise RuntimeError(f"Error running command: {captured_output}")
	return exit_code, captured_output


	return process.returncode
