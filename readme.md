# PyTinyTeX

![Build Status](https://github.com/JessicaTegner/PyTinyTeX/actions/workflows/ci.yaml/badge.svg)
[![PyPI version](https://badge.fury.io/py/pytinytex.svg)](https://pypi.python.org/pypi/PyTinyTeX/)
[![Development Status](https://img.shields.io/pypi/status/PyTinyTeX.svg)](https://pypi.python.org/pypi/PyTinyTeX/)
[![Python version](https://img.shields.io/pypi/pyversions/PyTinyTeX.svg)](https://pypi.python.org/pypi/PyTinyTeX/)
![License](https://img.shields.io/pypi/l/PyTinyTeX.svg)


PyTinyTeX provides a thin wrapper for [TinyTeX](https://yihui.org/tinytex/), a lightweight, cross-platform, portable, and easy-to-maintain LaTeX distribution based on TeX Live.

## Installation

Install PyTinyTeX using pip:

```bash
pip install -U pytinytex
```

```python
import pytinytex

pytinytex.download_tinytex(variation=0)  # Installs TinyTeX-0.*
```

**Parameters:**

- `version` (str): Specify the TinyTeX version to install. Use `"latest"` for the most recent version or a specific. Default is `"latest"`. For reference https://github.com/rstudio/tinytex-releases.

- `variation` (int): Choose the variant of TinyTeX to install:
  - `0`: Contains the `infraonly` scheme of TeX Live, without any LaTeX packages.
  - `1`(Default) : Contains approximately 90 LaTeX packages, sufficient for compiling common R Markdown documents (the original motivation behind TinyTeX).

  - `2`: Contains a more extensive set of LaTeX packages requested by the community.  The package list may grow over time, increasing the variation's size.


## Getting the TinyTeX Path

After installation, retrieve the path to your TinyTeX distribution:

```python
import pytinytex

path = pytinytex.get_tinytex_path()
print(path)

# Example Output (platform dependent):
# /home/jessica/.pytinytex/  (Linux/macOS)
# c:\Users\Jessica\.pytinytex\  (Windows)
```

## Integrating with pypandoc

PyTinyTeX seamlessly integrates with [pypandoc](https://pypi.org/project/pypandoc/), a Python wrapper for Pandoc, enabling document conversion between various formats, including LaTeX to PDF. To leverage PyTinyTeX with pypandoc, especially when working with LaTeX or PDF documents, provide pypandoc with the path to `pdflatex` (included in variation 1 and above):
 
```python
# Get the path to the pdflatex executable
pdflatex_path = pytinytex.get_pdf_latex_engine()

# Convert a Markdown file to PDF
pypandoc.convert_file(
    'input.md',
    'pdf',
    outputfile='output.pdf',
    extra_args=['--pdf-engine', pdflatex_path]
)
```

## TODO

*   Write docs, since this looks to be a bigger wrapper than PyPandoc
*   Wrap the tlmgr interface
*   Wrap the PDFLatex engine

## Contributing

Contributions are welcome. When opening a PR, please keep the following guidelines in mind:
1.  Before implementing, please open an issue for discussion.
2.  Make sure you have tests for the new logic.
3.  Add yourself to contributors at README.md unless you are already there. In that case tweak your


## Contributors

- [Jessica Tegner](https://github.com/JessicaTegner) - Maintainer and original creator of PyTinyTeX

## License

PyTinyTeX is licensed under the MIT License. See `LICENSE` for details. TinyTeX itself is licensed under the GPL-2 license. 
