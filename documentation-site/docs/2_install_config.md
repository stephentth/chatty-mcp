---
sidebar_position: 2
---

# Step 1: Installation

Since v0.2.0, I introduced support for package installation. You can use your favorite Python package manager to install the server via:

```bash
# if pipx is installed
pipx install chatty-mcp

# if uv is installed
uv pip install chatty-mcp
```

`pipx` is recommended because it creates isolated environments for each package. You can also install the server manually by cloning the repository and running `pipx install -e .` from the root directory.

## Installing from source

If you would like to install from source:

```bash
uv venv
source .venv/bin/activate
uv pip install -e .
```

<!-- ## Installing via Smithery.ai

You can find the full instructions on how to use Smithery.ai to connect to this MCP server -->
