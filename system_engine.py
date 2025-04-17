import logging
import platform
import subprocess

logger = logging.getLogger("chatty-mcp")


def tts_system(content: str, speech_speed: float, volume: float = 1.0) -> None:
    """Generate speech using system TTS commands

    This function uses the appropriate text-to-speech command based on the operating system.

    Args:
        content: Text to convert to speech
        speech_speed: Speed multiplier (1.0 = normal speed)
        volume: Volume level from 0.0 to 1.0

    Raises:
        RuntimeError: If the operating system is not supported
        subprocess.CalledProcessError: If the TTS command fails
    """
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


def test_system_voice(test_message: str, speech_speed: float, volume: float = 1.0) -> bool:
    """Test the system TTS engine with a sample message

    Args:
        test_message: Text to convert to speech
        speech_speed: Speed multiplier
        volume: Volume level

    Returns:
        bool: True if the test succeeded, False otherwise
    """
    try:
        logger.info("\n📢 Testing system TTS engine...")
        tts_system(test_message, speech_speed, volume)
        logger.info("✅ System TTS test completed successfully.")
        return True
    except Exception as e:
        logger.error(f"❌ Error testing system TTS: {str(e)}")
        return False
