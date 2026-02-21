"""Persona manager: CRUD operations + prompt formatting for contestant personas."""

import json
from pathlib import Path
from typing import Optional

from pydantic import ValidationError

from pageant_assistant.config.settings import PERSONAS_DIR
from pageant_assistant.personas.models import Persona


def _persona_path(persona_id: str) -> Path:
    """Return the file path for a given persona ID."""
    return PERSONAS_DIR / f"{persona_id}.json"


def _ensure_dir() -> None:
    """Create the personas directory if it does not exist."""
    PERSONAS_DIR.mkdir(parents=True, exist_ok=True)


def list_personas() -> list[dict]:
    """Return a list of {id, name, country} for all saved personas.

    Sorted alphabetically by name. Used for the sidebar dropdown.
    """
    _ensure_dir()
    personas = []
    for f in PERSONAS_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            personas.append({
                "id": data["id"],
                "name": data["name"],
                "country": data.get("country", ""),
            })
        except (json.JSONDecodeError, KeyError):
            continue
    return sorted(personas, key=lambda p: p["name"].lower())


def load_persona(persona_id: str) -> Optional[Persona]:
    """Load a single persona by ID. Returns None if not found or invalid."""
    path = _persona_path(persona_id)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return Persona(**data)
    except (json.JSONDecodeError, ValidationError):
        return None


def save_persona(persona: Persona) -> Persona:
    """Save a persona to disk. Creates or overwrites the file."""
    _ensure_dir()
    path = _persona_path(persona.id)
    path.write_text(persona.model_dump_json(indent=2), encoding="utf-8")
    return persona


def delete_persona(persona_id: str) -> bool:
    """Delete a persona file. Returns True if deleted, False if not found."""
    path = _persona_path(persona_id)
    if path.exists():
        path.unlink()
        return True
    return False


def format_persona_context(persona: Persona) -> str:
    """Format a Persona into a text block for prompt injection.

    Returns an empty string if persona is None.
    """
    if persona is None:
        return ""

    lines = [
        "CONTESTANT PROFILE:",
        f"- Name: {persona.name}",
        f"- Country: {persona.country}",
        f"- Platform/Advocacy: {persona.platform}",
        f"- Core Values: {', '.join(persona.values)}",
    ]

    if persona.personal_stories:
        lines.append("")
        lines.append(
            "PERSONAL STORIES (draw from these for authentic personal anchors):"
        )
        for i, story in enumerate(persona.personal_stories, 1):
            lines.append(f'{i}. "{story.title}" -- {story.text}')
            lines.append(f"   Key lesson: {story.key_lesson}")

    return "\n".join(lines)
