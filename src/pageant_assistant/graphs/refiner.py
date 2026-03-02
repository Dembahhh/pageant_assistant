"""Q&A Refiner graph (M1 + M3 + M4).

Pipeline:
    question_understanding -> rag_research -> drafting -> critic -> rewrite
    -> [loop back to critic if score < 5] -> claim_verifier -> coach_report -> exemplar

M3 additions: rubric-driven scoring, structured JSON critic output, exemplar library.
M4 additions: CRAG evidence retrieval (rag_research), claim verification (claim_verifier).
"""

import json
import re

from langgraph.graph import END, START, StateGraph

from pageant_assistant.config.settings import (
    DEFAULT_RUBRIC,
    DEFAULT_TIME_LIMIT,
    WORDS_PER_SECOND,
)
from pageant_assistant.exemplars.library import (
    find_exemplar,
    format_exemplar_reference,
)
from pageant_assistant.llm.prompts import (
    COACH_REPORT_PROMPT,
    CRITIC_PROMPT,
    DRAFTING_PROMPT,
    EXEMPLAR_PROMPT,
    QUESTION_ANALYSIS_PROMPT,
    REWRITE_PROMPT,
    STYLE_INSTRUCTIONS,
)
from pageant_assistant.llm.providers import get_llm
from pageant_assistant.rag.nodes import claim_verifier, rag_research
from pageant_assistant.rubrics.loader import format_rubric_for_prompt, load_rubric
from pageant_assistant.schemas.rubric import CriticOutput
from pageant_assistant.schemas.state import RefinerState

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _word_budget(time_limit: int, style_key: str = "structured_narrative") -> int:
    """Convert a time limit in seconds to an approximate word count.

    Uses per-style words-per-second rates from settings. Falls back to 2.5
    if the style key is missing from the dict.
    """
    wps = WORDS_PER_SECOND.get(style_key, 2.5)
    return int(time_limit * wps)


def _parse_critic_json(text: str) -> CriticOutput | None:
    """Try to parse the critic's response as structured JSON.

    Handles cases where the LLM wraps JSON in markdown code fences.
    Returns None if parsing fails.
    """
    # Strip markdown code fences if present
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        data = json.loads(cleaned)
        return CriticOutput(**data)
    except (json.JSONDecodeError, Exception):
        return None


def _format_structured_scores(critic_scores: dict | None) -> str:
    """Format parsed critic scores for the coach report prompt."""
    if not critic_scores:
        return ""
    lines = ["STRUCTURED SCORES:"]
    for dim in critic_scores.get("dimension_scores", []):
        lines.append(f"- {dim['name']}: {dim['score']}/10 — {dim['reason']}")
    lines.append(f"- Overall: {critic_scores.get('overall_score', 'N/A')}/10")
    if critic_scores.get("genericness_flags"):
        lines.append(f"- Genericness flags: {', '.join(critic_scores['genericness_flags'])}")
    return "\n".join(lines)


def _format_critique_for_rewrite(state: RefinerState) -> str:
    """Format critic output as human-readable feedback for the rewrite LLM.

    Falls back to the raw critique text when structured scores are unavailable.
    """
    critic_scores = state.get("critic_scores")
    if not critic_scores:
        return state.get("critique", "")

    lines = [f"Overall score: {critic_scores.get('overall_score', 'N/A')}/10"]

    for i, fix in enumerate(critic_scores.get("top_fixes", []), 1):
        lines.append(f"{i}. [{fix.get('target', '')}] {fix.get('instruction', '')}")

    flags = critic_scores.get("genericness_flags", [])
    if flags:
        lines.append(f"Genericness flags: {', '.join(flags)}")

    risk = critic_scores.get("risk_flags", [])
    if risk:
        lines.append(f"Risk flags: {', '.join(risk)}")

    return "\n".join(lines)


def _clean_prompt(text: str) -> str:
    """Collapse runs of 3+ newlines (from empty template variables) into one blank line."""
    return re.sub(r"\n{3,}", "\n\n", text)


# ---------------------------------------------------------------------------
# Graph nodes
# ---------------------------------------------------------------------------


def question_understanding(state: RefinerState) -> dict:
    """Classify the question and identify what judges are testing."""
    llm = get_llm("question_analysis")
    prompt = QUESTION_ANALYSIS_PROMPT.format(question=state["question"])
    response = llm.invoke(prompt)
    return {"question_analysis": response.content}


