import logging
import os
import time

from google import genai
from google.genai import types


logger = logging.getLogger(__name__)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
STT_MODEL = os.getenv("GEMINI_STT_MODEL", "gemini-2.5-flash")


def transcribe_audio_with_gemini(
    audio_bytes: bytes,
    mime_type: str = "audio/mp4",
) -> str:
    """Transcribe a small audio recording without a second Files API upload."""
    started_at = time.perf_counter()
    response = client.models.generate_content(
        model=STT_MODEL,
        contents=[
            types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
            "한국어 음성을 정확히 받아쓰고, 설명 없이 변환된 문장만 출력해.",
        ],
    )
    logger.info(
        "voice_stt_complete model=%s audio_size_bytes=%d elapsed_ms=%.1f",
        STT_MODEL,
        len(audio_bytes),
        (time.perf_counter() - started_at) * 1000,
    )
    return response.text.strip()
