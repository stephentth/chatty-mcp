---
sidebar_position: 2
---

# Step 1: Installation

## direct from github

```bash
pipx install git+https://github.com/stephentth/chatty-mcp.git
```

for macos with apple silicon chip

```bash
pipx install "git+https://github.com/stephentth/chatty-mcp.git#egg=chatty-mcp[apple_silicon]"
```

check with `chatty-mcp --help`

```bash
$ chatty-mcp --help

usage: chatty-mcp [-h] [--kokoro] [--speed SPEED] [--volume VOLUME] [--config] [--test-voice {kokoro,system,both}]

Chatty MCP server

options:
  -h, --help            show this help message and exit
  --kokoro              Use mlx_audio.tts.generate instead of system 'say' command
  --speed SPEED         Speech rate multiplier (default: 1.5)
  --volume VOLUME       Volume level from 0.0 (silent) to 1.0 (full volume), default: 1.0
  --config              Print example Cursor MCP configuration and exit
  --test-voice {kokoro,system,both}
                        Test TTS engines with a sample message and exit. Options: kokoro, system, or both.
```




## install from source

If you would like to install from source:

```bash
git clone https://github.com/stephentth/chatty-mcp.git
cd chatty-mcp
pipx install .

# for apple silicon machine
pipx install ."[apple_silicon]"
```
