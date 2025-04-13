import argparse
import asyncio
import json
import logging
import os
import platform
import subprocess
import sys

from mcp.server.fastmcp import FastMCP
import soundfile as sf
import sounddevice as sd
from kokoro_onnx import Kokoro

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("log.log"), logging.StreamHandler()],
)
logger = logging.getLogger("chatty-mcp")

mcp = FastMCP("chatty-mcp")

# Global settings
use_kokoro = False
use_streaming = True  # Whether to use streaming mode for Kokoro
speech_speed = 1.5
volume_level = 1.0
voice_name = "af_sarah"  # Default voice
kokoro_synth = None  # Initialize the synthesizer globally


def init_kokoro() -> Kokoro:
    """Initialize the Kokoro synthesizer if not already done"""
    global kokoro_synth

    if kokoro_synth is None:
        logger.info("Initializing kokoro-onnx")
        # Check if model files exist in current directory, otherwise use defaults
        model_path = "kokoro-v1.0.onnx"
        voices_path = "voices-v1.0.bin"

        if not os.path.exists(model_path) or not os.path.exists(voices_path):
            logger.warning("Model files not found in current directory. Using kokoro-onnx default paths.")
            model_path = None
            voices_path = None

        kokoro_synth = Kokoro(model_path, voices_path)
    return kokoro_synth


def play_audio_file(file_path: str) -> None:
    """Play an audio file using the appropriate system command"""
    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.run(["afplay", file_path], check=True)
        elif system == "Linux":
            subprocess.run(["aplay", file_path], check=True)
        elif system == "Windows":
            subprocess.run(["start", "/wait", file_path], shell=True, check=True)
        else:
            logger.warning(f"Unsupported OS for audio playback: {system}")
    except Exception as e:
        logger.error(f"Error playing audio file {file_path}: {str(e)}")
        raise


async def tts_kokoro_stream(content: str, speech_speed: float, volume: float = 1.0, voice: str = None) -> None:
    """Use kokoro-onnx streaming API for text-to-speech with sounddevice for direct playback"""
    logger.info(f"Using kokoro-onnx streaming engine with voice: {voice or voice_name}")

    kokoro = init_kokoro()

    # Create audio stream from text
    stream = kokoro.create_stream(
        text=content,
        voice=voice or voice_name,
        speed=speech_speed,
        lang="en-us",
    )

    # Process each chunk as it becomes available
    chunk_count = 0
    async for samples, sample_rate in stream:
        chunk_count += 1
        logger.info(f"Playing audio stream chunk {chunk_count}...")

        # Apply volume adjustment if needed
        if volume != 1.0:
            samples = samples * volume

        # Play audio directly using sounddevice
        sd.play(samples, sample_rate)
        sd.wait()  # Wait until audio finishes playing

    logger.info(f"Finished playing {chunk_count} audio stream chunks")


def tts_kokoro(content: str, speech_speed: float, volume: float = 1.0, voice: str = None) -> None:
    """Use kokoro-onnx for text-to-speech"""
    logger.info(f"Using kokoro-onnx engine with voice: {voice or voice_name}")

    # Get the initialized Kokoro instance
    kokoro = init_kokoro()

    # Generate audio with kokoro-onnx
    audio, sample_rate = kokoro.create(
        text=content,
        voice=voice or voice_name,
        speed=speech_speed,
        lang="en-us",
    )

    # Apply volume adjustment
    if volume != 1.0:
        audio = audio * volume

    # Save to temporary file
    temp_file = "temp_audio.wav"
    sf.write(temp_file, audio, sample_rate)

    try:
        # Play audio using the common function
        play_audio_file(temp_file)
    finally:
        # Clean up temp file
        try:
            os.remove(temp_file)
        except:
            pass


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


