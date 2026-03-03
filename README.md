# langchain-ppio

`langchain-ppio` provides a PPIO sandbox backend for [Deep Agents](https://docs.langchain.com/oss/python/deepagents/sandboxes), implemented with the [PPIO E2B-compatible API](https://ppio.com/docs/sandbox/e2b-compatible).

## Install

```bash
uv add langchain-ppio
```

## Quick Start

```python
import os
from pathlib import Path

from e2b import Sandbox
from langchain_ppio import PPIOSandbox

# Required for PPIO E2B compatibility
os.environ.setdefault("E2B_DOMAIN", "sandbox.ppio.cn")
if not os.getenv("E2B_API_KEY") and Path("ppio_key").exists():
    os.environ["E2B_API_KEY"] = Path("ppio_key").read_text().strip()

sandbox = Sandbox.create()
backend = PPIOSandbox(sandbox=sandbox)

result = backend.execute("echo hello")
print(result.output)

sandbox.kill()
```

## Run Smoke Test

```bash
uv run langchain-ppio-smoke
```

The smoke command reads `E2B_API_KEY` first, then falls back to `ppio_key`.  
`E2B_DOMAIN` defaults to `sandbox.ppio.cn`.

## Build & Publish With uv

```bash
uv build
uv publish
```
