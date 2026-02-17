from typing import TypedDict


class RefinerState(TypedDict, total=False):
    """State that flows through the Milestone 1 Q&A Refiner graph.

    Each node reads the fields it needs and writes back its outputs.
    `total=False` makes all fields optional so nodes can add them incrementally.
    """

    # --- Inputs (set at graph invocation) ---
    question: str           # The pageant question to answer
    raw_answer: str         # The contestant's draft answer
    time_limit: int         # Target answer length in seconds (20, 30, 40)
    style_preset: str       # "structured_narrative" or "values_shared_agency"

    # --- Input metadata ---
    question_id: str        # ID from question bank (for tracking/dedup)
    input_mode: str         # "text" or "voice" (for UI display)

    # --- Intermediate outputs (set by nodes) ---
    question_analysis: str  # From question understanding node
    draft_answer: str       # From drafting node
    critique: str           # From critic node

    # --- Final outputs ---
    refined_answer: str     # The polished on-stage answer
    coach_report: str       # Rubric scores + practice notes
    exemplar_answer: str    # Model winning answer for reference

    # --- Control ---
    iteration_count: int    # Tracks critic->rewrite loops (max 2)