def drafting(state: RefinerState) -> dict:
    """Generate a strong first draft answer."""
    llm = get_llm("drafting")
    time_limit = state.get("time_limit", DEFAULT_TIME_LIMIT)
    style_key = state.get("style_preset", "structured_narrative")
    prompt = DRAFTING_PROMPT.format(
        question=state["question"],
        raw_answer=state["raw_answer"],
        question_analysis=state["question_analysis"],
        time_limit=time_limit,
        word_budget=_word_budget(time_limit, style_key),
        style_description=STYLE_INSTRUCTIONS.get(style_key, ""),
        style_instructions=STYLE_INSTRUCTIONS.get(style_key, ""),
        persona_context=state.get("persona_context", ""),
        evidence_block=state.get("rag_evidence") or "",
    )
    prompt = _clean_prompt(prompt)
    response = llm.invoke(prompt)
    return {"draft_answer": response.content}


def critic(state: RefinerState) -> dict:
    """Score the draft against the rubric and flag issues."""
    llm = get_llm("critic")
    time_limit = state.get("time_limit", DEFAULT_TIME_LIMIT)

    # Load rubric
    rubric_name = state.get("rubric_name", DEFAULT_RUBRIC)
    rubric = load_rubric(rubric_name)
    rubric_text = format_rubric_for_prompt(rubric)

    # Find matching exemplar for structural reference
    question_analysis = state.get("question_analysis", "")
    # Infer question type from analysis (best effort)
    q_type = _infer_question_type(question_analysis)
    exemplar = find_exemplar(question_type=q_type)
    exemplar_notes = format_exemplar_reference(exemplar) if exemplar else ""

    # On second pass, score the rewrite instead of the original draft
    answer_to_score = state.get("refined_answer") or state["draft_answer"]

    style_key = state.get("style_preset", "structured_narrative")
    prompt = CRITIC_PROMPT.format(
        question=state["question"],
        draft_answer=answer_to_score,
        time_limit=time_limit,
        word_budget=_word_budget(time_limit, style_key),
        persona_context=state.get("persona_context", ""),
        rubric_dimensions=rubric_text,
        exemplar_structural_notes=exemplar_notes,
    )
    prompt = _clean_prompt(prompt)
    response = llm.invoke(prompt)

    # Try to parse structured JSON
    parsed = _parse_critic_json(response.content)

    result = {
        "critique": response.content,
        "iteration_count": state.get("iteration_count", 0) + 1,
        "rubric_name": rubric_name,
    }

    if parsed:
        result["critic_scores"] = parsed.model_dump()
    if exemplar:
        result["exemplar_ref"] = {
            "id": exemplar.get("id", ""),
            "winner_name": exemplar.get("winner_name", ""),
            "year": exemplar.get("year", 0),
            "structural_notes": exemplar.get("structural_notes", ""),
        }

    return result


def rewrite(state: RefinerState) -> dict:
    """Apply critic edits and style to produce the refined answer."""
    llm = get_llm("rewrite")
    time_limit = state.get("time_limit", DEFAULT_TIME_LIMIT)
    style_key = state.get("style_preset", "structured_narrative")
    prompt = REWRITE_PROMPT.format(
        question=state["question"],
        draft_answer=state.get("refined_answer") or state["draft_answer"],
        critique=_format_critique_for_rewrite(state),
        time_limit=time_limit,
        word_budget=_word_budget(time_limit, style_key),
        style_instructions=STYLE_INSTRUCTIONS.get(style_key, ""),
        persona_context=state.get("persona_context", ""),
        evidence_block=state.get("rag_evidence") or "",
    )
    prompt = _clean_prompt(prompt)
    response = llm.invoke(prompt)
    return {"refined_answer": response.content}


def coach_report(state: RefinerState) -> dict:
    """Generate the coach report with scores and practice notes."""
    llm = get_llm("drafting")  # Moderate creativity for report writing

    structured = _format_structured_scores(state.get("critic_scores"))

    prompt = COACH_REPORT_PROMPT.format(
        question=state["question"],
        raw_answer=state["raw_answer"],
        refined_answer=state["refined_answer"],
        critique=state["critique"],
        structured_scores=structured,
    )
    response = llm.invoke(prompt)
    return {"coach_report": response.content}


