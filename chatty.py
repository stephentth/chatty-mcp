import argparse
import asyncio
import json
import logging
import os
import platform
import subprocess
import sys
import shutil  # Added for command existence check
from dataclasses import dataclass, field
from typing import Optional

# Third-party imports - ensure these are installed
try:
    from mcp.server.fastmcp import FastMCP
    import soundfile as sf
    import sounddevice as sd
    from kokoro_onnx import Kokoro
except ImportError as e:
    print(f"Error: Missing required package(s). {e}")
    print("Please install necessary packages:")
    print("  pip install mcp-server soundfile sounddevice kokoro-onnx numpy")
    sys.exit(1)


# --- Logging Setup ---
# Configure once at the start
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("chatty-mcp.log"), # Changed log file name
        logging.StreamHandler(sys.stdout) # Ensure logs go to stdout
    ],
)
logger = logging.getLogger("chatty-mcp")


# --- Configuration Dataclass ---
@dataclass
class Settings:
    use_kokoro: bool = False
    use_streaming: bool = True
    speech_speed: float = 1.5
    volume_level: float = 1.0
    voice_name: str = "af_sarah"  # Default Kokoro voice
    kokoro_model_path: Optional[str] = None
    kokoro_voices_path: Optional[str] = None
    kokoro_synth: Optional[Kokoro] = field(default=None, init=False, repr=False) # Runtime synthesizer instance


# --- MCP Server Initialization ---
mcp = FastMCP("chatty-mcp")


# --- Kokoro TTS Functions ---
def init_kokoro(settings: Settings) -> Kokoro:
    """Initialize the Kokoro synthesizer if not already done, using paths from settings."""
    if settings.kokoro_synth is None:
        logger.info("Initializing kokoro-onnx synthesizer...")

        # Determine paths: Use provided args > environment vars > defaults in current dir > Kokoro internal defaults
        model_path = settings.kokoro_model_path or os.getenv("KOKORO_MODEL_PATH")
        voices_path = settings.kokoro_voices_path or os.getenv("KOKORO_VOICES_PATH")

        # Check current directory if paths still not explicitly set
        default_model_file = "kokoro-v1.0.onnx"
        default_voices_file = "voices-v1.0.bin"
        if model_path is None and os.path.exists(default_model_file):
            model_path = default_model_file
            logger.info(f"Using Kokoro model found in current directory: {model_path}")
        if voices_path is None and os.path.exists(default_voices_file):
            voices_path = default_voices_file
            logger.info(f"Using Kokoro voices found in current directory: {voices_path}")

        # If paths are still None, Kokoro will use its internal defaults (if packaged)
        if model_path is None or voices_path is None:
             logger.warning(
                 "Kokoro model/voices paths not specified and not found in current directory. "
                 "Attempting to use kokoro-onnx internal default paths (if available)."
            )

        try:
            settings.kokoro_synth = Kokoro(model_path, voices_path)
            logger.info("kokoro-onnx initialized successfully.")
        except Exception as e:
            logger.exception(f"Failed to initialize Kokoro: {e}")
            logger.error("Please ensure Kokoro model files are correctly specified or placed.")
            logger.error("Download links: https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0")
            raise RuntimeError(f"Kokoro initialization failed: {e}") from e

    return settings.kokoro_synth


