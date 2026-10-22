import asyncio
from subprocess import CompletedProcess
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

import pytinytex
from pytinytex import compiler, tlmgr


@pytest.mark.parametrize(
    "stage, error",
    [
        ("launch", PermissionError("failure")),
        ("launch", TypeError("failure")),
        ("log", PermissionError("failure")),
        ("log", ValueError("failure")),
        ("log", TypeError("failure")),
    ],
)
def test_compile_error_handling(monkeypatch, tmp_path, caplog, stage, error):
    tex = tmp_path / "test.tex"
    tex.touch()
    monkeypatch.setattr(pytinytex, "get_engine", lambda engine: "dummy")
    run = Mock(return_value=CompletedProcess([], 0, stdout=b"", stderr=b""))
    monkeypatch.setattr(compiler.subprocess, "run", run)
    if stage == "launch":
        run.side_effect = error
    else:
        tex.with_suffix(".log").touch()
        tex.with_suffix(".pdf").touch()
        monkeypatch.setattr(compiler, "parse_log", Mock(side_effect=error))

    if isinstance(error, TypeError):
        with pytest.raises(TypeError, match="failure"):
            compiler.compile(tex)
    else:
        result = compiler.compile(tex)
        assert result.success is (stage == "log")
        if stage == "launch":
            assert "failure" in result.output
        else:
            assert "Failed to parse log file: failure" in caplog.text


@pytest.mark.parametrize("error", [PermissionError("failure"), TypeError("failure")])
def test_refresh_error_handling(monkeypatch, tmp_path, error):
    (tmp_path / "mktexlsr").touch()
    monkeypatch.setattr(tlmgr.subprocess, "Popen", Mock(side_effect=error))
    if isinstance(error, TypeError):
        with pytest.raises(TypeError, match="failure"):
            tlmgr._refresh_filename_db(tmp_path)
    else:
        tlmgr._refresh_filename_db(tmp_path)


@pytest.mark.parametrize(
    "error",
    [
        OSError("failure"),
        ValueError("failure"),
        TypeError("failure"),
        asyncio.CancelledError("failure"),
    ],
)
def test_stdout_error_handling(error):
    process = SimpleNamespace(
        pid=1,
        stdout=SimpleNamespace(readline=AsyncMock(side_effect=error)),
        _transport=Mock(),
        wait=AsyncMock(return_value=0),
    )
    if isinstance(error, (OSError, ValueError)):
        assert asyncio.run(tlmgr._read_stdout(process, [])) == 0
    else:
        with pytest.raises(type(error), match="failure"):
            asyncio.run(tlmgr._read_stdout(process, []))
    process._transport.close.assert_called_once()


@pytest.mark.parametrize(
    "error",
    [
        BrokenPipeError("failure"),
        ValueError("failure"),
        TypeError("failure"),
        asyncio.CancelledError("failure"),
    ],
)
def test_stdin_error_handling(monkeypatch, error):
    monkeypatch.setattr(tlmgr.sys, "stdin", SimpleNamespace(readline=lambda: "hello\n"))
    process = SimpleNamespace(
        pid=1,
        stdin=SimpleNamespace(write=Mock(side_effect=error)),
        _transport=Mock(),
    )
    if isinstance(error, (OSError, ValueError)):
        asyncio.run(tlmgr._send_stdin(process))
    else:
        with pytest.raises(type(error), match="failure"):
            asyncio.run(tlmgr._send_stdin(process))
    process._transport.close.assert_called_once()
