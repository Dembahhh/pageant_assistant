from typing import Any, TypedDict


class CriticScoresState(TypedDict, total=False):
    """Mirrors CriticOutput.model_dump() shape for static checking."""

    overall_score: float
    dimension_scores: list[dict[str, Any]]
    time_fit_estimate_words: int
    top_fixes: list[dict[str, str]]
    genericness_flags: list[str]
    risk_flags: list[str]
    exemplar_reference: dict[str, Any] | None


class ExemplarRefState(TypedDict, total=False):
    """Mirrors ExemplarReference.model_dump() shape."""

    match_type: str
    exemplar_id: str
    structural_takeaways: list[str]


class RefinerState(TypedDict, total=False):
    """State that flows through the Milestone 1 Q&A Refiner graph.

    Each node reads the fields it needs and writes back its outputs.
    `total=False` makes all fields optional so nodes can add them incrementally.
    """

    # --- Inputs (set at graph invocation) ---
    question: str  # The pageant question to answer
    raw_answer: str  # The contestant's draft answer
    time_limit: int  # Target answer length in seconds (20, 30, 40)
    style_preset: str  # "structured_narrative" or "values_shared_agency"

    # --- Input metadata ---
    question_id: str  # ID from question bank (for tracking/dedup)
    input_mode: str  # "text" or "voice" (for UI display)

    # --- Persona context (set at graph invocation, optional) ---
    persona_id: str  # ID of the active persona
    persona_context: str  # Pre-formatted persona text block for prompts

    # --- Intermediate outputs (set by nodes) ---
    question_analysis: str  # From question understanding node
    draft_answer: str  # From drafting node
    critique: str  # From critic node

    # --- Final outputs ---
    refined_answer: str  # The polished on-stage answer
    coach_report: str  # Rubric scores + practice notes
    exemplar_answer: str  # Model winning answer for reference

    # --- Structured scoring (M3) ---
    critic_scores: CriticScoresState  # Parsed CriticOutput as dict (from model_dump)
    rubric_name: str  # Which rubric was used (e.g. "miss_universe")
    exemplar_ref: ExemplarRefState  # Matched exemplar metadata (if any)

    # --- RAG evidence (M4) ---
    rag_evidence: str  # Formatted evidence block injected into prompts (None = not retrieved)
    rag_question_type: str  # Question type inferred by rag_research (e.g. "advocacy")
    claim_flags: list[str]  # Unsupported factual claims flagged by claim_verifier

    # --- Control ---
    iteration_count: int  # Tracks critic->rewrite loops (max 2)
