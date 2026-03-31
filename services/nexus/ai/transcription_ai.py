"""Whisper-based audio transcription via OpenAI API."""

import io
import logging
import os

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".m4a", ".mp3", ".mp4", ".wav"}
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB


def check_openai_available() -> bool:
    """Return True if OPENAI_API_KEY is configured."""
    return bool(os.getenv("OPENAI_API_KEY"))


def transcribe_audio(file_bytes: bytes, filename: str) -> str:
    """Transcribe audio bytes using OpenAI Whisper API.

    Args:
        file_bytes: Raw audio bytes.
        filename: Original filename (used to infer format by Whisper).

    Returns:
        Transcript string.

    Raises:
        RuntimeError: On transcription failure.
    """
    from openai import OpenAI  # lazy import — only needed when called

    client = OpenAI()
    audio_file = io.BytesIO(file_bytes)
    audio_file.name = filename  # Whisper infers codec from the filename extension

    try:
        result = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
        )
        logger.info("Whisper transcribed %d chars from %s", len(result.text), filename)
        return result.text
    except Exception as e:
        logger.error("Whisper transcription failed for %s: %s", filename, e)
        raise RuntimeError(f"語音轉錄失敗：{e}") from e
