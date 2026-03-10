# PyTinyTeX

![Build Status](https://github.com/JessicaTegner/PyTinyTeX/actions/workflows/ci.yaml/badge.svg)
[![PyPI version](https://badge.fury.io/py/pytinytex.svg)](https://pypi.python.org/pypi/PyTinyTeX/)
[![Development Status](https://img.shields.io/pypi/status/PyTinyTeX.svg)](https://pypi.python.org/pypi/PyTinyTeX/)
[![Python version](https://img.shields.io/pypi/pyversions/PyTinyTeX.svg)](https://pypi.python.org/pypi/PyTinyTeX/)
![License](https://img.shields.io/pypi/l/PyTinyTeX.svg)

PyTinyTeX provides a thin wrapper for [TinyTeX](https://yihui.org/tinytex), A lightweight, cross-platform, portable, and easy-to-maintain LaTeX distribution based on TeX Live.

### Installation

Installation through the normal means

```
pip install pytinytex
```

### Installing a version of TinyTeX

Each version of TinyTeX contains three variations:
* TinyTeX-0.* contains the infraonly scheme of TeX Live, without any LaTeX packages.
* TinyTeX-1.* contains about 90 LaTeX packages enough to compile common R Markdown documents (which was the original motivation of the TinyTeX project).
* TinyTeX-2-* contains more LaTeX packages requested by the community. The list of packages may grow as time goes by, and the size of this variation will grow correspondingly.


By default the variation PyTinyTeX will install is variation 1, but this can be changed.

```python
import pytinytex

pytinytex.download_tinytex(variation=0)
```

You can also use `ensure_tinytex_installed()` which will automatically download TinyTeX if it is not already installed:

```python
import pytinytex

# Downloads TinyTeX automatically if not found
pytinytex.ensure_tinytex_installed()
```


### Getting the TinyTeX path

After installing TinyTeX, you can get the path to the installed distribution with the following:

```python
import pytinytex

pytinytex.get_tinytex_path()
# /home/jessica/.pytinytex/
# c:\Users\Jessica\.pytinytex\
```

### LaTeX engine discovery

PyTinyTeX can locate LaTeX engine executables included with TinyTeX (variation 1 and above):

```python
import pytinytex

# Generic — pass any engine name
pytinytex.get_engine("pdflatex")
pytinytex.get_engine("xelatex")
pytinytex.get_engine("lualatex")

# Convenience shortcuts
pytinytex.get_pdflatex_engine()
pytinytex.get_xelatex_engine()
pytinytex.get_lualatex_engine()
```

### Package management

PyTinyTeX wraps the tlmgr (TeX Live Manager) interface for managing LaTeX packages:

```python
import pytinytex

# Install / remove packages
pytinytex.install("booktabs")
pytinytex.remove("booktabs")

# List installed packages (returns list of dicts)
pytinytex.list_installed()

# Search for packages
pytinytex.search("amsmath")

# Get detailed info about a package (returns dict)
pytinytex.info("booktabs")

# Update all packages
pytinytex.update()

# Get the TeX Live version string
pytinytex.get_version()
```

### Integrating  with pypandoc

PyTinyTeX can be used with [PyPandoc](https://pypi.org/project/pypandoc/), a Python wrapper for Pandoc. PyPandoc can be used to convert documents between different formats, including LaTeX to PDF.
To use PyTinyTeX with pypandoc, when working with latex or pdf documents, you need to give pypandoc the path to pdflatex (included with variation 1 and above), like the following:

```python
import pytinytex
import pypandoc

# make sure that pytinytex is installed
pytinytex.ensure_tinytex_installed()

# get the path to the pdflatex executable
pdflatex_path = pytinytex.get_pdflatex_engine()

# convert a markdown file to a pdf
pypandoc.convert_file('input.md', 'pdf', outputfile='output.pdf', extra_args=['--pdf-engine', pdflatex_path])
```


### Contributing

Contributions are welcome. When opening a PR, please keep the following guidelines in mind:

1. Before implementing, please open an issue for discussion.
2. Make sure you have tests for the new logic.
3. Add yourself to contributors at README.md unless you are already there. In that case tweak your


### Contributors

* [Jessica Tegner](https://github.com/JessicaTegner) - Maintainer and original creator of PyTinyTeX

### License

PyTinyTeX is available under MIT license. See [LICENSE](https://raw.githubusercontent.com/JessicaTegner/PyTinyTeX/master/LICENSE) for more details. TinyTeX itself is available under the GPL-2 license.
