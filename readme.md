# PyTinyTeX

![Build Status](https://github.com/JessicaTegner/PyTinyTeX/actions/workflows/ci.yaml/badge.svg)
[![PyPI version](https://badge.fury.io/py/pytinytex.svg)](https://pypi.python.org/pypi/PyTinyTeX/)
[![Development Status](https://img.shields.io/pypi/status/PyTinyTeX.svg)](https://pypi.python.org/pypi/PyTinyTeX/)
[![Python version](https://img.shields.io/pypi/pyversions/PyTinyTeX.svg)](https://pypi.python.org/pypi/PyTinyTeX/)
![License](https://img.shields.io/pypi/l/PyTinyTeX.svg)

The easiest way to go from `.tex` to `.pdf` in Python. PyTinyTeX wraps [TinyTeX](https://yihui.org/tinytex) — a lightweight, cross-platform, portable LaTeX distribution based on TeX Live — and gives you compilation, package management, and diagnostics from Python or the command line.

```python
import pytinytex

pytinytex.download_tinytex()
result = pytinytex.compile("paper.tex", auto_install=True)
print(result.pdf_path)  # paper.pdf
```

No system-wide TeX installation required. Missing packages are installed automatically.

---

## Installation

```
pip install pytinytex
```

Python 3.8+ on Linux, macOS, and Windows.

## Quick start

### 1. Get TinyTeX

```python
import pytinytex

# Download the default variation (variation 1: ~90 common LaTeX packages)
pytinytex.download_tinytex()

# Or pick a variation:
#   0 — infrastructure only, no packages
#   1 — common packages (default)
#   2 — extended package set
pytinytex.download_tinytex(variation=2)

# Track download progress
pytinytex.download_tinytex(progress_callback=lambda downloaded, total: print(f"{downloaded}/{total} bytes"))
```

### 2. Compile a document

```python
result = pytinytex.compile("paper.tex")

if result.success:
    print("PDF at:", result.pdf_path)
else:
    for error in result.errors:
        print(f"  ! {error.message} (line {error.line})")
```

Multi-pass compilation for cross-references and TOC:

```python
result = pytinytex.compile("paper.tex", num_runs=2)
```

Choose your engine:

```python
result = pytinytex.compile("paper.tex", engine="xelatex")
result = pytinytex.compile("paper.tex", engine="lualatex")
```

### 3. Auto-install missing packages

The killer feature: if your document needs a package you don't have, PyTinyTeX can find it, install it, and retry — all in one call:

```python
result = pytinytex.compile("paper.tex", auto_install=True)
print(result.installed_packages)  # e.g. ['booktabs', 'pgf']
```

## Package management

Full access to the TeX Live package manager (tlmgr):

```python
import pytinytex

pytinytex.install("booktabs")
pytinytex.remove("booktabs")

# List installed packages (returns list of dicts)
for pkg in pytinytex.list_installed():
    print(pkg["name"])

# Search for packages
pytinytex.search("amsmath")

# Detailed package info (returns dict)
pytinytex.info("booktabs")

# Update all packages
pytinytex.update()

# TeX Live version
pytinytex.get_version()
```

## Engine discovery

Locate LaTeX engine executables (variation 1+):

```python
pytinytex.get_engine("pdflatex")   # full path to the executable
pytinytex.get_engine("xelatex")
pytinytex.get_engine("lualatex")

# Convenience shortcuts
pytinytex.get_pdflatex_engine()
pytinytex.get_xelatex_engine()
pytinytex.get_lualatex_engine()
```

## LaTeX log parser

Parse any LaTeX `.log` file into structured data — useful even outside PyTinyTeX:

```python
from pytinytex import parse_log

with open("paper.log") as f:
    parsed = parse_log(f.read())

for error in parsed.errors:
    print(f"{error.file}:{error.line}: {error.message}")

for warning in parsed.warnings:
    print(warning.message)

# Missing .sty packages detected automatically
print(parsed.missing_packages)  # e.g. ['tikz', 'booktabs']
```

## Health check

Diagnose your TinyTeX installation:

```python
result = pytinytex.doctor()
for check in result.checks:
    status = "PASS" if check.passed else "FAIL"
    print(f"  [{status}] {check.name}: {check.message}")
```

Checks: TinyTeX installed, PATH configured, tlmgr functional, engine availability.

## Command-line interface

Every feature is also available from the terminal:

```bash
# Download TinyTeX
pytinytex download
pytinytex download --variation 2

# Compile a document
pytinytex compile paper.tex
pytinytex compile paper.tex --engine xelatex --runs 2 --auto-install

# Package management
pytinytex install booktabs
pytinytex remove booktabs
pytinytex list
pytinytex search amsmath
pytinytex info booktabs
pytinytex update

# Diagnostics
pytinytex doctor
pytinytex version

# Also works as a Python module
python -m pytinytex doctor
```

## Integrating with pypandoc

PyTinyTeX pairs naturally with [pypandoc](https://pypi.org/project/pypandoc/) for converting Markdown, HTML, and other formats to PDF:

```python
import pytinytex
import pypandoc

pdflatex_path = pytinytex.get_pdflatex_engine()
pypandoc.convert_file("input.md", "pdf", outputfile="output.pdf",
                      extra_args=["--pdf-engine", pdflatex_path])
```

## Uninstalling TinyTeX

```python
pytinytex.uninstall()  # removes the TinyTeX directory
```

Or from the CLI:

```bash
pytinytex uninstall
```

## Contributing

Contributions are welcome. When opening a PR, please keep the following guidelines in mind:

1. Before implementing, please open an issue for discussion.
2. Make sure you have tests for the new logic.
3. Add yourself to contributors in this README unless you are already there.

## Contributors

* [Jessica Tegner](https://github.com/JessicaTegner) — Maintainer and original creator of PyTinyTeX

## License

PyTinyTeX is available under the MIT license. See [LICENSE](https://raw.githubusercontent.com/JessicaTegner/PyTinyTeX/master/LICENSE) for more details. TinyTeX itself is available under the GPL-2 license.
