from __future__ import annotations

from unittest.mock import Mock

from e2b import (
    CommandExitException,
    CommandResult,
    InvalidArgumentException,
    NotFoundException,
    TimeoutException,
)

from langchain_ppio import PPIOSandbox


def make_backend() -> tuple[PPIOSandbox, Mock]:
    sandbox = Mock()
    sandbox.sandbox_id = "sbx_123"
    backend = PPIOSandbox(sandbox=sandbox, timeout=111)
    return backend, sandbox


def test_id_exposes_sandbox_id() -> None:
    backend, _ = make_backend()
    assert backend.id == "sbx_123"


def test_execute_success_combines_stdout_and_stderr() -> None:
    backend, sandbox = make_backend()
    sandbox.commands.run.return_value = CommandResult(
        stdout="hello",
        stderr="warn",
        exit_code=0,
        error=None,
    )

    result = backend.execute("echo hello")

    sandbox.commands.run.assert_called_once_with("echo hello", timeout=111)
    assert result.exit_code == 0
    assert result.output == "hello\nwarn"
    assert result.truncated is False


def test_execute_nonzero_is_captured() -> None:
    backend, sandbox = make_backend()
    sandbox.commands.run.side_effect = CommandExitException(
        stdout="ok",
        stderr="boom",
        exit_code=2,
        error="boom",
    )

    result = backend.execute("false", timeout=7)

    sandbox.commands.run.assert_called_once_with("false", timeout=7)
    assert result.exit_code == 2
    assert result.output == "ok\nboom"


def test_execute_timeout_maps_to_124() -> None:
    backend, sandbox = make_backend()
    sandbox.commands.run.side_effect = TimeoutException("timed out")

    result = backend.execute("sleep 5")

    assert result.exit_code == 124
    assert "timed out" in result.output


def test_download_files_maps_not_found() -> None:
    backend, sandbox = make_backend()
    sandbox.files.read.side_effect = NotFoundException("missing")

    [res] = backend.download_files(["/tmp/missing.txt"])

    assert res.path == "/tmp/missing.txt"
    assert res.content is None
    assert res.error == "file_not_found"


def test_download_files_maps_directory_error() -> None:
    backend, sandbox = make_backend()
    sandbox.files.read.side_effect = InvalidArgumentException("is a directory")

    [res] = backend.download_files(["/tmp/dir"])

    assert res.content is None
    assert res.error == "is_directory"


def test_upload_files_success() -> None:
    backend, sandbox = make_backend()

    [res] = backend.upload_files([("/tmp/a.txt", b"abc")])

    sandbox.files.write.assert_called_once_with("/tmp/a.txt", b"abc")
    assert res.path == "/tmp/a.txt"
    assert res.error is None


def test_upload_files_invalid_path_without_remote_call() -> None:
    backend, sandbox = make_backend()

    [res] = backend.upload_files([("relative.txt", b"abc")])

    sandbox.files.write.assert_not_called()
    assert res.error == "invalid_path"
