"""TeX Live Manager (tlmgr) wrapper functions and command runner."""

import asyncio
import logging
import os
import shutil
import sys
from pathlib import Path

logger = logging.getLogger("pytinytex")

_TLMGR_SELF_UPDATE_PATTERNS = [
    "tlmgr itself needs to be updated",
    "please update tlmgr",
]


def _needs_self_update(error_message):
    """Check if a tlmgr error message indicates that tlmgr itself needs updating."""
    lower = error_message.lower()
    return any(p in lower for p in _TLMGR_SELF_UPDATE_PATTERNS)


# --- Package management ---


def install(package):
    """Install a TeX Live package via tlmgr.

    Args:
            package: Package name (e.g. "booktabs", "amsmath").

    Returns:
            Tuple of (exit_code, output).
    """
    from . import get_tinytex_path

    path = get_tinytex_path()
    result = _run_tlmgr_command(["install", package], path, False)
    _refresh_filename_db(path)
    return result


def remove(package):
    """Remove a TeX Live package via tlmgr.

    Args:
            package: Package name to remove.

    Returns:
            Tuple of (exit_code, output).
    """
    from . import get_tinytex_path

    path = get_tinytex_path()
    result = _run_tlmgr_command(["remove", package], path, False)
    _refresh_filename_db(path)
    return result


def list_installed():
    """List all installed TeX Live packages.

    Returns:
            List of dicts with keys such as 'name', 'installed', 'detail'.
    """
    from . import get_tinytex_path

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
    from . import get_tinytex_path

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
    from . import get_tinytex_path

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
    from . import get_tinytex_path

    path = get_tinytex_path()
    return _run_tlmgr_command(["update", package], path, False)


def help():
    """Display tlmgr help text.

    Returns:
            Tuple of (exit_code, output).
    """
    from . import get_tinytex_path

    path = get_tinytex_path()
    return _run_tlmgr_command(["help"], path, False)


def shell():
    """Open an interactive tlmgr shell session."""
    from . import get_tinytex_path

    path = get_tinytex_path()
    return _run_tlmgr_command(["shell"], path, False, True)


def get_version():
    """Return the installed TeX Live / TinyTeX version string.

    Returns:
            Version string as reported by ``tlmgr --version``.
    """
    from . import get_tinytex_path

    path = get_tinytex_path()
    _, output = _run_tlmgr_command(["--version"], path, False)
    return output.strip()


def uninstall(path=None):
    """Remove the TinyTeX installation from disk and clear the path cache.

    Args:
            path: Directory to remove.  Defaults to the currently resolved
                    TinyTeX path (or DEFAULT_TARGET_FOLDER).
    """
    from . import _tinytex_path, clear_path_cache
    from .tinytex_download import DEFAULT_TARGET_FOLDER

    if not path:
        path = _tinytex_path() or str(DEFAULT_TARGET_FOLDER)
    # Walk up from the bin directory to the installation root.
    # The cached path typically points at e.g. .pytinytex/bin/x86_64-linux,
    # but the user likely means the top-level .pytinytex folder.
    target = Path(path)
    default = Path(DEFAULT_TARGET_FOLDER)
    try:
        is_under_default = default.exists() and target.is_relative_to(default)
    except AttributeError:
        # Path.is_relative_to() was added in Python 3.9
        try:
            target.relative_to(default)
            is_under_default = default.exists()
        except ValueError:
            is_under_default = False
    if is_under_default:
        target = default
    if target.exists():
        shutil.rmtree(target)
        logger.info("Removed TinyTeX installation at %s", target)
    clear_path_cache()


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
            results.append(
                {
                    "name": name,
                    "installed": installed,
                    "detail": right,
                }
            )
        elif " - " in line:
            name, desc = line.split(" - ", 1)
            results.append(
                {
                    "name": name.strip(),
                    "description": desc.strip(),
                }
            )
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


def _refresh_filename_db(path):
    """Run mktexlsr to refresh the TeX filename database after install/remove."""
    from . import _find_file

    mktexlsr = _find_file(path, "mktexlsr")
    if not mktexlsr:
        logger.debug("mktexlsr not found, skipping filename database refresh")
        return
    mktexlsr = str(Path(mktexlsr).resolve(True))
    new_env = os.environ.copy()
    creation_flag = 0x08000000 if sys.platform == "win32" else 0
    logger.debug("Refreshing TeX filename database: %s", mktexlsr)
    try:
        asyncio.run(_run_command(mktexlsr, env=new_env, creationflags=creation_flag))
    except RuntimeError:
        logger.debug("mktexlsr failed, continuing anyway")


# --- Command runner ---


def _run_tlmgr_command(
    args, path, machine_readable=True, interactive=False, _retried=False
):
    original_args = list(args)  # save before mutation
    from . import _find_file

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
    try:
        return asyncio.run(
            _run_command(
                *args, stdin=interactive, env=new_env, creationflags=creation_flag
            )
        )
    except RuntimeError as e:
        is_self_update = "update" in original_args and "--self" in original_args
        if not _retried and not is_self_update and _needs_self_update(str(e)):
            logger.warning(
                "tlmgr requires self-update. Running 'tlmgr update --self'..."
            )
            _run_tlmgr_command(
                ["update", "--self"], path, machine_readable=False, _retried=True
            )
            return _run_tlmgr_command(
                original_args, path, machine_readable, interactive, _retried=True
            )
        raise


async def _read_stdout(process, output_buffer):
    """Read lines from process.stdout and collect them."""
    logger.debug("Reading stdout from process %s", process.pid)
    try:
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            line = line.decode("utf-8", errors="replace").rstrip()
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
            process.stdin.write(user_input.encode("utf-8"))
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
        **kwargs,
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
