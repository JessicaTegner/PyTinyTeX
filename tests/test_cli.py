"""Tests for the CLI module."""

import os
from unittest import mock

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


def test_cli_tinytex_sets_env(monkeypatch):
    captured = {}

    def fake_version():
        captured["env"] = os.environ.get("PYTINYTEX_TINYTEX")
        return "tlmgr revision 12345"

    monkeypatch.setattr("pytinytex.get_version", fake_version)
    result = main(["--tinytex", "/tmp/opt/tinytext", "version"])
    assert result == 0
    assert captured["env"] == "/tmp/opt/tinytext"


def test_cli_download_default_target(monkeypatch):
    monkeypatch.delenv("PYTINYTEX_TINYTEX", raising=False)
    with mock.patch("pytinytex.download_tinytex") as dl:
        result = main(["download"])
    assert result == 0
    dl.assert_called_once()
    assert "target_folder" not in dl.call_args.kwargs


def test_cli_download_honours_tinytex(monkeypatch):
    with mock.patch("pytinytex.download_tinytex") as dl:
        result = main(["--tinytex", "/tmp/opt/tinytext", "download"])
    assert result == 0
    dl.assert_called_once_with(version="latest", variation=1, target_folder="/tmp/opt/tinytext")


def test_cli_help_documents_tinytex(capsys):
    try:
        main(["--help"])
    except SystemExit:
        pass
    assert "--tinytex" in capsys.readouterr().out
