"""Minimal smoke test for langchain-ppio."""

from __future__ import annotations

import os
from pathlib import Path

from e2b import Sandbox

from langchain_ppio import PPIOSandbox


def _ensure_e2b_env() -> None:
    os.environ.setdefault("E2B_DOMAIN", "sandbox.ppio.cn")

    if os.getenv("E2B_API_KEY"):
        return

    key_file = Path("ppio_key")
    if key_file.exists():
        key = key_file.read_text(encoding="utf-8").strip()
        if key:
            os.environ["E2B_API_KEY"] = key


def main() -> int:
    _ensure_e2b_env()
    if not os.getenv("E2B_API_KEY"):
        print("E2B_API_KEY is not set and ppio_key file is missing/empty.")
        return 1

    sandbox = Sandbox.create()
    backend = PPIOSandbox(sandbox=sandbox)
    try:
        result = backend.execute("echo hello-from-ppio")
        print(f"sandbox_id={backend.id}")
        print(f"exit_code={result.exit_code}")
        print(result.output.strip())
        return 0 if result.exit_code == 0 else 1
    finally:
        sandbox.kill()


if __name__ == "__main__":
    raise SystemExit(main())
