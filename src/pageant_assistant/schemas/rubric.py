"""Pydantic models for the Milestone 3 structured critic output."""

from pydantic import BaseModel, Field


class DimensionScore(BaseModel):
    """Score for a single rubric dimension."""

    name: str
    score: float = Field(ge=0, le=10)
    reason: str


class CriticFix(BaseModel):
    """A concrete, actionable fix suggested by the critic."""

    type: str       # e.g. "rewrite_sentence", "add_anchor", "strengthen_close"
    target: str     # which dimension or part of the answer this addresses
    instruction: str


class ExemplarReference(BaseModel):
    """Reference to a matched exemplar from the library."""

    match_type: str = "none"       # "exact", "closest_match", "none"
    exemplar_id: str = ""
    structural_takeaways: list[str] = Field(default_factory=list)


class CriticOutput(BaseModel):
    """Full structured output from the critic node."""

    overall_score: float = Field(ge=0, le=10)
    dimension_scores: list[DimensionScore]
    time_fit_estimate_words: int = 0
    top_fixes: list[CriticFix] = Field(default_factory=list)
    genericness_flags: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    exemplar_reference: ExemplarReference | None = None
