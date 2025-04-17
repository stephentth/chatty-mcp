import argparse
import asyncio
import json
import logging
import os
import platform
import subprocess
import sys

from mcp.server.fastmcp import FastMCP

from system_engine import tts_system, test_system_voice
from kokoro_engine import tts_kokoro, tts_kokoro_stream

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[],  # No handlers initially, will be configured in configure_logging
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
                "command": "uv",
                "args": [
                    "tool",
                    "--directory",
                    current_dir,
                    "run",
                    "chatty-mcp",
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
                "description": "Chatty MCP server",
            }
        }
    }
    json.dump(example_config, sys.stdout, indent=2)
    sys.stdout.write("\n")  # Add newline after JSON

    logger.info("1. Download the model files:")
    logger.info(
        "   wget https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx"
    )
    logger.info(
        "   wget https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"
    )
    logger.info("2. Place the model files in one of these locations (in order of priority):")
    logger.info("   - Current directory (where chatty-mcp runs)")
    logger.info("   - $HOME/.kokoro_models/ directory")
    logger.info("   - $HOME/.chatty-mcp/ directory")
    logger.info("   - Custom path specified by environment variables:")
    logger.info("     export CHATTY_MCP_KOKORO_MODEL_PATH=/path/to/kokoro-v1.0.onnx")
    logger.info("     export CHATTY_MCP_KOKORO_VOICE_PATH=/path/to/voices-v1.0.bin")


def configure_logging(log_dir=None):
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
        log_file_path = os.path.join(log_dir, "chatty-mcp.log")
        handler = logging.FileHandler(log_file_path)
    else:
        handler = logging.FileHandler("log.log")

    handler.setFormatter(logging.Formatter(log_format))
    logging.root.addHandler(handler)

    # if log_dir:
    #     # Log file location will be printed to stderr during startup, but no further console output
    #     print(f"Logging to file: {log_file_path}", file=sys.stderr)


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
            try:
                if use_streaming:
                    await tts_kokoro_stream(content, speech_speed, volume_level, voice_name)
                else:
                    tts_kokoro(content, speech_speed, volume_level, voice_name)
            except FileNotFoundError:
                logger.warning("Kokoro model files not found, falling back to system TTS")
                tts_system(content, speech_speed, volume_level)
                return "WARNING: Kokoro model not found, fallback to system TTS"
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
        logger.info(f"\n📢 Testing Kokoro-ONNX TTS engine with voice: {args.voice}...")
        model_filename = "kokoro-v1.0.onnx"
        voices_filename = "voices-v1.0.bin"

        model_found = False
        voices_found = False
        home_dir = os.path.expanduser("~")

        search_locations = [
            os.getcwd(),
            os.path.join(home_dir, ".kokoro_models"),
            os.path.join(home_dir, ".chatty-mcp"),
        ]

        # Search for files in each location
        for location in search_locations:
            if not os.path.exists(location):
                continue

            if os.path.exists(os.path.join(location, model_filename)):
                model_found = True

            if os.path.exists(os.path.join(location, voices_filename)):
                voices_found = True

            if model_found and voices_found:
                break

        env_model_path = os.environ.get("CHATTY_MCP_KOKORO_MODEL_PATH")
        env_voices_path = os.environ.get("CHATTY_MCP_KOKORO_VOICE_PATH")

        env_model_found = env_model_path and os.path.exists(env_model_path)
        env_voices_found = env_voices_path and os.path.exists(env_voices_path)

        # Check if any files were found
        model_found = model_found or env_model_found
        voices_found = voices_found or env_voices_found

        # Display warning if models aren't found anywhere
        if not model_found or not voices_found:
            logger.warning("⚠️  Warning: Model files not found in any of the standard locations.")
            logger.warning("   Kokoro will attempt to use its default model paths, which may not work.")
            logger.warning("   To download the model files, use these commands:")
            logger.warning(
                "   wget https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx"
            )
            logger.warning(
                "   wget https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"
            )
            logger.warning("   Place them in one of these locations:")
            logger.warning("   - Current directory")
            logger.warning("   - $HOME/.kokoro_models/ directory")
            logger.warning("   - $HOME/.chatty-mcp/ directory")
            logger.warning("   - Custom path set via environment variables")

        # Run the appropriate test based on streaming mode
        if args.streaming:
            logger.info("   Using streaming mode...")
            asyncio.run(tts_kokoro_stream(test_message, args.speed, args.volume, args.voice))
        else:
            tts_kokoro(test_message, args.speed, args.volume, args.voice)

        logger.info("✅ Kokoro-ONNX TTS test completed successfully.")
        return True
    except Exception as e:
        logger.error(f"❌ Error testing Kokoro-ONNX TTS: {str(e)}")
        logger.error("   Make sure you have installed: pip install kokoro-onnx sounddevice soundfile numpy")
        if platform.system() == "Linux":
            logger.error("   On Linux, you may need to run: apt-get install portaudio19-dev")
        logger.error("   And downloaded the model files to one of the supported locations.")
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
