"""Voice I/O: speech-to-text (Groq Whisper) and text-to-speech (Groq PlayAI)."""

from groq import Groq
from pageant_assistant.config.settings import (
    GROQ_API_KEY,
    STT_MODEL,
    TTS_MODEL,
    TTS_VOICE,
    TTS_RESPONSE_FORMAT,
)


def transcribe_audio(audio_bytes: bytes, filename: str = "answer.wav") -> str:
    """Transcribe audio bytes to text using Groq Whisper.

    Args:
        audio_bytes: Raw audio data (WAV format from st.audio_input).
        filename: Filename hint for the API.

    Returns:
        Transcribed text string.
    """
    client = Groq(api_key=GROQ_API_KEY)
    transcription = client.audio.transcriptions.create(
        file=(filename, audio_bytes),
        model=STT_MODEL,
        language="en",
    )
    return transcription.text


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
