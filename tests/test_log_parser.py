"""Tests for the LaTeX log parser."""

from pytinytex.log_parser import parse_log, LogEntry, ParsedLog


def test_parse_empty_log():
	result = parse_log("")
	assert isinstance(result, ParsedLog)
	assert result.errors == []
	assert result.warnings == []
	assert result.missing_packages == []


def test_parse_missing_sty():
	log = """\
(/some/file.tex
! LaTeX Error: File `booktabs.sty' not found.

Type X to quit or <RETURN> to proceed,
or enter new name. (Default extension: sty)

Enter file name:
"""
	result = parse_log(log)
	assert len(result.missing_packages) == 1
	assert "booktabs" in result.missing_packages
	assert len(result.errors) == 1
	assert result.errors[0].package == "booktabs"


def test_parse_multiple_missing_packages():
	log = """\
! LaTeX Error: File `foo.sty' not found.

l.5 \\usepackage{foo}

! LaTeX Error: File `bar.sty' not found.

l.6 \\usepackage{bar}
"""
	result = parse_log(log)
	assert len(result.missing_packages) == 2
	assert "foo" in result.missing_packages
	assert "bar" in result.missing_packages


def test_parse_duplicate_missing_package():
	log = """\
! LaTeX Error: File `foo.sty' not found.

! LaTeX Error: File `foo.sty' not found.
"""
	result = parse_log(log)
	assert len(result.missing_packages) == 1
	assert result.missing_packages[0] == "foo"


def test_parse_error_with_line_number():
	log = """\
! Undefined control sequence.
l.42 \\badcommand
"""
	result = parse_log(log)
	assert len(result.errors) == 1
	assert result.errors[0].line == 42
	assert "Undefined control sequence" in result.errors[0].message


def test_parse_warning():
	log = """\
LaTeX Warning: Reference `fig:test' on page 1 undefined on input line 10.
"""
	result = parse_log(log)
	assert len(result.warnings) == 1
	assert "Reference" in result.warnings[0].message
	assert result.warnings[0].level == "warning"


def test_parse_package_warning():
	log = """\
Package hyperref Warning: Token not allowed in a PDF string (Unicode):
 removing `\\textbf' on input line 25.
"""
	result = parse_log(log)
	assert len(result.warnings) == 1
	assert "hyperref" in result.warnings[0].message


def test_parse_complex_log():
	"""Test parsing a realistic log with mixed content."""
	log = """\
This is pdfTeX, Version 3.14159265 (TeX Live 2024) (preloaded format=pdflatex)
entering extended mode
(/home/user/doc.tex
LaTeX2e <2024-06-01> patch level 2
(/usr/share/texmf-dist/tex/latex/base/article.cls
Document Class: article 2024/06/29 v1.4n Standard LaTeX document class
)
! LaTeX Error: File `tikz.sty' not found.

Type X to quit or <RETURN> to proceed,
or enter new name. (Default extension: sty)

Enter file name:
l.3 \\usepackage{tikz}

LaTeX Warning: Label `eq:1' multiply defined.

No pages of output.
"""
	result = parse_log(log)
	assert len(result.missing_packages) == 1
	assert "tikz" in result.missing_packages
	assert len(result.errors) >= 1
	assert len(result.warnings) >= 1


def test_parse_no_errors_success():
	log = """\
This is pdfTeX, Version 3.14159265 (TeX Live 2024)
entering extended mode
Output written on test.pdf (1 page, 1234 bytes).
Transcript written on test.log.
"""
	result = parse_log(log)
	assert len(result.errors) == 0
	assert len(result.missing_packages) == 0


def test_log_entry_fields():
	entry = LogEntry(level="error", message="test", file="foo.tex", line=10, package="bar")
	assert entry.level == "error"
	assert entry.message == "test"
	assert entry.file == "foo.tex"
	assert entry.line == 10
	assert entry.package == "bar"


def test_log_entry_defaults():
	entry = LogEntry(level="warning", message="test")
	assert entry.file is None
	assert entry.line is None
	assert entry.package is None
