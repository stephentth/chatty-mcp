---
sidebar_position: 2
---

# Step 1: Installation

Since v0.2.0, I introduced support for package installation. You can use your favorite Python package manager to install the server via:

```bash
uv add git+https://github.com/stephentth/chatty-mcp.git
```

For MacOS with

```bash
uv add "chatty-mcp[apple_silicon] @ git+https://github.com/stephentth/chatty-mcp.git"
```


## Installing from source

If you would like to install from source:

```bash
git clone https://github.com/stephentth/chatty-mcp.git
cd chatty-mcp
uv sync
# for macos
uv sync --extra apple_silicon
```
