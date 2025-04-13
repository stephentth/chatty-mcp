---
sidebar_position: 1
---

# Welcome

Chatty MCP, a Model Context Protocol (MCP) server enables your MCP client to deliver spoken output, creating a dynamic and engaging interaction. Enhance your experience with lively, audible responses, such as after each prompt in the Cursor AI editor or Cline AI, adding a unique touch to your coding workflow. Its applications extend beyond these use cases, offering versatile functionality.

<!-- Image of Cursor with edit -->

![Chatty MCP in action](/img/main_screenshot.png)

# Features

- Provides a command for Cursor or Cline to produce spoken output.
- Supports the MCP server protocol.
- Compatible with native TTS solutions and advanced TTS models.
- Allows customization of volume and speaking style.

# Prerequisites

- Python >= 3.10
- UV: Python package manager

Depending on your operating system and preferred voice model, the requirements are:

- For fast, native, traditional voice:
  - **macOS**: Utilizes the built-in `say` command, requiring no additional installation.
  - **Linux**:
    - Requires `espeak` and `festival` to be installed on the system.
- For advanced features and natural-sounding voice synthesis:
  - **Models**:
    - Supports `Kokoro-TTS` (https://kokorottsai.com/).
  - **Inference**:
    - **macOS**: Leverages `mlx_audio.tts.generate`, a library optimized for fast inference on Apple Silicon.
