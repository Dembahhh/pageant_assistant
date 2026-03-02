import os
from pathlib import Path

from dotenv import load_dotenv


def _find_project_root() -> Path:
    """Walk up from this file until pyproject.toml is found."""
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").exists():
            return parent
    raise FileNotFoundError(
        "Could not locate project root (no pyproject.toml found above settings.py)"
    )


PROJECT_ROOT = _find_project_root()
load_dotenv(PROJECT_ROOT / ".env")

# --- LLM Configuration ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    # Fallback to Streamlit Community Cloud secrets management
    try:
        import streamlit as st

        GROQ_API_KEY = st.secrets.get("GROQ_API_KEY")
    except Exception:
        pass
GROQ_MODEL = "llama-3.3-70b-versatile"

# Temperature defaults per agent role
TEMPERATURE = {
    "supervisor": 0.0,  # Deterministic routing decisions
    "question_analysis": 0.2,  # Precise classification
    "drafting": 0.7,  # Creative but focused
    "critic": 0.1,  # Consistent scoring
    "rewrite": 0.6,  # Creative within constraints
    "exemplar": 0.75,  # Slightly higher creativity for showcase answer
}

# --- Time Limits ---
VALID_TIME_LIMITS = [20, 30, 40]  # seconds
DEFAULT_TIME_LIMIT = 30

# --- Style Presets ---
# Each preset has a display name and a words-per-second rate for word budgets.
# Bold/punchy styles use shorter sentences delivered faster; warm/diplomatic
# styles use longer measured sentences, so fewer words fit the same time limit.
STYLE_PRESETS = {
    "structured_narrative": "Structured Narrative (Catriona-style)",
    "values_shared_agency": "Values + Shared Agency (Zozibini-style)",
    "bold_punchy": "Bold & Punchy (Harnaaz-style)",
    "warm_diplomatic": "Warm & Diplomatic (Andrea-style)",
    "policy_grounded": "Policy-Grounded (R'Bonney-style)",
}
DEFAULT_STYLE = "structured_narrative"

# Words-per-second by style preset — used to calculate word budgets from time limits.
WORDS_PER_SECOND: dict[str, float] = {
    "structured_narrative": 2.5,
    "values_shared_agency": 2.5,
    "bold_punchy": 3.0,
    "warm_diplomatic": 2.3,
    "policy_grounded": 2.5,
}

# --- Paths ---
DATA_DIR = PROJECT_ROOT / "data"
CHROMA_DIR = DATA_DIR / "chroma"
RUBRICS_DIR = PROJECT_ROOT / "src" / "pageant_assistant" / "rubrics"
QUESTIONS_DIR = DATA_DIR / "questions"
PERSONAS_DIR = DATA_DIR / "personas"
EXEMPLARS_DIR = DATA_DIR / "exemplars"

# Ensure required data directories exist on import
for _d in (DATA_DIR, CHROMA_DIR, QUESTIONS_DIR, PERSONAS_DIR, EXEMPLARS_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# --- Rubric ---
DEFAULT_RUBRIC = "miss_universe"

# --- RAG ---
RAG_COLLECTION_NAME = "pageant_evidence"

# --- Voice Configuration ---
STT_MODEL = "whisper-large-v3-turbo"
TTS_MODEL = "canopylabs/orpheus-v1-english"
TTS_VOICE = "hannah"
TTS_RESPONSE_FORMAT = "wav"

# --- LangSmith (optional) ---
LANGSMITH_ENABLED = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
