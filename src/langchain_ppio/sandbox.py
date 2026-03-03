"""PPIO sandbox implementation."""

from __future__ import annotations

from typing import Any, Protocol

from deepagents.backends.protocol import (
    ExecuteResponse,
    FileDownloadResponse,
    FileUploadResponse,
)
from deepagents.backends.sandbox import BaseSandbox
from e2b import (
    AuthenticationException,
    CommandExitException,
    InvalidArgumentException,
    NotFoundException,
    SandboxException,
    TimeoutException,
)


class _CommandsProtocol(Protocol):
    def run(
        self,
        cmd: str,
        *args: Any,
        timeout: float | None = ...,
        **kwargs: Any,
    ) -> Any: ...


class _FilesProtocol(Protocol):
    def read(self, path: str, format: str = ...) -> Any: ...

    def write(self, path: str, data: bytes | str) -> Any: ...


class E2BCompatibleSandbox(Protocol):
    @property
    def sandbox_id(self) -> str: ...

    @property
    def commands(self) -> _CommandsProtocol: ...

    @property
    def files(self) -> _FilesProtocol: ...


def _normalize_bytes(content: Any) -> bytes:
    if isinstance(content, memoryview):
        return content.tobytes()
    if isinstance(content, bytearray):
        return bytes(content)
    if isinstance(content, str):
        return content.encode()
    return content


def _map_path_error(message: str, *, fallback: str) -> str:
    lower = message.lower()
    if "permission" in lower or "forbidden" in lower:
        return "permission_denied"
    if "directory" in lower:
        return "is_directory"
    if "not found" in lower or "no such file" in lower:
        return "file_not_found"
    if "path" in lower or "invalid" in lower:
        return "invalid_path"
    return fallback


def _join_output(stdout: str | None, stderr: str | None) -> str:
    out = stdout or ""
    err = stderr or ""
    if out and err:
        return f"{out}\n{err}"
    return out or err


class PPIOSandbox(BaseSandbox):
    """PPIO sandbox adapter using the E2B-compatible SDK surface."""

    def __init__(self, *, sandbox: E2BCompatibleSandbox, timeout: int = 30 * 60) -> None:
        """Create a backend wrapping an existing E2B-compatible sandbox."""
        self._sandbox = sandbox
        self._timeout = timeout

    def _read_file(self, path: str) -> FileDownloadResponse:
        if not path.startswith("/"):
            return FileDownloadResponse(path=path, content=None, error="invalid_path")

        try:
            content = self._sandbox.files.read(path, format="bytes")
            return FileDownloadResponse(path=path, content=_normalize_bytes(content), error=None)
        except NotFoundException:
            return FileDownloadResponse(path=path, content=None, error="file_not_found")
        except AuthenticationException:
            return FileDownloadResponse(path=path, content=None, error="permission_denied")
        except InvalidArgumentException as exc:
            return FileDownloadResponse(
                path=path,
                content=None,
                error=_map_path_error(str(exc), fallback="invalid_path"),
            )
        except SandboxException as exc:
            return FileDownloadResponse(
                path=path,
                content=None,
                error=_map_path_error(str(exc), fallback="file_not_found"),
            )

    def _write_file(self, path: str, content: bytes) -> FileUploadResponse:
        if not path.startswith("/"):
            return FileUploadResponse(path=path, error="invalid_path")

        try:
            self._sandbox.files.write(path, content)
            return FileUploadResponse(path=path, error=None)
        except NotFoundException:
            return FileUploadResponse(path=path, error="file_not_found")
        except AuthenticationException:
            return FileUploadResponse(path=path, error="permission_denied")
        except InvalidArgumentException as exc:
            return FileUploadResponse(path=path, error=_map_path_error(str(exc), fallback="invalid_path"))
        except SandboxException as exc:
            return FileUploadResponse(path=path, error=_map_path_error(str(exc), fallback="permission_denied"))

    @property
    def id(self) -> str:
        """Return the sandbox id."""
        return self._sandbox.sandbox_id

    def execute(self, command: str, *, timeout: int | None = None) -> ExecuteResponse:
        """Execute a shell command inside the sandbox."""
        command_timeout = self._timeout if timeout is None else timeout

        try:
            result = self._sandbox.commands.run(command, timeout=command_timeout)
            return ExecuteResponse(
                output=_join_output(result.stdout, result.stderr),
                exit_code=result.exit_code,
                truncated=False,
            )
        except CommandExitException as exc:
            return ExecuteResponse(
                output=_join_output(exc.stdout, exc.stderr),
                exit_code=exc.exit_code,
                truncated=False,
            )
        except TimeoutException as exc:
            return ExecuteResponse(output=str(exc), exit_code=124, truncated=False)
        except SandboxException as exc:
            return ExecuteResponse(output=str(exc), exit_code=1, truncated=False)

    def download_files(self, paths: list[str]) -> list[FileDownloadResponse]:
        """Download files from the sandbox."""
        return [self._read_file(path) for path in paths]

    def upload_files(self, files: list[tuple[str, bytes]]) -> list[FileUploadResponse]:
        """Upload files into the sandbox."""
        return [self._write_file(path, content) for path, content in files]
