---
sidebar_position: 5
title: Speech Engines
---

# Speech Engines

Chatty MCP supports multiple speech synthesis options, giving you flexibility to choose the best voice experience for your environment.

## System Text-to-Speech

Chatty MCP leverages your operating system's native TTS capabilities for a lightweight solution that requires no additional downloads:

| OS | Engine | Features |
|---|---|---|
| macOS | `say` command | Adjustable speed and volume |
| Linux | `espeak` | Adjustable speed and volume |

System TTS is the default option if no other engines are specified.

## Kokoro-ONNX

For higher quality, more natural-sounding speech, Chatty MCP integrates with [Kokoro-ONNX](https://github.com/thewh1teagle/kokoro-onnx), an optimized implementation of [Kokoro-TTS](https://huggingface.co/spaces/hexgrad/Kokoro-TTS).

### Features

- **Multiple voices**: Choose from various voice options
- **Streaming mode**: Begin playback while audio is still being generated
- **Natural sound**: High-quality, realistic speech synthesis
- **Adjustable parameters**: Control speed and volume
- **Cross-platform**: Works on macOS, Linux

### Getting Started with Kokoro

1. Download the model files:
   ```bash
   wget https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
   wget https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
   ```

2. Place the model files in one of these locations (in order of priority):
   - Current directory (where you run chatty-mcp)
   - `$HOME/.kokoro_models/` directory
   - Custom path specified by environment variables:
     ```bash
     export CHATTY_MCP_KOKORO_MODEL_PATH=/path/to/kokoro-v1.0.onnx
     export CHATTY_MCP_KOKORO_VOICE_PATH=/path/to/voices-v1.0.bin
     ```
   - If not found in any of these locations, Kokoro-ONNX will attempt to use its default paths

3. Enable Kokoro in your Cursor MCP configuration:
   ```json
   {
     "mcpServers": {
       "chatty": {
         "command": "chatty-mcp",
         "args": ["--engine", "kokoro", "--streaming", "--voice", "af_sarah"],
         "description": "Chatty MCP with Kokoro TTS"
       }
     }
   }
   ```

## Command Line Options

| Option | Description |
|---|---|
| `--engine VALUE` | Select speech engine: 'system' or 'kokoro' (default: system) |
| `--streaming` | Enable streaming mode for faster response time |
| `--voice VALUE` | Select voice (e.g., af_sarah, af_nicole) |
| `--speed VALUE` | Set speech rate multiplier (default: 1.5) |
| `--volume VALUE` | Set volume from 0.0 to 1.0 (default: 1.0) |
| `--test-voice VALUE` | Test speech (options: kokoro, system, both) |
| `--kokoro` | Deprecated: Use `--engine=kokoro` instead |

## Performance Considerations

- **System TTS**: Lightweight with low resource usage, but less natural-sounding
- **Kokoro standard mode**: Better quality, but may have slight delay before speaking
- **Kokoro streaming mode**: Best experience with natural sound and quick response time

For the most responsive and natural-sounding experience, we recommend using Kokoro with streaming mode enabled.

