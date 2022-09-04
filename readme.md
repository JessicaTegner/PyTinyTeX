# PyTinyTeX

![Build Status](https://github.com/JessicaTegner/PyTinyTeX/actions/workflows/ci.yaml/badge.svg)
[![PyPI version](https://badge.fury.io/py/pytinytex.svg)](https://pypi.python.org/pypi/PyTinyTeX/)
[![Development Status](https://img.shields.io/pypi/status/PyTinyTeX.svg)](https://pypi.python.org/pypi/PyTinyTeX/)
[![Python version](https://img.shields.io/pypi/pyversions/PyTinyTeX.svg)](https://pypi.python.org/pypi/PyTinyTeX/)
![License](https://img.shields.io/pypi/l/PyTinyTeX.svg)

PyTinyTeX provides a thin wrapper for [TinyTeX](https://yihui.org/tinytex), A lightweight, cross-platform, portable, and easy-to-maintain LaTeX distribution based on TeX Live.

### Installation

Installation through the normal means

~~~
pip install pytinytex
~~~

Or through poetry

~~~
poetry add pytinytex
~~~


### Installing a version of TinyTeX

Each version of TinyTeX contains three variations:
* TinyTeX-0.* contains the infraonly scheme of TeX Live, without any LaTeX packages. If you install this variation, you may install any other packages via tlmgr (which is a utility included in this variation), e.g., tlmgr install latex-bin framed.
* TinyTeX-1.* contains about 90 LaTeX packages enough to compile common R Markdown documents (which was the original motivation of the TinyTeX project).
* TinyTeX-2-* contains more LaTeX packages requested by the community. The list of packages may grow as time goes by, and the size of this variation will grow correspondingly.


By default the variation PyTinyTeX will install is variation 1, but this can be changed.

~~~
import pytinytex

pytinytex.download_tinytex()
~~~


### Getting the TinyTeX path

After installing TinyTeX, you can get PyTinyTeX to pick it up with the following

~~~
import pytinytex

# from the current working dir
pytinytex.get_tinytex_path()

# Or from a specific starting base
pytinytex.get_tinytex_path("../../")
~~~

You can then use the returned string (which is the path to the installed TinyTeX distributions "bin" directory), with other libraries or programs.


### TODO

* Write docs, since this looks to be a bigger wrapper than PyPandoc
* Wrap the tlmgr interface
* Wrap the PDFLatex engine


### Contributing

Contributions are welcome. When opening a PR, please keep the following guidelines in mind:

1. Before implementing, please open an issue for discussion.
2. Make sure you have tests for the new logic.
3. Add yourself to contributors at README.md unless you are already there. In that case tweak your 


### Contributors
* [Jessica Tegner](https://github.com/JessicaTegner) - Maintainer and original creator of PyTinyTeX

### License
PyTinyTeX is available under MIT license. See [LICENSE](https://raw.githubusercontent.com/JessicaTegner/PyTinyTeX/master/LICENSE) for more details. TinyTeX itself is available under the GPL-2 license.
