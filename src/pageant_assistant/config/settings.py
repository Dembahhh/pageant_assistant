import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root (PAGEANT_ASSISTANT/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# --- LLM Configuration ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.3-70b-versatile"

# Temperature defaults per agent role
TEMPERATURE = {
    "supervisor": 0.0,       # Deterministic routing decisions
    "question_analysis": 0.2, # Precise classification
    "drafting": 0.7,          # Creative but focused
    "critic": 0.1,            # Consistent scoring
    "rewrite": 0.6,           # Creative within constraints
    "exemplar": 0.75,         # Slightly higher creativity for showcase answer
}

# --- Time Limits ---
VALID_TIME_LIMITS = [20, 30, 40]  # seconds
DEFAULT_TIME_LIMIT = 30

# Approximate words-per-second for spoken answers
WORDS_PER_SECOND = 2.5

# --- Style Presets ---
STYLE_PRESETS = {
    "structured_narrative": "Structured Narrative (Catriona-style)",
    "values_shared_agency": "Values + Shared Agency (Zozibini-style)",
}
DEFAULT_STYLE = "structured_narrative"

# --- Paths ---
DATA_DIR = PROJECT_ROOT / "data"
CHROMA_DIR = DATA_DIR / "chroma"
RUBRICS_DIR = PROJECT_ROOT / "src" / "pageant_assistant" / "rubrics"
QUESTIONS_DIR = DATA_DIR / "questions"
PERSONAS_DIR = DATA_DIR / "personas"
EXEMPLARS_DIR = DATA_DIR / "exemplars"

# --- Rubric ---
DEFAULT_RUBRIC = "miss_universe"

# --- Voice Configuration ---
STT_MODEL = "whisper-large-v3-turbo"
TTS_MODEL = "canopylabs/orpheus-v1-english"
TTS_VOICE = "hannah"
TTS_RESPONSE_FORMAT = "wav"

# --- LangSmith (optional) ---
LANGSMITH_ENABLED = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
