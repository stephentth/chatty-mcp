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

        model_path = None
        voices_path = None

        # Search locations in order of priority
        search_locations = [
            os.getcwd(),
            os.path.join(os.path.expanduser("~"), ".kokoro_models"),
            os.path.join(os.path.expanduser("~"), ".chatty-mcp"),
        ]

        for location in search_locations:
            if not os.path.exists(location):
                continue

            loc_model_path = os.path.join(location, model_filename)
            if os.path.exists(loc_model_path) and model_path is None:
                model_path = loc_model_path
                logger.info(f"Using model from {model_path}")

            loc_voices_path = os.path.join(location, voices_filename)
            if os.path.exists(loc_voices_path) and voices_path is None:
                voices_path = loc_voices_path
                logger.info(f"Using voices from {voices_path}")

            if model_path is not None and voices_path is not None:
                break

        # Environment variables as final fallback
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

        if model_path is None or voices_path is None:
            error_msg = "Kokoro model files not found in any configured locations"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        logger.info(f"Initializing Kokoro with model={model_path}, voices={voices_path}")
        kokoro_synth = Kokoro(model_path, voices_path)

    return kokoro_synth


async def tts_kokoro_stream(content: str, speech_speed: float, volume: float = 1.0, voice: str = "af_sarah") -> None:
    logger.info(f"Using kokoro-onnx streaming engine with voice: {voice}")

    kokoro = init_kokoro()

    stream = kokoro.create_stream(
        text=content,
        voice=voice,
        speed=speech_speed,
        lang="en-us",
    )

    chunk_count = 0
    async for samples, sample_rate in stream:
        chunk_count += 1
        logger.info(f"Playing audio stream chunk {chunk_count}...")

        if volume != 1.0:
            samples = samples * volume

        sd.play(samples, sample_rate)
        sd.wait()  # Wait until audio finishes playing

    logger.info(f"Finished playing {chunk_count} audio stream chunks")


def tts_kokoro(content: str, speech_speed: float, volume: float = 1.0, voice: str = "af_sarah") -> None:
    logger.info(f"Using kokoro-onnx engine with voice: {voice}")

    kokoro = init_kokoro()

    # Generate audio with kokoro-onnx
    audio, sample_rate = kokoro.create(
        text=content,
        voice=voice,
        speed=speech_speed,
        lang="en-us",
    )

    if volume != 1.0:
        audio = audio * volume

    temp_file = "temp_audio.wav"
    sf.write(temp_file, audio, sample_rate)

    try:
        play_audio_file(temp_file)
    finally:
        try:
            os.remove(temp_file)
        except:
            pass
