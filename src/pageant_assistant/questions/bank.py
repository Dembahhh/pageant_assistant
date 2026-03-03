"""Question bank: load, filter, and randomly select pageant questions."""

import functools
import json
import random

from pageant_assistant.config.settings import QUESTIONS_DIR

QUESTIONS_FILE = QUESTIONS_DIR / "question_bank.json"


@functools.lru_cache(maxsize=1)
def load_questions() -> tuple[dict, ...]:
    """Load the full question bank from JSON (cached for process lifetime)."""
    with open(QUESTIONS_FILE, encoding="utf-8") as f:
        data = json.load(f)
    return tuple(data["questions"])


def get_random_question(
    pageant_type: str | None = None,
    question_type: str | None = None,
    difficulty: str | None = None,
    exclude_ids: set[str] | None = None,
) -> dict:
    """Return one random question, optionally filtered.

    Args:
        pageant_type: Filter by pageant (e.g. "miss_universe"). None = any.
        question_type: Filter by type (e.g. "personal"). None = any.
        difficulty: Filter by difficulty (e.g. "beginner"). None = any.
        exclude_ids: Set of question IDs already shown this session.

    Returns:
        A question dict with id, text, pageant_type, question_type, difficulty, tags.
    """
    questions = load_questions()

    if pageant_type and pageant_type != "any":
        questions = [q for q in questions if q["pageant_type"] == pageant_type]
    if question_type and question_type != "any":
        questions = [q for q in questions if q["question_type"] == question_type]
    if difficulty and difficulty != "any":
        questions = [q for q in questions if q["difficulty"] == difficulty]
    if exclude_ids:
        questions = [q for q in questions if q["id"] not in exclude_ids]

    # Fallback: if all questions exhausted or filters too narrow, reset
    if not questions:
        questions = load_questions()
        if not questions:
            raise RuntimeError("Question bank is empty or could not be loaded.")

    return random.choice(questions)


def get_filter_options() -> dict:
    """Return available filter values for UI dropdowns."""
    return {
        "pageant_type": [
            ("any", "Any Pageant"),
            ("miss_universe", "Miss Universe"),
            ("miss_world", "Miss World"),
            ("miss_usa", "Miss USA"),
            ("miss_grand", "Miss Grand International"),
            ("miss_earth", "Miss Earth"),
            ("miss_charm", "Miss Charm"),
            ("general", "General"),
        ],
        "question_type": [
            ("any", "Any Type"),
            ("personal", "Personal"),
            ("issues_based", "Issues-Based"),
            ("advocacy", "Advocacy"),
            ("leadership", "Leadership"),
            ("fun_creative", "Fun / Creative"),
        ],
        "difficulty": [
            ("any", "Any Difficulty"),
            ("beginner", "Beginner"),
            ("intermediate", "Intermediate"),
            ("advanced", "Advanced"),
        ],
    }
