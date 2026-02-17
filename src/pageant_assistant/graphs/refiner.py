"""Milestone 1: Q&A Refiner graph.

Pipeline: question_understanding -> drafting -> critic -> rewrite -> coach_report
With an optional critic->rewrite loop if the score is very low.
"""

import re
from langgraph.graph import StateGraph, START, END

from pageant_assistant.schemas.state import RefinerState
from pageant_assistant.llm.providers import get_llm
from pageant_assistant.llm.prompts import (
    QUESTION_ANALYSIS_PROMPT,
    DRAFTING_PROMPT,
    CRITIC_PROMPT,
    REWRITE_PROMPT,
    COACH_REPORT_PROMPT,
    EXEMPLAR_PROMPT,
    STYLE_INSTRUCTIONS,
)
from pageant_assistant.config.settings import WORDS_PER_SECOND, DEFAULT_TIME_LIMIT


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _word_budget(time_limit: int) -> int:
    """Convert a time limit in seconds to an approximate word count."""
    return int(time_limit * WORDS_PER_SECOND)


# ---------------------------------------------------------------------------
# Graph nodes — each takes the full state and returns a partial update dict
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
        word_budget=_word_budget(time_limit),
        style_description=STYLE_INSTRUCTIONS.get(style_key, ""),
        style_instructions=STYLE_INSTRUCTIONS.get(style_key, ""),
    )
    response = llm.invoke(prompt)
    return {"draft_answer": response.content}


def critic(state: RefinerState) -> dict:
    """Score the draft against the rubric and flag issues."""
    llm = get_llm("critic")
    time_limit = state.get("time_limit", DEFAULT_TIME_LIMIT)
    # On second pass, score the rewrite instead of the original draft
    answer_to_score = state.get("refined_answer") or state["draft_answer"]
    prompt = CRITIC_PROMPT.format(
        question=state["question"],
        draft_answer=answer_to_score,
        time_limit=time_limit,
        word_budget=_word_budget(time_limit),
    )
    response = llm.invoke(prompt)
    return {
        "critique": response.content,
        "iteration_count": state.get("iteration_count", 0) + 1,
    }


def rewrite(state: RefinerState) -> dict:
    """Apply critic edits and style to produce the refined answer."""
    llm = get_llm("rewrite")
    time_limit = state.get("time_limit", DEFAULT_TIME_LIMIT)
    style_key = state.get("style_preset", "structured_narrative")
    prompt = REWRITE_PROMPT.format(
        question=state["question"],
        draft_answer=state.get("refined_answer") or state["draft_answer"],
        critique=state["critique"],
        time_limit=time_limit,
        word_budget=_word_budget(time_limit),
        style_instructions=STYLE_INSTRUCTIONS.get(style_key, ""),
    )
    response = llm.invoke(prompt)
    return {"refined_answer": response.content}


def coach_report(state: RefinerState) -> dict:
    """Generate the coach report with scores and practice notes."""
    llm = get_llm("drafting")  # Moderate creativity for report writing
    prompt = COACH_REPORT_PROMPT.format(
        question=state["question"],
        raw_answer=state["raw_answer"],
        refined_answer=state["refined_answer"],
        critique=state["critique"],
    )
    response = llm.invoke(prompt)
    return {"coach_report": response.content}


def generate_exemplar(state: RefinerState) -> dict:
    """Generate a model winning answer as a reference exemplar."""
    llm = get_llm("exemplar")
    time_limit = state.get("time_limit", DEFAULT_TIME_LIMIT)
    style_key = state.get("style_preset", "structured_narrative")
    prompt = EXEMPLAR_PROMPT.format(
        question=state["question"],
        question_analysis=state["question_analysis"],
        time_limit=time_limit,
        word_budget=_word_budget(time_limit),
        style_instructions=STYLE_INSTRUCTIONS.get(style_key, ""),
    )
    response = llm.invoke(prompt)
    return {"exemplar_answer": response.content}


# ---------------------------------------------------------------------------
# Conditional edge: should we loop back to critic for another pass?
# ---------------------------------------------------------------------------

def should_reloop(state: RefinerState) -> str:
    """Decide whether to do another critic->rewrite pass or finalize."""
    # Max 2 iterations
    if state.get("iteration_count", 0) >= 2:
        return "coach_report"

    # Check if overall score is below 5 (parse from critique text)
    critique_text = state.get("critique", "")
    match = re.search(r"\*\*Overall score\*\*[:\s]*(\d+(?:\.\d+)?)", critique_text, re.IGNORECASE)
    if match:
        score = float(match.group(1))
        if score < 5.0:
            return "critic"

    return "coach_report"


# ---------------------------------------------------------------------------
# Build the graph
# ---------------------------------------------------------------------------

def build_refiner_graph() -> StateGraph:
    """Construct and compile the M1 Q&A Refiner graph."""
    graph = StateGraph(RefinerState)

    # Add nodes
    graph.add_node("question_understanding", question_understanding)
    graph.add_node("drafting", drafting)
    graph.add_node("critic", critic)
    graph.add_node("rewrite", rewrite)
    graph.add_node("coach_report", coach_report)
    graph.add_node("generate_exemplar", generate_exemplar)

    # Linear flow: START -> understand -> draft -> critic -> rewrite
    graph.add_edge(START, "question_understanding")
    graph.add_edge("question_understanding", "drafting")
    graph.add_edge("drafting", "critic")
    graph.add_edge("critic", "rewrite")

    # After rewrite: conditional — loop back to critic or move to report
    graph.add_conditional_edges("rewrite", should_reloop)

    # Final nodes: coach report -> exemplar -> END
    graph.add_edge("coach_report", "generate_exemplar")
    graph.add_edge("generate_exemplar", END)

    return graph.compile()
