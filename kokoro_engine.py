import os
import logging
import asyncio
import platform
import subprocess
import soundfile as sf
import sounddevice as sd
from kokoro_onnx import Kokoro

logger = logging.getLogger("chatty-mcp")

# Kokoro globals
kokoro_synth = None


def play_audio_file(file_path: str) -> None:
    """Play an audio file using the appropriate system command"""
    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.run(["afplay", file_path], check=True)
        elif system == "Linux":
            subprocess.run(["aplay", file_path], check=True)
        else:
            logger.warning(f"Unsupported OS for audio playback: {system}")
    except Exception as e:
        logger.error(f"Error playing audio file {file_path}: {str(e)}")
        raise


def init_kokoro() -> Kokoro:
    """Initialize the Kokoro synthesizer if not already done"""
    global kokoro_synth

    if kokoro_synth is None:
        logger.info("Initializing kokoro-onnx")

        # Default filenames
        model_filename = "kokoro-v1.0.onnx"
        voices_filename = "voices-v1.0.bin"

        # Search for model files in the following locations (in order of priority):
        # 1. Current directory
        model_path = model_filename if os.path.exists(model_filename) else None
        voices_path = voices_filename if os.path.exists(voices_filename) else None

        # 2. User's home directory under .kokoro_models
        if model_path is None or voices_path is None:
            home_dir = os.path.expanduser("~")
            kokoro_models_dir = os.path.join(home_dir, ".kokoro_models")

            if os.path.exists(kokoro_models_dir):
                home_model_path = os.path.join(kokoro_models_dir, model_filename)
                home_voices_path = os.path.join(kokoro_models_dir, voices_filename)

                if os.path.exists(home_model_path) and model_path is None:
                    model_path = home_model_path
                    logger.info(f"Using model from {model_path}")

                if os.path.exists(home_voices_path) and voices_path is None:
                    voices_path = home_voices_path
                    logger.info(f"Using voices from {voices_path}")

        # 3. Environment variables
        if model_path is None:
            env_model_path = os.environ.get("CHATTY_MCP_KOKORO_MODEL_PATH")
            if env_model_path and os.path.exists(env_model_path):
                model_path = env_model_path
                logger.info(f"Using model from environment variable: {model_path}")

        if voices_path is None:
            env_voices_path = os.environ.get("CHATTY_MCP_KOKORO_VOICE_PATH")
            if env_voices_path and os.path.exists(env_voices_path):
                voices_path = env_voices_path
                logger.info(f"Using voices from environment variable: {voices_path}")

        # 4. Fallback to default paths provided by Kokoro-ONNX
        if model_path is None or voices_path is None:
            logger.warning("Model files not found in configured locations. Using kokoro-onnx default paths.")
            model_path = None
            voices_path = None

        # Initialize the Kokoro synthesizer
        logger.info(f"Initializing Kokoro with model={model_path}, voices={voices_path}")
        kokoro_synth = Kokoro(model_path, voices_path)

    return kokoro_synth


async def tts_kokoro_stream(content: str, speech_speed: float, volume: float = 1.0, voice: str = "af_sarah") -> None:
    """Use Kokoro-ONNX streaming API for text-to-speech with direct audio playback

    This function generates and plays audio in chunks as they become available,
    providing faster response time compared to the non-streaming version.

    Args:
        content: Text to convert to speech
        speech_speed: Speed multiplier (1.0 = normal speed)
        volume: Volume level from 0.0 to 1.0
        voice: Voice identifier to use for speech
    """
    logger.info(f"Using kokoro-onnx streaming engine with voice: {voice}")

    kokoro = init_kokoro()

    # Create audio stream from text
    stream = kokoro.create_stream(
        text=content,
        voice=voice,
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


def tts_kokoro(content: str, speech_speed: float, volume: float = 1.0, voice: str = "af_sarah") -> None:
    """Use Kokoro-ONNX for text-to-speech with full audio generation before playback

    This function generates the complete audio before playing it.

    Args:
        content: Text to convert to speech
        speech_speed: Speed multiplier (1.0 = normal speed)
        volume: Volume level from 0.0 to 1.0
        voice: Voice identifier to use for speech
    """
    logger.info(f"Using kokoro-onnx engine with voice: {voice}")

    # Get the initialized Kokoro instance
    kokoro = init_kokoro()

    # Generate audio with kokoro-onnx
    audio, sample_rate = kokoro.create(
        text=content,
        voice=voice,
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
