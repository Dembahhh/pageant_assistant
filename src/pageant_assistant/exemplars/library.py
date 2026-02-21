"""Exemplar library: load and search real winning answers for structural reference."""

import json
from typing import Optional

from pageant_assistant.config.settings import EXEMPLARS_DIR

EXEMPLARS_FILE = EXEMPLARS_DIR / "exemplar_library.json"


def load_exemplars() -> list[dict]:
    """Load all exemplars from the JSON library."""
    if not EXEMPLARS_FILE.exists():
        return []
    try:
        data = json.loads(EXEMPLARS_FILE.read_text(encoding="utf-8"))
        return data.get("exemplars", [])
    except (json.JSONDecodeError, KeyError):
        return []


def find_exemplar(
    question_type: str,
    theme_tags: Optional[list[str]] = None,
    pageant: str = "Miss Universe",
) -> Optional[dict]:
    """Find the closest matching exemplar by question type and theme overlap.

    Matching priority:
    1. Exact question_type match + most overlapping theme_tags
    2. Exact question_type match (any)
    3. None if no match
    """
    exemplars = load_exemplars()
    if not exemplars:
        return None

    # Filter by pageant
    candidates = [e for e in exemplars if e.get("pageant") == pageant]
    if not candidates:
        candidates = exemplars

    # Filter by question type
    type_matches = [e for e in candidates if e.get("question_type") == question_type]

    if type_matches and theme_tags:
        # Rank by tag overlap
        tag_set = set(t.lower() for t in theme_tags)

        def tag_overlap(ex: dict) -> int:
            ex_tags = set(t.lower() for t in ex.get("theme_tags", []))
            return len(tag_set & ex_tags)

        type_matches.sort(key=tag_overlap, reverse=True)
        return type_matches[0]

    if type_matches:
        return type_matches[0]

    # No type match — return the most recent exemplar as a loose reference
    candidates.sort(key=lambda e: e.get("year", 0), reverse=True)
    return candidates[0] if candidates else None


def format_exemplar_reference(exemplar: Optional[dict]) -> str:
    """Format exemplar structural notes for prompt injection.

    Only injects structural takeaways — never the actual answer text.
    """
    if not exemplar:
        return ""

    lines = [
        "EXEMPLAR REFERENCE (for structural guidance only — do NOT copy wording):",
        f"- Source: {exemplar.get('winner_name', 'Unknown')}, "
        f"{exemplar.get('pageant', '')} {exemplar.get('year', '')}",
        f"- Question type: {exemplar.get('question_type', 'unknown')}",
        f"- Structural notes: {exemplar.get('structural_notes', 'N/A')}",
    ]
    return "\n".join(lines)