async def tts_kokoro_stream(content: str, settings: Settings) -> None:
    """Use kokoro-onnx streaming API with sounddevice for direct playback."""
    kokoro = init_kokoro(settings) # Ensures synth is initialized
    voice = settings.voice_name
    speed = settings.speech_speed
    volume = settings.volume_level

    logger.info(f"Using kokoro-onnx streaming (voice: {voice}, speed: {speed}, volume: {volume})")

    try:
        # Create audio stream from text
        stream = kokoro.create_stream(
            text=content,
            voice=voice,
            speed=speed,
            lang="en-us", # Assuming English, parameterize if needed
        )

        chunk_count = 0
        # Process each chunk as it becomes available
        async for samples, sample_rate in stream:
            chunk_count += 1
            logger.debug(f"Playing audio stream chunk {chunk_count} (Sample rate: {sample_rate}, Samples: {len(samples)})")

            # Apply volume adjustment if needed
            adjusted_samples = samples * volume if volume != 1.0 else samples

            # Play audio directly using sounddevice
            # Consider asyncio.to_thread if sd.wait() blocking is an issue elsewhere
            try:
                sd.play(adjusted_samples, sample_rate)
                sd.wait()  # Wait until this chunk finishes playing
            except sd.PortAudioError as pae:
                 logger.error(f"Sounddevice playback error: {pae}")
                 logger.error("Ensure you have a working audio output device and necessary drivers/libraries (like portaudio).")
                 raise # Re-raise to signal failure
            except Exception as play_e:
                 logger.error(f"Unexpected error during sounddevice playback: {play_e}")
                 raise # Re-raise

        if chunk_count == 0:
            logger.warning("Kokoro stream produced no audio chunks.")
        else:
            logger.info(f"Finished playing {chunk_count} audio stream chunks.")

    except Exception as e:
        logger.exception(f"Error during Kokoro streaming TTS: {e}")
        raise # Re-raise to be caught by the 'speak' tool


def tts_kokoro(content: str, settings: Settings) -> None:
    """Use kokoro-onnx non-streaming API with sounddevice for direct playback."""
    kokoro = init_kokoro(settings) # Ensures synth is initialized
    voice = settings.voice_name
    speed = settings.speech_speed
    volume = settings.volume_level

    logger.info(f"Using kokoro-onnx non-streaming (voice: {voice}, speed: {speed}, volume: {volume})")

    try:
        # Generate audio with kokoro-onnx
        audio, sample_rate = kokoro.create(
            text=content,
            voice=voice,
            speed=speed,
            lang="en-us", # Assuming English, parameterize if needed
        )

        if audio is None or len(audio) == 0:
             logger.warning("Kokoro non-streaming synthesis produced no audio data.")
             return # Nothing to play

        logger.debug(f"Generated audio (Sample rate: {sample_rate}, Samples: {len(audio)})")

        # Apply volume adjustment
        adjusted_audio = audio * volume if volume != 1.0 else audio

        # Play audio directly using sounddevice
        try:
             sd.play(adjusted_audio, sample_rate)
             sd.wait() # Wait until audio finishes playing
             logger.info("Finished playing non-streaming audio.")
        except sd.PortAudioError as pae:
             logger.error(f"Sounddevice playback error: {pae}")
             logger.error("Ensure you have a working audio output device and necessary drivers/libraries (like portaudio).")
             raise # Re-raise to signal failure
        except Exception as play_e:
             logger.error(f"Unexpected error during sounddevice playback: {play_e}")
             raise # Re-raise

    except Exception as e:
        logger.exception(f"Error during Kokoro non-streaming TTS: {e}")
        raise # Re-raise to be caught by the 'speak' tool


