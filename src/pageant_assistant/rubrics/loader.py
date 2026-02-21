"""Rubric loader: load rubric definitions from JSON and format for prompts."""

import json
from pathlib import Path

from pageant_assistant.config.settings import RUBRICS_DIR


# Fallback rubric used when the JSON file is missing or corrupted.
_DEFAULT_DIMENSIONS = [
    {"name": "Directness & Clarity", "weight": 1.0, "description": "First sentence answers the question directly."},
    {"name": "Structure & Flow", "weight": 1.0, "description": "Logical arc from answer to close."},
    {"name": "Authenticity & Specificity", "weight": 1.2, "description": "Personal and specific, not generic."},
    {"name": "Leadership & Agency", "weight": 1.0, "description": "Shows vision or action."},
    {"name": "Worldview & Relevance", "weight": 0.8, "description": "Global framing when appropriate."},
    {"name": "Closing Strength", "weight": 1.0, "description": "Memorable, quotable close."},
    {"name": "Conciseness & Time-Fit", "weight": 1.0, "description": "Within word budget."},
    {"name": "Credibility & Safety", "weight": 0.8, "description": "No unsupported claims."},
]


def load_rubric(pageant: str = "miss_universe") -> dict:
    """Load a rubric by pageant name. Falls back to defaults if file missing."""
    path = RUBRICS_DIR / f"{pageant}.json"
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if "dimensions" in data:
                return data
        except (json.JSONDecodeError, KeyError):
            pass
    return {
        "pageant": pageant.replace("_", " ").title(),
        "version": "fallback",
        "dimensions": _DEFAULT_DIMENSIONS,
        "cap_rules": [],
        "genericness_signals": [],
    }


def format_rubric_for_prompt(rubric: dict) -> str:
    """Format rubric dimensions into a prompt-injectable string."""
    lines = []
    for i, dim in enumerate(rubric["dimensions"], 1):
        weight_note = f" (weight: {dim['weight']}x)" if dim.get("weight", 1.0) != 1.0 else ""
        lines.append(f"{i}. **{dim['name']}**{weight_note} — {dim['description']}")

    cap_lines = []
    for rule in rubric.get("cap_rules", []):
        cap_lines.append(
            f"- If {rule['if_dimension']} scores below {rule['below']}, "
            f"cap overall score at {rule['then_max_overall']}."
        )

    result = "SCORING DIMENSIONS (score each 0-10):\n" + "\n".join(lines)
    if cap_lines:
        result += "\n\nCAP RULES:\n" + "\n".join(cap_lines)
    return result
