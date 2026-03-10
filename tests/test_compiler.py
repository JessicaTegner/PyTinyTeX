"""Tests for the compile() function."""

import os
import tempfile

import pytest

import pytinytex
from .utils import download_tinytex, TINYTEX_DISTRIBUTION  # noqa


@pytest.fixture
def simple_tex():
	"""Create a simple .tex file in a temp directory."""
	with tempfile.TemporaryDirectory() as tmpdir:
		tex_path = os.path.join(tmpdir, "test.tex")
		with open(tex_path, "w") as f:
			f.write(r"""\documentclass{article}
\begin{document}
Hello, World!
\end{document}
""")
		yield tex_path


@pytest.fixture
def bad_tex():
	"""Create a .tex file with errors."""
	with tempfile.TemporaryDirectory() as tmpdir:
		tex_path = os.path.join(tmpdir, "bad.tex")
		with open(tex_path, "w") as f:
			f.write(r"""\documentclass{article}
\begin{document}
\badcommand
\end{document}
""")
		yield tex_path


@pytest.fixture
def missing_pkg_tex():
	"""Create a .tex file that requires a missing package."""
	with tempfile.TemporaryDirectory() as tmpdir:
		tex_path = os.path.join(tmpdir, "missing.tex")
		with open(tex_path, "w") as f:
			f.write(r"""\documentclass{article}
\usepackage{nonexistent_pkg_xyz_123}
\begin{document}
Hello
\end{document}
""")
		yield tex_path


@pytest.mark.parametrize("download_tinytex", [1], indirect=True)
def test_compile_simple(download_tinytex, simple_tex):  # noqa
	pytinytex.ensure_tinytex_installed(TINYTEX_DISTRIBUTION)
	result = pytinytex.compile(simple_tex)
	assert isinstance(result, pytinytex.CompileResult)
	assert result.success is True
	assert result.pdf_path is not None
	assert os.path.isfile(result.pdf_path)
	assert result.engine == "pdflatex"
	assert result.runs == 1


@pytest.mark.parametrize("download_tinytex", [1], indirect=True)
def test_compile_multi_run(download_tinytex, simple_tex):  # noqa
	pytinytex.ensure_tinytex_installed(TINYTEX_DISTRIBUTION)
	result = pytinytex.compile(simple_tex, num_runs=2)
	assert result.success is True
	assert result.runs == 2


@pytest.mark.parametrize("download_tinytex", [1], indirect=True)
def test_compile_output_dir(download_tinytex, simple_tex):  # noqa
	pytinytex.ensure_tinytex_installed(TINYTEX_DISTRIBUTION)
	with tempfile.TemporaryDirectory() as outdir:
		result = pytinytex.compile(simple_tex, output_dir=outdir)
		assert result.success is True
		assert outdir in result.pdf_path


@pytest.mark.parametrize("download_tinytex", [1], indirect=True)
def test_compile_with_errors(download_tinytex, bad_tex):  # noqa
	pytinytex.ensure_tinytex_installed(TINYTEX_DISTRIBUTION)
	result = pytinytex.compile(bad_tex)
	# pdflatex in nonstopmode may still produce a PDF despite errors
	assert isinstance(result, pytinytex.CompileResult)
	assert result.log_path is not None


@pytest.mark.parametrize("download_tinytex", [1], indirect=True)
def test_compile_missing_package(download_tinytex, missing_pkg_tex):  # noqa
	pytinytex.ensure_tinytex_installed(TINYTEX_DISTRIBUTION)
	result = pytinytex.compile(missing_pkg_tex, auto_install=False)
	# Should fail due to missing package
	assert result.success is False


def test_compile_nonexistent_file():
	with pytest.raises(FileNotFoundError):
		pytinytex.compile("/nonexistent/path/file.tex")


def test_compile_invalid_engine():
	with tempfile.TemporaryDirectory() as tmpdir:
		tex_path = os.path.join(tmpdir, "test.tex")
		with open(tex_path, "w") as f:
			f.write("\\documentclass{article}\\begin{document}Hi\\end{document}")
		with pytest.raises(ValueError):
			pytinytex.compile(tex_path, engine="badengine")


def test_compile_result_fields():
	result = pytinytex.CompileResult(success=True, engine="xelatex", runs=2)
	assert result.success is True
	assert result.engine == "xelatex"
	assert result.runs == 2
	assert result.errors == []
	assert result.warnings == []
	assert result.installed_packages == []
	assert result.output == ""
	assert result.pdf_path is None
