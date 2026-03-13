"""LaTeX compilation with optional auto-install of missing packages."""

from __future__ import annotations

import dataclasses
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

from .log_parser import LogEntry, ParsedLog, parse_log

logger = logging.getLogger("pytinytex")


@dataclasses.dataclass
class CompileResult:
    """Result of a LaTeX compilation."""

    success: bool
    pdf_path: Optional[str] = None
    log_path: Optional[str] = None
    engine: str = "pdflatex"
    runs: int = 0
    errors: List[LogEntry] = dataclasses.field(default_factory=list)
    warnings: List[LogEntry] = dataclasses.field(default_factory=list)
    installed_packages: List[str] = dataclasses.field(default_factory=list)
    output: str = ""


def compile(
    tex_file,
    engine="pdflatex",
    output_dir=None,
    num_runs=1,
    auto_install=False,
    max_install_attempts=3,
    extra_args=None,
):
    """Compile a .tex file to PDF.

    Args:
            tex_file: Path to the .tex file to compile.
            engine: LaTeX engine to use ('pdflatex', 'xelatex', 'lualatex',
                    'latex'). Defaults to 'pdflatex'.
            output_dir: Directory for output files. Defaults to the same
                    directory as the .tex file.
            num_runs: Number of compilation passes. Use 2+ for cross-references
                    and TOC. Defaults to 1.
            auto_install: If True, automatically install missing packages via
                    tlmgr and retry compilation. Defaults to False.
            max_install_attempts: Maximum number of install-and-retry cycles
                    when auto_install is True. Defaults to 3.
            extra_args: Additional command-line arguments to pass to the engine.

    Returns:
            CompileResult with compilation outcome, parsed errors/warnings,
            and list of any auto-installed packages.

    Raises:
            FileNotFoundError: If tex_file does not exist.
            ValueError: If engine is not a known LaTeX engine.
    """
    # Import here to avoid circular imports
    from . import get_engine
    from .tlmgr import install

    tex_path = Path(tex_file).resolve()
    if not tex_path.exists():
        raise FileNotFoundError(f"TeX file not found: {tex_path}")

    engine_path = get_engine(engine)

    if output_dir is None:
        output_dir = str(tex_path.parent)
    else:
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    stem = tex_path.stem
    pdf_path = os.path.join(output_dir, stem + ".pdf")
    log_path = os.path.join(output_dir, stem + ".log")

    result = CompileResult(
        success=False,
        pdf_path=pdf_path,
        log_path=log_path,
        engine=engine,
    )

    all_installed = []

    for attempt in range(max_install_attempts + 1):
        # Build the command
        cmd = [engine_path, "-interaction=nonstopmode"]
        if output_dir:
            cmd.append(f"-output-directory={output_dir}")
        if extra_args:
            cmd.extend(extra_args)
        cmd.append(str(tex_path))

        # Run for num_runs passes
        output_lines = []
        exit_code = 0
        creation_flag = 0x08000000 if sys.platform == "win32" else 0

        for run in range(num_runs):
            logger.debug("Compilation pass %d/%d: %s", run + 1, num_runs, cmd)
            try:
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    creationflags=creation_flag,
                )
                stdout = proc.stdout.decode("utf-8", errors="replace")
                stderr = proc.stderr.decode("utf-8", errors="replace")
                output_lines.append(stdout)
                if stderr:
                    output_lines.append(stderr)
                exit_code = proc.returncode
            except Exception as e:
                output_lines.append(str(e))
                exit_code = 1
                break

        result.runs = num_runs
        result.output = "\n".join(output_lines)

        # Parse the log file if it exists
        parsed = ParsedLog()
        if os.path.isfile(log_path):
            try:
                with open(log_path, encoding="utf-8", errors="replace") as f:
                    log_content = f.read()
                parsed = parse_log(log_content)
            except Exception as e:
                logger.warning("Failed to parse log file: %s", e)

        result.errors = parsed.errors
        result.warnings = parsed.warnings
        result.success = exit_code == 0 and os.path.isfile(pdf_path)

        # Auto-install missing packages if needed
        if auto_install and parsed.missing_packages and attempt < max_install_attempts:
            newly_installed = []
            for pkg in parsed.missing_packages:
                if pkg in all_installed:
                    continue
                logger.info("Auto-installing missing package: %s", pkg)
                try:
                    install(pkg)
                    newly_installed.append(pkg)
                    all_installed.append(pkg)
                except RuntimeError as e:
                    logger.warning("Failed to install '%s': %s", pkg, e)

            if not newly_installed:
                # Nothing new could be installed, no point retrying
                break

            logger.info("Retrying compilation after installing: %s", newly_installed)
            continue

        # No auto-install needed or not enabled
        break

    result.installed_packages = all_installed
    return result


