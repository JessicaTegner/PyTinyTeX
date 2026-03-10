"""LaTeX log file parser for structured error/warning extraction."""

from __future__ import annotations

import dataclasses
import re
from typing import List, Optional


@dataclasses.dataclass
class LogEntry:
	"""A single error or warning from a LaTeX log file."""
	level: str  # "error" or "warning"
	message: str
	file: Optional[str] = None
	line: Optional[int] = None
	package: Optional[str] = None  # e.g. missing .sty name


@dataclasses.dataclass
class ParsedLog:
	"""Structured result of parsing a LaTeX log file."""
	errors: List[LogEntry] = dataclasses.field(default_factory=list)
	warnings: List[LogEntry] = dataclasses.field(default_factory=list)
	missing_packages: List[str] = dataclasses.field(default_factory=list)


# Patterns for extracting information from LaTeX logs
_RE_MISSING_FILE = re.compile(
	r"! LaTeX Error: File [`'](.+?\.sty)' not found",
)
_RE_MISSING_FILE_ALT = re.compile(
	r"! LaTeX Error: File [`'](.+?\.\w+)' not found",
)
_RE_ERROR = re.compile(r"^! (.+)", re.MULTILINE)
_RE_LINE_NUMBER = re.compile(r"^l\.(\d+)", re.MULTILINE)
_RE_WARNING = re.compile(
	r"((?:LaTeX|Package|Class)\s+(?:\w+\s+)?Warning:\s*.+?)(?:\n(?!\s)|$)",
	re.MULTILINE,
)
_RE_FILE_CONTEXT = re.compile(r"\(([^\s()]+\.\w+)")
_RE_UNDEFINED_CONTROL = re.compile(
	r"! Undefined control sequence\.",
)
_RE_MISSING_PACKAGE_SUGGESTION = re.compile(
	r"(?:perhaps|try)\s+installing\s+the\s+(\S+)\s+package",
	re.IGNORECASE,
)


def parse_log(log_content: str) -> ParsedLog:
	"""Parse LaTeX log content into structured data.

	Args:
		log_content: Raw text content of a LaTeX .log file.

	Returns:
		ParsedLog with errors, warnings, and missing packages extracted.
	"""
	result = ParsedLog()
	seen_packages = set()

	# Extract missing .sty files
	for match in _RE_MISSING_FILE.finditer(log_content):
		sty_name = match.group(1)
		pkg_name = sty_name.rsplit(".", 1)[0]
		if pkg_name not in seen_packages:
			seen_packages.add(pkg_name)
			result.missing_packages.append(pkg_name)

	# Parse errors
	lines = log_content.split("\n")
	i = 0
	while i < len(lines):
		line = lines[i]

		# Standard LaTeX error: starts with "!"
		if line.startswith("! "):
			error_msg = line[2:]

			# Collect continuation lines (until blank line or l.NNN)
			file_ctx = _find_file_context(lines, i)
			line_num = None
			j = i + 1
			while j < len(lines):
				if not lines[j].strip():
					break
				line_match = _RE_LINE_NUMBER.match(lines[j])
				if line_match:
					line_num = int(line_match.group(1))
					break
				if not lines[j].startswith("! "):
					error_msg += " " + lines[j].strip()
				j += 1

			# Check if this is a missing file error
			pkg = None
			sty_match = _RE_MISSING_FILE.match(line)
			if sty_match:
				pkg = sty_match.group(1).rsplit(".", 1)[0]

			result.errors.append(LogEntry(
				level="error",
				message=error_msg.strip(),
				file=file_ctx,
				line=line_num,
				package=pkg,
			))
			i = j + 1
			continue

		# Warnings
		if "Warning:" in line:
			warning_msg = line.strip()
			# Collect continuation lines (indented)
			j = i + 1
			while j < len(lines) and lines[j].startswith(" "):
				warning_msg += " " + lines[j].strip()
				j += 1

			file_ctx = _find_file_context(lines, i)
			result.warnings.append(LogEntry(
				level="warning",
				message=warning_msg,
				file=file_ctx,
			))
			i = j
			continue

		i += 1

	return result


def _find_file_context(lines: list, index: int) -> Optional[str]:
	"""Walk backwards from index to find the most recent file context."""
	for i in range(index, -1, -1):
		match = _RE_FILE_CONTEXT.search(lines[i])
		if match:
			return match.group(1)
	return None
