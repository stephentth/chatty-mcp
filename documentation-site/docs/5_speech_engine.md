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
| Windows | Coming soon | - |

System TTS is the default option if no other engines are specified.

## Kokoro-ONNX

For higher quality, more natural-sounding speech, Chatty MCP integrates with [Kokoro-ONNX](https://github.com/thewh1teagle/kokoro-onnx), an optimized implementation of [Kokoro-TTS](https://huggingface.co/spaces/hexgrad/Kokoro-TTS).

### Features

- **Multiple voices**: Choose from various voice options
- **Streaming mode**: Begin playback while audio is still being generated
- **Natural sound**: High-quality, realistic speech synthesis
- **Adjustable parameters**: Control speed and volume
- **Cross-platform**: Works on macOS, Linux, and Windows

### Getting Started with Kokoro

1. Install the required dependencies:
   ```bash
   pip install kokoro-onnx sounddevice soundfile numpy
   ```

2. Download the model files:
   ```bash
   wget https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
   wget https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
   ```

3. Place the model files in your Chatty MCP directory

4. Enable Kokoro in your Cursor MCP configuration:
   ```json
   {
     "mcpServers": {
       "chatty": {
         "command": "chatty-mcp",
         "args": ["--kokoro", "--streaming", "--voice", "af_sarah"],
         "description": "Chatty MCP with Kokoro TTS"
       }
     }
   }
   ```

## Command Line Options

| Option | Description |
|---|---|
| `--kokoro` | Use Kokoro-ONNX instead of system TTS |
| `--streaming` | Enable streaming mode for faster response time |
| `--voice VALUE` | Select voice (e.g., af_sarah, af_nicole) |
| `--speed VALUE` | Set speech rate multiplier (default: 1.5) |
| `--volume VALUE` | Set volume from 0.0 to 1.0 (default: 1.0) |
| `--list-voices` | Show available Kokoro voices |
| `--test-voice VALUE` | Test speech (options: kokoro, system, both) |

## Performance Considerations

- **System TTS**: Lightweight, low resource usage, but less natural sounding
- **Kokoro standard mode**: Better quality, but may have slight delay before speaking
- **Kokoro streaming mode**: Best experience with natural sound and quick response time

For the most responsive and natural-sounding experience, we recommend using Kokoro with streaming mode enabled.

