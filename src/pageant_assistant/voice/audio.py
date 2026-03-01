"""Voice I/O: speech-to-text (Groq Whisper) and text-to-speech (Groq PlayAI).

Both functions use ``requests`` (urllib3) instead of the Groq SDK (httpx)
because httpx fails on Streamlit Community Cloud with Python 3.13.
"""

import requests as _req

from pageant_assistant.config.settings import (
    GROQ_API_KEY,
    STT_MODEL,
    TTS_MODEL,
    TTS_RESPONSE_FORMAT,
    TTS_VOICE,
)

_GROQ_STT_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
_GROQ_TTS_URL = "https://api.groq.com/openai/v1/audio/speech"


def transcribe_audio(audio_bytes: bytes, filename: str = "answer.webm") -> str:
    """Transcribe audio bytes to text using Groq Whisper.

    Args:
        audio_bytes: Raw audio data from st.audio_input (browser records WebM).
        filename: Filename hint — extension tells Groq the audio format.

    Returns:
        Transcribed text string.
    """
    resp = _req.post(
        _GROQ_STT_URL,
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
        files={"file": (filename, audio_bytes)},
        data={"model": STT_MODEL, "language": "en"},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["text"]


def synthesize_speech(text: str, voice: str | None = None) -> bytes:
    """Convert text to speech audio using Groq TTS.

    Args:
        text: The text to speak.
        voice: Override the default voice.

    Returns:
        Audio bytes ready for st.audio().
    """
    resp = _req.post(
        _GROQ_TTS_URL,
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": TTS_MODEL,
            "voice": voice or TTS_VOICE,
            "input": text,
            "response_format": TTS_RESPONSE_FORMAT,
        },
        timeout=120,
    )
    resp.raise_for_status()
    return resp.content
