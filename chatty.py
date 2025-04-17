import argparse
import asyncio
import json
import logging
import os
import platform
import subprocess
import sys

from mcp.server.fastmcp import FastMCP

# Import the engine modules
from system_engine import tts_system, test_system_voice
from kokoro_engine import tts_kokoro, tts_kokoro_stream

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("chatty-mcp")

mcp = FastMCP("chatty-mcp")

# Global settings
speech_engine = "system"  # Possible values: "system", "kokoro"
use_streaming = True  # Whether to use streaming mode for Kokoro
speech_speed = 1.5
volume_level = 1.0
voice_name = "af_sarah"  # Default voice


def print_example_config() -> None:
    """Print an example Cursor MCP configuration to stdout."""
    current_dir = os.path.dirname(os.path.abspath(__file__))

    example_config = {
        "mcpServers": {
            "chatty": {
                "command": "chatty-mcp",
                "args": [
                    "--engine",
                    "kokoro",
                    "--streaming",
                    "--voice",
                    "af_sarah",
                    "--speed",
                    "1.5",
                    "--volume",
                    "0.8",
                ],
                "description": "Chatty MCP server with Kokoro-ONNX TTS engine (streaming mode)",
            }
        }
    }
    json.dump(example_config, sys.stdout, indent=2)
    print()
    print("\nInstallation Notes:")
    print("1. Install required packages:")
    print("   pip install kokoro-onnx sounddevice soundfile numpy")
    print("   Note: On Linux, you may need to run: apt-get install portaudio19-dev")
    print("2. Download the model files:")
    print("   wget https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx")
    print("   wget https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin")
    print("3. Place the model files in one of these locations (in order of priority):")
    print("   - Current directory (where chatty-mcp runs)")
    print("   - $HOME/.kokoro_models/ directory")
    print("   - Custom path specified by environment variables:")
    print("     export CHATTY_MCP_KOKORO_MODEL_PATH=/path/to/kokoro-v1.0.onnx")
    print("     export CHATTY_MCP_KOKORO_VOICE_PATH=/path/to/voices-v1.0.bin")
    print("\nFeatures:")
    print("- Speech engines: Use --engine=[system|kokoro] to select your preferred engine")
    print("- Streaming mode: Begins playing audio as chunks are generated (faster response)")
    print("- Multiple voices: Try different voices with --voice parameter")
    print("- Test voices: Run with --test-voice=kokoro --voice=af_nicole")


def configure_logging(log_dir=None):
    """Configure logging with optional directory for log files"""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    handlers = [logging.StreamHandler()]

    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
        log_file_path = os.path.join(log_dir, "chatty-mcp.log")
        handlers.append(logging.FileHandler(log_file_path))
        logger.info(f"Logging to file: {log_file_path}")
    else:
        handlers.append(logging.FileHandler("log.log"))

    for handler in logging.root.handlers[:]:
        if not isinstance(handler, logging.StreamHandler):
            logging.root.removeHandler(handler)

    for handler in handlers:
        if isinstance(handler, logging.FileHandler):
            logging.root.addHandler(handler)

    for handler in logging.root.handlers:
        handler.setFormatter(logging.Formatter(log_format))


@mcp.tool()
async def speak(content: str) -> str:
    """Speech to the user about something

    Args:
        content: Content about what you want to say

    Returns:
        str: 'done' on successful speech synthesis, or error message describing the failure.
             Error messages are prefixed with 'Error:' and include details about what went wrong.
    """
    logger.info(f"TTS request: {content[:50]}... (speed: {speech_speed}, volume: {volume_level})")
    try:
        if speech_engine == "kokoro":
            if use_streaming:
                await tts_kokoro_stream(content, speech_speed, volume_level, voice_name)
            else:
                tts_kokoro(content, speech_speed, volume_level, voice_name)
        elif speech_engine == "system":
            tts_system(content, speech_speed, volume_level)
        else:
            logger.error(f"Unsupported speech engine: {speech_engine}")
            raise RuntimeError(f"Text-to-speech not supported for engine: {speech_engine}")

        logger.info("TTS completed successfully")
        return "done"
    except subprocess.CalledProcessError as e:
        logger.error(f"TTS process failed with error code {e.returncode}")
        return f"Error: TTS process failed with code {e.returncode}"
    except Exception as e:
        logger.error(f"Unexpected error during TTS: {str(e)}")
        return f"Error: {str(e)}"


