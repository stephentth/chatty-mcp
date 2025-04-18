---
sidebar_position: 2
---

# Step 1: Installation

## Install from GitHub

```bash
uv tool install git+https://github.com/stephentth/chatty-mcp.git
```

or 

```bash
pipx install git+https://github.com/stephentth/chatty-mcp.git
```

Verify the installation with `chatty-mcp --help`:

```bash
➜ chatty-mcp --help
usage: chatty-mcp [-h] [--engine {system,kokoro}] [--streaming] [--speed SPEED] [--volume VOLUME] [--voice VOICE]
                  [--config] [--test-voice {kokoro,system,both}]

Chatty MCP server

options:
  -h, --help            show this help message and exit
  --engine {system,kokoro}
                        Speech engine to use (default: system)
  --streaming           Use streaming mode with kokoro-onnx (plays audio in chunks as they're generated)
  --speed SPEED         Speech rate multiplier (default: 1.5)
  --volume VOLUME       Volume level from 0.0 (silent) to 1.0 (full volume), default: 1.0
  --voice VOICE         Voice to use with kokoro-onnx (default: af_sarah)
  --config              Print example Cursor MCP configuration and exit
  --test-voice {kokoro,system,both}
                        Test TTS engines with a sample message and exit. Options: kokoro, system, or both.
```

## Install from Source

If you prefer to install from source:

```bash
git clone https://github.com/stephentth/chatty-mcp.git
cd chatty-mcp
pipx install .
# or
uv tool install .
```