# --- System TTS Function ---
def tts_system(content: str, settings: Settings) -> None:
    """Uses platform-specific TTS commands."""
    system = platform.system()
    speed = settings.speech_speed
    volume = settings.volume_level # Volume [0.0, 1.0]

    logger.info(f"Using system TTS on {system} (speed: {speed}, volume: {volume})")

    cmd = []
    cmd_name = None

    try:
        if system == "Darwin":  # macOS
            cmd_name = "say"
            if not shutil.which(cmd_name):
                 raise FileNotFoundError(f"System command '{cmd_name}' not found.")
            # Default macOS speech rate is ~175 words per minute
            adjusted_rate = max(1, int(175 * speed)) # Ensure rate is positive
            # macOS say volume is -v flag (0 to 100)
            macos_volume = max(0, min(100, int(volume * 100)))

            cmd = [cmd_name, "-r", str(adjusted_rate)]
            if volume != 1.0: # Only add volume flag if non-default
                 cmd.extend(["-v", str(macos_volume)])
            cmd.append(content)

        elif system == "Linux":
            # Prefer espeak-ng if available, fallback to espeak
            cmd_name = shutil.which("espeak-ng") or shutil.which("espeak")
            if not cmd_name:
                raise FileNotFoundError("System command 'espeak-ng' or 'espeak' not found. Please install one (e.g., 'sudo apt install espeak-ng').")
            logger.info(f"Using Linux command: {cmd_name}")
            # espeak speed is words per minute (approx 80-450)
            adjusted_rate = max(80, min(450, int(175 * speed))) # Clamp to reasonable range
            # espeak amplitude is -a flag (0 to 200, default 100)
            espeak_amplitude = max(0, min(200, int(volume * 100 * 2))) # Scale volume [0,1] to amplitude [0,200]

            cmd = [cmd_name, "-s", str(adjusted_rate)]
            if volume != 0.5: # Default amplitude is 100 (volume 0.5)
                cmd.extend(["-a", str(espeak_amplitude)])
            cmd.append(content)

        else:
            logger.warning(f"System TTS not configured for operating system: {system}")
            raise OSError(f"Text-to-speech not supported on {system}")

        logger.debug(f"Running system TTS command: {' '.join(cmd)}")
        subprocess.run(cmd, check=True, capture_output=True) # Capture output to prevent it cluttering MCP logs
        logger.info("System TTS command executed successfully.")

    except FileNotFoundError as fnf_err:
        logger.error(f"TTS command failed: {fnf_err}")
        raise # Re-raise
    except subprocess.CalledProcessError as cpe:
        error_output = cpe.stderr.decode(errors='ignore').strip()
        logger.error(f"System TTS command failed with error code {cpe.returncode}.")
        if error_output:
            logger.error(f"TTS Error Output: {error_output}")
        raise RuntimeError(f"System TTS failed (code {cpe.returncode})") from cpe
    except Exception as e:
        logger.exception(f"An unexpected error occurred during system TTS: {e}")
        raise # Re-raise


# --- Helper Functions ---
def print_example_config(settings: Settings) -> None:
    """Print an example Cursor MCP configuration to stdout."""
    # Use the script's directory for the example command path
    script_path = os.path.abspath(__file__)
    script_dir = os.path.dirname(script_path)
    script_name = os.path.basename(script_path)

    example_args = [
        "--directory", script_dir, # Example using script's dir
        "run", script_name,
    ]
    # Add current settings to example args
    if settings.use_kokoro: example_args.append("--kokoro")
    if settings.use_streaming: example_args.append("--streaming")
    if settings.kokoro_model_path: example_args.extend(["--model-path", settings.kokoro_model_path])
    if settings.kokoro_voices_path: example_args.extend(["--voices-path", settings.kokoro_voices_path])
    example_args.extend(["--voice", settings.voice_name])
    example_args.extend(["--speed", str(settings.speech_speed)])
    example_args.extend(["--volume", str(settings.volume_level)])


    example_config = {
        "mcpServers": {
            "chatty": {
                # Assumes 'uvicorn' or similar ASGI runner is used if needed,
                # or just python for direct execution if FastMCP handles server internally.
                # Adjust command based on how FastMCP expects to be launched.
                # This example assumes direct python execution.
                "command": sys.executable, # Use current python interpreter
                "args": [script_path] + example_args[3:], # Pass script path and args
                # Alternative using 'uv' (if installed and script is runnable via uv run)
                # "command": "uv",
                # "args": example_args,
                "description": f"Chatty MCP server ({'Kokoro' if settings.use_kokoro else 'System'} TTS{' Streaming' if settings.use_kokoro and settings.use_streaming else ''})",
            }
        }
    }
    print("--- Example Cursor MCP Configuration ---")
    json.dump(example_config, sys.stdout, indent=2)
    print("\n--- End Example Configuration ---")

    print("\nInstallation notes:")
    print("1. Install required Python packages:")
    print("   pip install mcp-server soundfile sounddevice kokoro-onnx numpy")
    print("2. System Dependencies:")
    print("   - Linux: May require 'portaudio19-dev' (e.g., 'sudo apt update && sudo apt install portaudio19-dev').")
    print("   - Linux System TTS: Requires 'espeak-ng' or 'espeak' (e.g., 'sudo apt install espeak-ng').")
    print("   - macOS System TTS: Should work out-of-the-box.")
    print("3. Kokoro Model Files (if using --kokoro):")
    print("   - Download 'kokoro-v1.0.onnx' and 'voices-v1.0.bin' from:")
    print("     https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0")
    print("   - Place them in the same directory as this script, OR")
    print("   - Specify paths using --model-path and --voices-path arguments, OR")
    print("   - Set KOKORO_MODEL_PATH and KOKORO_VOICES_PATH environment variables.")

    print("\nUsage Features:")
    print("- Toggle TTS engine: --kokoro")
    print("- Toggle Kokoro streaming: --streaming (only applies if --kokoro is used)")
    print("- Adjust speed/volume: --speed <multiplier> --volume <0.0-1.0>")
    print("- Select Kokoro voice: --voice <voice_name>")
    print("- List known Kokoro voices: --list-voices")
    print("- Test TTS engines: --test-voice=[kokoro|system|both]")


