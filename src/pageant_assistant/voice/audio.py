"""Voice I/O: speech-to-text (Groq Whisper) and text-to-speech (Groq PlayAI)."""

from groq import Groq

from pageant_assistant.config.settings import (
    GROQ_API_KEY,
    STT_MODEL,
    TTS_MODEL,
    TTS_RESPONSE_FORMAT,
    TTS_VOICE,
)


def transcribe_audio(audio_bytes: bytes, filename: str = "answer.webm") -> str:
    """Transcribe audio bytes to text using Groq Whisper.

    Uses requests (urllib3) directly instead of the Groq SDK (httpx) because
    httpx's multipart upload fails on some hosted environments (SCC/Python 3.13).

    Args:
        audio_bytes: Raw audio data from st.audio_input (browser records WebM).
        filename: Filename hint — extension tells Groq the audio format.

    Returns:
        Transcribed text string.
    """
    import requests as _req

    resp = _req.post(
        "https://api.groq.com/openai/v1/audio/transcriptions",
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
        WAV audio bytes ready for st.audio().
    """
    client = Groq(api_key=GROQ_API_KEY)
    response = client.audio.speech.create(
        model=TTS_MODEL,
        voice=voice or TTS_VOICE,
        input=text,
        response_format=TTS_RESPONSE_FORMAT,
    )
    return response.read()
