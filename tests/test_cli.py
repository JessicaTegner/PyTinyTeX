"""Tests for the CLI module."""

from pytinytex.cli import main


def test_cli_no_args():
	"""Running with no args should print help and return 1."""
	result = main([])
	assert result == 1


def test_cli_version(monkeypatch):
	"""Test the version subcommand."""
	monkeypatch.setattr("pytinytex.get_version", lambda: "tlmgr revision 12345")
	result = main(["version"])
	assert result == 0


def test_cli_help_flag(capsys):
	"""--help should work without errors."""
	try:
		main(["--help"])
	except SystemExit:
		pass  # argparse calls sys.exit(0) on --help