def list_kokoro_voices(settings: Settings) -> None:
     """Initializes Kokoro and prints known/common voices."""
     try:
         # Initialize Kokoro to potentially load voice data, though API for listing is absent
         _ = init_kokoro(settings)
         print("\n🎤 Known Kokoro Voices (kokoro-onnx API does not currently list all):")
         # Hardcoded list based on common knowledge - replace if API becomes available
         print("  Common English:")
         print("    af_sarah (Female)")
         print("    af_nicole (Female)")
         print("    en_US-alan-medium (Male)")
         print("  -> Note: This list might be incomplete.")
         print("  -> Check kokoro-onnx documentation or source for potentially more voices.")
         print("     https://github.com/thewh1teagle/kokoro-onnx")
     except Exception as e:
         print(f"❌ Error initializing Kokoro to list voices: {str(e)}")
         # No need to exit(1), just failed to list


def test_tts_engines(settings: Settings) -> None:
    """Tests the configured TTS engine(s)."""
    test_message = "Hello, this is a test of the Chatty MCP text-to-speech system. Testing one, two, three."
    exit_code = 0

    async def run_kokoro_stream_test():
         print("\n  Testing Kokoro-ONNX (Streaming)...")
         await tts_kokoro_stream(test_message, settings)

    def run_kokoro_test():
        print("\n  Testing Kokoro-ONNX (Non-Streaming)...")
        tts_kokoro(test_message, settings)

    def run_system_test():
         print("\n  Testing System TTS...")
         tts_system(test_message, settings)

    # --- Kokoro Test ---
    if settings.use_kokoro:
         print(f"\n📢 Testing Kokoro TTS (voice: {settings.voice_name})")
         try:
             # Check explicitly specified paths first
             model_ok = os.path.exists(settings.kokoro_model_path) if settings.kokoro_model_path else False
             voices_ok = os.path.exists(settings.kokoro_voices_path) if settings.kokoro_voices_path else False
             # If not found, check current directory
             if not model_ok: model_ok = os.path.exists("kokoro-v1.0.onnx")
             if not voices_ok: voices_ok = os.path.exists("voices-v1.0.bin")

             if not model_ok or not voices_ok:
                 logger.warning("Kokoro model files not found at specified paths or current directory.")
                 # Provide download instructions (moved here from main logic)
                 print("  Please download 'kokoro-v1.0.onnx' and 'voices-v1.0.bin' from:")
                 print("  https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0")
                 print("  Place them in the script's directory or specify paths via arguments.")

             if settings.use_streaming:
                 asyncio.run(run_kokoro_stream_test())
             else:
                 run_kokoro_test()
             print("✅ Kokoro TTS test completed.")
         except Exception as e:
             print(f"❌ Error testing Kokoro TTS: {str(e)}")
             print("  Troubleshooting:")
             print("  - Ensure 'kokoro-onnx', 'sounddevice', 'soundfile', 'numpy' are installed.")
             if platform.system() == "Linux":
                 print("  - On Linux, ensure 'portaudio19-dev' is installed ('sudo apt install portaudio19-dev').")
             print("  - Verify model files are downloaded and accessible.")
             exit_code = 1 # Indicate failure

    # --- System Test ---
    else: # If not using kokoro, test system
         print("\n📢 Testing System TTS")
         try:
             run_system_test()
             print("✅ System TTS test completed.")
         except FileNotFoundError as e:
              print(f"❌ Error testing System TTS: {e}")
              print("  Troubleshooting:")
              if platform.system() == "Linux": print("  - Ensure 'espeak-ng' or 'espeak' is installed.")
              elif platform.system() == "Darwin": print("  - Ensure 'say' command is available.")
              exit_code = 1
         except Exception as e:
             print(f"❌ Error testing System TTS: {str(e)}")
             exit_code = 1

    sys.exit(exit_code)



