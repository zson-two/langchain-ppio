# langchain-ppio

`langchain-ppio` provides a PPIO sandbox backend for [Deep Agents](https://docs.langchain.com/oss/python/deepagents/sandboxes).

## Install

```bash
uv add langchain-ppio
```

## Quick Start

```python
import os
from pathlib import Path

from ppio_sandbox.core import Sandbox
from langchain_ppio import PPIOSandbox

# Optional: load API key from local file
if not os.getenv("PPIO_API_KEY") and Path("ppio_key").exists():
    os.environ["PPIO_API_KEY"] = Path("ppio_key").read_text().strip()

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

The smoke command will read `PPIO_API_KEY` from environment variables first, then fallback to a local `ppio_key` file.

## Build & Publish With uv

```bash
uv build
uv publish
```