def generate_exemplar(state: RefinerState) -> dict:
    """Generate a model winning answer, guided by real exemplar structure."""
    llm = get_llm("exemplar")
    time_limit = state.get("time_limit", DEFAULT_TIME_LIMIT)
    style_key = state.get("style_preset", "structured_narrative")

    # Use exemplar reference from critic step if available
    exemplar_ref = state.get("exemplar_ref")
    exemplar_text = ""
    if exemplar_ref and exemplar_ref.get("structural_notes"):
        exemplar_text = (
            f"STRUCTURAL REFERENCE (from {exemplar_ref.get('winner_name', 'a past winner')}, "
            f"{exemplar_ref.get('year', '')}):\n"
            f"{exemplar_ref['structural_notes']}\n"
            f"Use this structure as guidance — do NOT copy any wording."
        )

    prompt = EXEMPLAR_PROMPT.format(
        question=state["question"],
        question_analysis=state["question_analysis"],
        time_limit=time_limit,
        word_budget=_word_budget(time_limit, style_key),
        style_instructions=STYLE_INSTRUCTIONS.get(style_key, ""),
        exemplar_reference=exemplar_text,
    )
    response = llm.invoke(prompt)
    return {"exemplar_answer": response.content}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _infer_question_type(question_analysis: str) -> str:
    """Best-effort extraction of question type from the analysis text."""
    analysis_lower = question_analysis.lower()
    for q_type in ("personal", "issues_based", "advocacy", "leadership", "fun_creative"):
        if q_type.replace("_", " ") in analysis_lower or q_type in analysis_lower:
            return q_type
    if "issue" in analysis_lower:
        return "issues_based"
    return "personal"  # Default fallback


# ---------------------------------------------------------------------------
# Conditional edge: should we loop back to critic for another pass?
# ---------------------------------------------------------------------------


def should_reloop(state: RefinerState) -> str:
    """Decide whether to do another critic->rewrite pass or proceed to verification.

    Returns:
        ``"critic"`` to loop again, or ``"claim_verifier"`` to continue to the
        claim verification and coach report nodes.
    """
    # Hard cap: max 2 iterations regardless of score
    if state.get("iteration_count", 0) >= 2:
        return "claim_verifier"

    # Prefer structured score when available (M3 JSON critic output)
    critic_scores = state.get("critic_scores")
    if critic_scores and "overall_score" in critic_scores:
        if critic_scores["overall_score"] < 5.0:
            return "critic"
        return "claim_verifier"

    # Fallback: regex parse from free-text critique
    critique_text = state.get("critique", "")
    match = re.search(r'"overall_score"\s*:\s*(\d+(?:\.\d+)?)', critique_text)
    if not match:
        match = re.search(
            r"\*\*Overall score\*\*[:\s]*(\d+(?:\.\d+)?)",
            critique_text,
            re.IGNORECASE,
        )
    if match:
        score = float(match.group(1))
        if score < 5.0:
            return "critic"

    return "claim_verifier"


# ---------------------------------------------------------------------------
# Build the graph
# ---------------------------------------------------------------------------


def build_refiner_graph() -> StateGraph:
    """Construct and compile the M4 Q&A Refiner graph.

    Pipeline (M4):
        START
        → question_understanding
        → rag_research          (retrieve + grade Kenya/Africa evidence)
        → drafting              (evidence_block injected when relevant)
        → critic
        → rewrite               (evidence_block injected when relevant)
        → [loop back to critic if score < 5, max 2 iterations]
        → claim_verifier        (flag unsupported factual claims)
        → coach_report
        → generate_exemplar
        → END

    Returns:
        Compiled LangGraph StateGraph.
    """
    graph = StateGraph(RefinerState)

    # Register all nodes
    graph.add_node("question_understanding", question_understanding)
    graph.add_node("rag_research", rag_research)
    graph.add_node("drafting", drafting)
    graph.add_node("critic", critic)
    graph.add_node("rewrite", rewrite)
    graph.add_node("claim_verifier", claim_verifier)
    graph.add_node("coach_report", coach_report)
    graph.add_node("generate_exemplar", generate_exemplar)

    # Linear flow: START → understand → research → draft → critic → rewrite
    graph.add_edge(START, "question_understanding")
    graph.add_edge("question_understanding", "rag_research")
    graph.add_edge("rag_research", "drafting")
    graph.add_edge("drafting", "critic")
    graph.add_edge("critic", "rewrite")

    # Conditional: loop back to critic OR proceed to claim verification
    graph.add_conditional_edges("rewrite", should_reloop)

    # Final pipeline: verify → report → exemplar → END
    graph.add_edge("claim_verifier", "coach_report")
    graph.add_edge("coach_report", "generate_exemplar")
    graph.add_edge("generate_exemplar", END)

    return graph.compile()
