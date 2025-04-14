from typing import Any
import subprocess
import logging
import argparse
import json
import sys
import platform
import os

from mcp.server.fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("log.log"), logging.StreamHandler()],
)
logger = logging.getLogger("chatty-mcp")

mcp = FastMCP("chatty-mcp")

use_kokoro = False
speech_speed = 1.5
volume_level = 1.0


def tts_kokoro(content: str, speech_speed: float, volume: float = 1.0) -> None:
    system = platform.system()

    logger.info("Using mlx_audio.tts.generate (Kokoro) engine")
    # Kokoro doesn't have direct volume control, note this in logs
    if volume != 1.0:
        logger.info(f"Volume setting ({volume}) not directly supported by Kokoro, using system volume")

    subprocess.run(
        [
            "mlx_audio.tts.generate",
            "--text",
            content,
            "--play",
            "--lang_code",
            "en-us",
            "--speed",
            str(speech_speed),
        ],
        check=True,
    )


def tts_system(content: str, speech_speed: float, volume: float = 1.0) -> None:
    system = platform.system()

    if system == "Darwin":  # macOS
        logger.info("Using macOS 'say' command")
        # Default macOS speech rate is ~175 words per minute
        adjusted_rate = int(175 * speech_speed)

        cmd = [
            "say",
            "-r",
            str(adjusted_rate),
        ]

        # macOS say command supports volume with -v flag (0 to 100)
        if volume != 1.0:
            macos_volume = int(volume * 100)
            cmd.extend(["-v", str(macos_volume)])

        cmd.append(content)

        subprocess.run(cmd, check=True)
    elif system == "Linux":
        logger.info("Using Linux 'espeak' command")
        # espeak speed is words per minute
        # Normal speed is around 175 wpm
        adjusted_rate = int(175 * speech_speed)

        cmd = [
            "espeak",
            "-s",
            str(adjusted_rate),
        ]

        # espeak supports amplitude (volume) with -a flag (0 to 200, default 100)
        if volume != 1.0:
            # Scale volume to espeak range (0-200)
            espeak_volume = int(volume * 200)
            cmd.extend(["-a", str(espeak_volume)])

        cmd.append(content)

        subprocess.run(cmd, check=True)
    else:
        logger.warning(f"Unsupported operating system: {system}")
        raise RuntimeError(f"Text-to-speech not supported on {system}")


@mcp.tool()
async def speak(content: str) -> str:
    """Speech to the user about something

    Args:
        content: Content about what you want to say
    """
    # logger.info(f"TTS request: {content[:50]}... (speed: {speech_speed}, volume: {volume_level})")
    try:
        if use_kokoro:
            tts_kokoro(content, speech_speed, volume_level)
        else:
            tts_system(content, speech_speed, volume_level)

        logger.info("TTS completed successfully")
        return "done"
    except subprocess.CalledProcessError as e:
        logger.error(f"TTS process failed with error code {e.returncode}")
        return f"Error: TTS process failed with code {e.returncode}"
    except Exception as e:
        logger.error(f"Unexpected error during TTS: {str(e)}")
        return f"Error: {str(e)}"


def print_example_config() -> None:
    """Print an example Cursor MCP configuration to stdout."""
    current_dir = os.path.dirname(os.path.abspath(__file__))

    example_config = {
        "mcpServers": {
            "chatty": {
                "command": "uv",
                "args": [
                    "--directory",
                    current_dir,
                    "run",
                    "chatty.py",
                    "--kokoro",
                    "--speed",
                    "1.5",
                    "--volume",
                    "0.8",
                ],
            }
        }
    }
    json.dump(example_config, sys.stdout, indent=2)
    print()


def main():
    """Entry point function for CLI usage via pyproject.toml"""
    parser = argparse.ArgumentParser(description="Chatty MCP server")
    parser.add_argument(
        "--kokoro",
        action="store_true",
        help="Use mlx_audio.tts.generate instead of system 'say' command",
    )
    parser.add_argument("--speed", type=float, default=1.5, help="Speech rate multiplier (default: 1.5)")
    parser.add_argument(
        "--volume",
        type=float,
        default=1.0,
        help="Volume level from 0.0 (silent) to 1.0 (full volume), default: 1.0",
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
    args = parser.parse_args()

    if args.config:
        print_example_config()
        sys.exit(0)

    if args.test_voice:
        test_message = "Hello, this is a test of the Chatty MCP text-to-speech system. If you hear this message, the voice engine is working correctly."

        if args.test_voice in ["kokoro", "both"]:
            try:
                print("\n📢 Testing Kokoro TTS engine...")
                tts_kokoro(test_message, args.speed, args.volume)
                print("✅ Kokoro TTS test completed successfully.")
            except Exception as e:
                print(f"❌ Error testing Kokoro TTS: {str(e)}")

        if args.test_voice in ["system", "both"]:
            try:
                print("\n📢 Testing system TTS engine...")
                tts_system(test_message, args.speed, args.volume)
                print("✅ System TTS test completed successfully.")
            except Exception as e:
                print(f"❌ Error testing system TTS: {str(e)}")

        sys.exit(0)

    global use_kokoro, speech_speed, volume_level
    use_kokoro = args.kokoro
    speech_speed = args.speed
    volume_level = max(0.0, min(1.0, args.volume))

    engine_name = "mlx_audio (Kokoro)" if use_kokoro else "system TTS"
    logger.info(f"Starting speech server with {engine_name} engine at speed {speech_speed} and volume {volume_level}")

    mcp.run(transport="stdio")
    logger.info("Chatty MCP server stopped")


if __name__ == "__main__":
    main()