def test_kokoro_voice(test_message: str, args) -> bool:
    """Test the Kokoro TTS engine with a sample message

    Args:
        test_message: Text to convert to speech
        args: Command line arguments containing speed, volume, voice, and streaming settings

    Returns:
        bool: True if the test succeeded, False otherwise
    """
    try:
        print(f"\n📢 Testing Kokoro-ONNX TTS engine with voice: {args.voice}...")
        # Check for model files in all supported locations
        model_filename = "kokoro-v1.0.onnx"
        voices_filename = "voices-v1.0.bin"

        # Check current directory
        model_found = os.path.exists(model_filename)
        voices_found = os.path.exists(voices_filename)

        # Check home directory
        home_dir = os.path.expanduser("~")
        home_model_path = os.path.join(home_dir, ".kokoro_models", model_filename)
        home_voices_path = os.path.join(home_dir, ".kokoro_models", voices_filename)

        home_model_found = os.path.exists(home_model_path)
        home_voices_found = os.path.exists(home_voices_path)

        # Check environment variables
        env_model_path = os.environ.get("CHATTY_MCP_KOKORO_MODEL_PATH")
        env_voices_path = os.environ.get("CHATTY_MCP_KOKORO_VOICE_PATH")

        env_model_found = env_model_path and os.path.exists(env_model_path)
        env_voices_found = env_voices_path and os.path.exists(env_voices_path)

        # Display warning if models aren't found anywhere
        if not (model_found or home_model_found or env_model_found) or not (
            voices_found or home_voices_found or env_voices_found
        ):
            print("⚠️  Warning: Model files not found in any of the standard locations.")
            print("   Kokoro will attempt to use its default model paths, which may not work.")
            print("   To download the model files, use these commands:")
            print(
                "   wget https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx"
            )
            print(
                "   wget https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"
            )
            print("   Place them in one of these locations:")
            print("   - Current directory")
            print("   - $HOME/.kokoro_models/ directory")
            print("   - Custom path set via environment variables")

        # Run the appropriate test based on streaming mode
        if args.streaming:
            print("   Using streaming mode...")
            asyncio.run(tts_kokoro_stream(test_message, args.speed, args.volume, args.voice))
        else:
            tts_kokoro(test_message, args.speed, args.volume, args.voice)

        print("✅ Kokoro-ONNX TTS test completed successfully.")
        return True
    except Exception as e:
        print(f"❌ Error testing Kokoro-ONNX TTS: {str(e)}")
        print("   Make sure you have installed: pip install kokoro-onnx sounddevice soundfile numpy")
        if platform.system() == "Linux":
            print("   On Linux, you may need to run: apt-get install portaudio19-dev")
        print("   And downloaded the model files to one of the supported locations.")
        return False


def main():
    parser = argparse.ArgumentParser(description="Chatty MCP server")
    parser.add_argument(
        "--engine",
        type=str,
        choices=["system", "kokoro"],
        default="system",
        help="Speech engine to use (default: system)",
    )
    parser.add_argument(
        "--streaming",
        action="store_true",
        help="Use streaming mode with kokoro-onnx (plays audio in chunks as they're generated)",
    )
    parser.add_argument("--speed", type=float, default=1.5, help="Speech rate multiplier (default: 1.5)")
    parser.add_argument(
        "--volume",
        type=float,
        default=1.0,
        help="Volume level from 0.0 (silent) to 1.0 (full volume), default: 1.0",
    )
    parser.add_argument(
        "--voice",
        type=str,
        default="af_sarah",
        help="Voice to use with kokoro-onnx (default: af_sarah)",
    )
    parser.add_argument(
        "--config",
        action="store_true",
        help="Print example Cursor MCP configuration and exit",
    )
    parser.add_argument(
        "--test-voice",
        choices=["kokoro", "system", "both"],
        help="Test TTS engines with a sample message and exit. Options: kokoro, system, or both.",
    )
    parser.add_argument(
        "--log-dir",
        type=str,
        help="Directory to store log files (default: current directory)",
    )

    args = parser.parse_args()

    # Configure logging with optional log directory
    configure_logging(args.log_dir)

    if args.config:
        print_example_config()
        sys.exit(0)

    if args.test_voice:
        test_message = "Hello, this is a test of the Chatty MCP text-to-speech system. If you hear this message, the voice engine is working correctly."
        success = True

        if args.test_voice in ["kokoro", "both"]:
            success = test_kokoro_voice(test_message, args) and success

        if args.test_voice in ["system", "both"]:
            success = test_system_voice(test_message, args.speed, args.volume) and success

        sys.exit(0 if success else 1)

    global speech_engine, use_streaming, speech_speed, volume_level, voice_name

    speech_engine = args.engine

    use_streaming = args.streaming
    speech_speed = args.speed
    volume_level = max(0.0, min(1.0, args.volume))
    voice_name = args.voice

    engine_name = "kokoro-onnx" if speech_engine == "kokoro" else "system TTS"
    streaming_mode = " (streaming mode)" if speech_engine == "kokoro" and use_streaming else ""
    voice_info = f" with voice '{voice_name}'" if speech_engine == "kokoro" else ""

    logger.info(
        f"Starting speech server with {engine_name}{streaming_mode}{voice_info} at speed {speech_speed} and volume {volume_level}"
    )

    mcp.run(transport="stdio")
    logger.info("Chatty MCP server stopped")


if __name__ == "__main__":
    main()