# --- MCP Tool Definition ---
@mcp.tool()
async def speak(content: str, settings: Settings) -> str:
    """
    Synthesizes speech from text using the configured engine.

    Args:
        content: The text content to speak.
        settings: The application settings object.

    Returns:
        "done" on success, or an error message string on failure.
    """
    engine_name = "kokoro-onnx" if settings.use_kokoro else "system TTS"
    mode = "streaming" if settings.use_kokoro and settings.use_streaming else "non-streaming"
    voice_info = f", voice: {settings.voice_name}" if settings.use_kokoro else ""

    logger.info(
        f"TTS Request ({engine_name} {mode}{voice_info}, speed: {settings.speech_speed}, volume: {settings.volume_level}): "
        f"'{content[:50]}...'"
    )

    try:
        if settings.use_kokoro:
            if settings.use_streaming:
                await tts_kokoro_stream(content, settings)
            else:
                # Run synchronous function in a thread to avoid blocking event loop excessively
                # Note: sd.wait() inside tts_kokoro still blocks the thread, but not the main asyncio loop
                await asyncio.to_thread(tts_kokoro, content, settings)
        else:
             # System TTS uses subprocess, which can block. Run in thread.
             await asyncio.to_thread(tts_system, content, settings)

        logger.info("TTS completed successfully.")
        return "done"
    except FileNotFoundError as e:
         logger.error(f"TTS failed: Required command or file not found: {e}")
         return f"Error: TTS dependency not found - {e}"
    except sd.PortAudioError as pae:
         logger.error(f"TTS failed: Audio playback error: {pae}")
         return f"Error: Audio playback failed - {pae}"
    except RuntimeError as e:
         logger.error(f"TTS failed: {e}")
         return f"Error: {e}"
    except Exception as e:
        # Catch any other unexpected errors
        logger.exception(f"Unexpected error during TTS: {e}")
        return f"Error: An unexpected error occurred during TTS - {e}"