def print_example_config() -> None:
    """Print an example Cursor MCP configuration to stdout."""
    current_dir = os.path.dirname(os.path.abspath(__file__))

    example_config = {
        "mcpServers": {
            "chatty": {
                "command": "chatty-mcp",
                "args": [
                    "--kokoro",
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
    print("\nInstallation notes:")
    print("1. Install required packages:")
    print("   pip install kokoro-onnx sounddevice soundfile numpy")
    print("   Note: On Linux, you may need to run: apt-get install portaudio19-dev")
    print("2. Download the model files:")
    print("   wget https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx")
    print("   wget https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin")
    print("3. Place the model files in the same directory as chatty.py")
    print("\nUsage Features:")
    print("- Standard mode: Creates full audio before playing")
    print("- Streaming mode: Begins playing audio as chunks are generated (faster response)")
    print("- Multiple voices: Try different voices with --voice parameter")
    print("- List available voices: Run with --list-voices")
    print("- Test voices: Run with --test-voice=kokoro --voice=af_nicole")


@mcp.tool()
async def speak(content: str) -> str:
    """Speech to the user about something

    Args:
        content: Content about what you want to say
    """
    logger.info(f"TTS request: {content[:50]}... (speed: {speech_speed}, volume: {volume_level})")
    try:
        if use_kokoro:
            if use_streaming:
                await tts_kokoro_stream(content, speech_speed, volume_level, voice_name)
            else:
                tts_kokoro(content, speech_speed, volume_level, voice_name)
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


def main():
    """Entry point function for CLI usage via pyproject.toml"""
    parser = argparse.ArgumentParser(description="Chatty MCP server")
    parser.add_argument(
        "--kokoro",
        action="store_true",
        help="Use kokoro-onnx instead of system speech commands",
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
        "--list-voices",
        action="store_true",
        help="List available voices in kokoro-onnx and exit",
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

    if args.list_voices:
        try:
            # Initialize Kokoro to get voice list
            kokoro = init_kokoro()
            print("\n🎤 Available Kokoro voices:")
            # This is a placeholder - the actual method to list voices depends on the Kokoro API
            # As of now, kokoro-onnx doesn't have a direct method to list voices
            print("  af_sarah - Female English voice")
            print("  af_nicole - Female English voice")
            print("  en_US-alan-medium - Male English voice")
            print("See full list at: https://github.com/thewh1teagle/kokoro-onnx")
            sys.exit(0)
        except Exception as e:
            print(f"❌ Error listing voices: {str(e)}")
            sys.exit(1)

    if args.config:
        print_example_config()
        sys.exit(0)

    if args.test_voice:
        test_message = "Hello, this is a test of the Chatty MCP text-to-speech system. If you hear this message, the voice engine is working correctly."

        if args.test_voice in ["kokoro", "both"]:
            try:
                print(f"\n📢 Testing Kokoro-ONNX TTS engine with voice: {args.voice}...")
                # Check for model files before test
                model_path = "kokoro-v1.0.onnx"
                voices_path = "voices-v1.0.bin"
                if not os.path.exists(model_path) or not os.path.exists(voices_path):
                    print("⚠️  Warning: Model files not found in current directory.")
                    print(f"   Expected: {model_path} and {voices_path}")
                    print("   You may need to download them with:")
                    print(
                        "   wget https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx"
                    )
                    print(
                        "   wget https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"
                    )
                    print("   Attempting to use default model paths...")

                if args.streaming:
                    print("   Using streaming mode...")
                    asyncio.run(tts_kokoro_stream(test_message, args.speed, args.volume, args.voice))
                else:
                    tts_kokoro(test_message, args.speed, args.volume, args.voice)
                print("✅ Kokoro-ONNX TTS test completed successfully.")
            except Exception as e:
                print(f"❌ Error testing Kokoro-ONNX TTS: {str(e)}")
                print("   Make sure you have installed: pip install kokoro-onnx sounddevice soundfile numpy")
                if platform.system() == "Linux":
                    print("   On Linux, you may need to run: apt-get install portaudio19-dev")
                print("   And downloaded the model files to the current directory.")

        if args.test_voice in ["system", "both"]:
            try:
                print("\n📢 Testing system TTS engine...")
                tts_system(test_message, args.speed, args.volume)
                print("✅ System TTS test completed successfully.")
            except Exception as e:
                print(f"❌ Error testing system TTS: {str(e)}")

        sys.exit(0)

    global use_kokoro, use_streaming, speech_speed, volume_level, voice_name
    use_kokoro = args.kokoro
    use_streaming = args.streaming
    speech_speed = args.speed
    volume_level = max(0.0, min(1.0, args.volume))
    voice_name = args.voice

    engine_name = "kokoro-onnx" if use_kokoro else "system TTS"
    streaming_mode = " (streaming mode)" if use_kokoro and use_streaming else ""
    voice_info = f" with voice '{voice_name}'" if use_kokoro else ""

    logger.info(
        f"Starting speech server with {engine_name}{streaming_mode}{voice_info} at speed {speech_speed} and volume {volume_level}"
    )

    mcp.run(transport="stdio")
    logger.info("Chatty MCP server stopped")


if __name__ == "__main__":
    main()