# --- Main Execution ---
def main():
    """Main entry point: Parses arguments and runs the MCP server or utility actions."""
    parser = argparse.ArgumentParser(
        description="Chatty MCP server for Text-to-Speech using System TTS or Kokoro-ONNX.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter # Show defaults in help
    )
    parser.add_argument(
        "--kokoro",
        action="store_true",
        help="Use kokoro-onnx TTS engine instead of system commands.",
    )
    parser.add_argument(
        "--streaming",
        action="store_true",
        default=True, # Default to streaming if Kokoro is used
        help="Use streaming mode with kokoro-onnx (starts playback faster). No effect if --kokoro is not used.",
    )
    parser.add_argument("--speed", type=float, default=1.5, help="Speech rate multiplier.")
    parser.add_argument(
        "--volume",
        type=float,
        default=1.0,
        help="Volume level from 0.0 (silent) to 1.0 (normal). Higher values might clip.",
    )
    parser.add_argument(
        "--voice",
        type=str,
        default="af_sarah",
        help="Voice to use with kokoro-onnx.",
    )
    parser.add_argument(
        "--model-path",
        type=str,
        default=None,
        help="Path to kokoro-onnx model file (e.g., kokoro-v1.0.onnx). Overrides default search.",
    )
    parser.add_argument(
        "--voices-path",
        type=str,
        default=None,
        help="Path to kokoro-onnx voices file (e.g., voices-v1.0.bin). Overrides default search.",
    )

    # Utility arguments
    util_group = parser.add_argument_group('Utility Actions (exit after running)')
    util_group.add_argument(
        "--list-voices",
        action="store_true",
        help="List known available voices in kokoro-onnx and exit.",
    )
    util_group.add_argument(
        "--config",
        action="store_true",
        help="Print an example Cursor MCP JSON configuration to stdout and exit.",
    )
    util_group.add_argument(
        "--test-voice",
        action="store_true",
        help="Test the configured TTS engine (kokoro or system) with a sample message and exit.",
    )

    args = parser.parse_args()

    # Create settings object, clamping volume
    settings = Settings(
         use_kokoro=args.kokoro,
         use_streaming=args.streaming if args.kokoro else False, # Streaming only applies to Kokoro
         speech_speed=max(0.1, args.speed), # Ensure minimum speed
         volume_level=max(0.0, min(2.0, args.volume)), # Allow slight boost, clamp 0-2
         voice_name=args.voice,
         kokoro_model_path=args.model_path,
         kokoro_voices_path=args.voices_path,
    )

    # Handle utility actions first
    if args.list_voices:
        list_kokoro_voices(settings)
        sys.exit(0)

    if args.config:
        print_example_config(settings)
        sys.exit(0)

    if args.test_voice:
        test_tts_engines(settings)
        # test_tts_engines will call sys.exit()

    # --- Run the MCP Server ---
    engine_name = "kokoro-onnx" if settings.use_kokoro else "system TTS"
    streaming_mode = " (streaming)" if settings.use_kokoro and settings.use_streaming else ""
    voice_info = f" with voice '{settings.voice_name}'" if settings.use_kokoro else ""

    logger.info(
        f"Starting Chatty MCP server with {engine_name}{streaming_mode}{voice_info}"
    )
    logger.info(f"  Settings: Speed={settings.speech_speed}, Volume={settings.volume_level}")
    if settings.kokoro_model_path: logger.info(f"  Kokoro Model Path: {settings.kokoro_model_path}")
    if settings.kokoro_voices_path: logger.info(f"  Kokoro Voices Path: {settings.kokoro_voices_path}")


    # Inject settings into the speak tool context if FastMCP supports it easily,
    # otherwise pass it explicitly if needed, or rely on module-level access
    # for simplicity in this script.
    # Assuming FastMCP allows passing context or the tool can access 'settings' from module scope:
    # Let's redefine the speak tool slightly to capture settings from the outer scope
    # This isn't the cleanest dependency injection but works for a single script.

    @mcp.tool()
    async def speak_tool(content: str) -> str:
         """
         (MCP Tool Wrapper) Synthesizes speech from text.

         Args:
             content: The text content to speak.

         Returns:
             "done" on success, or an error message string on failure.
         """
         # Call the main speak function, passing the settings from the outer scope
         return await speak(content, settings)


    try:
         # Initialize Kokoro once before starting server if it will be used
         if settings.use_kokoro:
             init_kokoro(settings)

         mcp.run(transport="stdio") # Or other transports as needed

    except KeyboardInterrupt:
         logger.info("Server stopped by user (KeyboardInterrupt).")
    except Exception as e:
         logger.exception(f"MCP server failed: {e}")
    finally:
         logger.info("Chatty MCP server stopped.")
         # Optional: Cleanup resources if needed (e.g., close Kokoro explicitly if it has a close method)
         # if settings.kokoro_synth and hasattr(settings.kokoro_synth, 'close'):
         #     settings.kokoro_synth.close()


if __name__ == "__main__":
    # Set loop policy for Windows if needed for asyncio + subprocess/sounddevice interaction
    if platform.system() == "Windows":
        # ProactorEventLoop might be needed for subprocesses, but Selector might be better for network/stdio
        # Default usually works, but uncomment if encountering loop issues.
        # asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        pass
    main()
