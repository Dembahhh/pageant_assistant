"""Graph nodes for M4 RAG: rag_research and claim_verifier.

rag_research  — retrieves and grades evidence before drafting.
claim_verifier — checks factual claims in the refined answer against evidence.

Both nodes degrade gracefully: any exception results in empty/None state
fields so the coaching pipeline always completes.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from pageant_assistant.llm.providers import get_llm
from pageant_assistant.rag.prompts import CLAIM_VERIFY_PROMPT, RELEVANCE_GRADE_PROMPT
from pageant_assistant.rag.store import retrieve_evidence
from pageant_assistant.schemas.state import RefinerState

logger = logging.getLogger(__name__)

# Question types for which evidence retrieval adds value.
# Personal and fun/creative questions do not benefit from factual evidence.
_RAG_ELIGIBLE: frozenset[str] = frozenset({"issues_based", "advocacy", "leadership"})


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _parse_question_type(question_analysis: str) -> str:
    """Extract the question type label from the analysis text (best-effort).

    Args:
        question_analysis: Free-text output from the question_understanding node.

    Returns:
        One of "personal", "issues_based", "advocacy", "leadership",
        "fun_creative".  Falls back to "personal" when no label is found.

    Example:
        >>> _parse_question_type("Question type: issues-based...")
        'issues_based'
    """
    text = question_analysis.lower()
    for label in ("personal", "issues_based", "advocacy", "leadership", "fun_creative"):
        if label.replace("_", " ") in text or label in text:
            return label
    if "issue" in text:
        return "issues_based"
    return "personal"  # Conservative default


def _grade_chunk(llm: Any, question: str, chunk: dict[str, Any]) -> bool:
    """Ask the LLM whether a single evidence chunk is relevant to the question.

    Args:
        llm: An initialised LLM instance (low temperature for consistency).
        question: The pageant question being answered.
        chunk: A chunk dict with at least a ``text`` key.

    Returns:
        True if the chunk is relevant, False otherwise.  Returns True on any
        parse failure to avoid silently discarding potentially useful evidence.

    Example:
        >>> llm = get_llm("critic")
        >>> _grade_chunk(llm, "What is leadership?", {"text": "Leaders inspire...", "chunk_type": "framing"})
        True
    """
    try:
        prompt = RELEVANCE_GRADE_PROMPT.format(
            question=question,
            chunk_text=chunk["text"],
        )
        response = llm.invoke(prompt)
        content = response.content.strip()
        # Strip markdown code fences the LLM sometimes adds
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content.strip())
        data: dict[str, Any] = json.loads(content)
        relevant = bool(data.get("relevant", False))
        logger.debug(
            "_grade_chunk: topic=%s type=%s → relevant=%s",
            chunk.get("topic"),
            chunk.get("chunk_type"),
            relevant,
        )
        return relevant
    except (json.JSONDecodeError, KeyError) as exc:
        logger.warning("_grade_chunk: parse error (%s) — defaulting to include chunk", exc)
        return True  # Generous default: never silently discard on failure


def _format_evidence_block(chunks: list[dict[str, Any]]) -> str:
    """Render selected evidence chunks as a numbered, labelled prompt block.

    Args:
        chunks: Graded and selected evidence dicts (max 3).

    Returns:
        A formatted multi-line string ready for prompt injection, or an empty
        string if ``chunks`` is empty.

    Example:
        >>> block = _format_evidence_block([{"text": "Hello", "chunk_type": "framing", "source": "WHO"}])
        >>> block.startswith("EVIDENCE")
        True
    """
    if not chunks:
        return ""
    lines = [
        "EVIDENCE — use only if directly relevant. "
        "Do NOT fabricate additional facts beyond what is shown:\n"
    ]
    for i, chunk in enumerate(chunks, 1):
        source = chunk.get("source", "")
        lines.append(f"[{i}] ({chunk.get('chunk_type', 'general')}) {chunk['text']}")
        if source:
            lines.append(f"    Source: {source}")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Node: rag_research
# ---------------------------------------------------------------------------


def rag_research(state: RefinerState) -> dict[str, Any]:
    """Retrieve and grade evidence chunks relevant to the current question.

    Fires only for ``issues_based``, ``advocacy``, and ``leadership`` question
    types.  Returns ``rag_evidence=None`` for ``personal`` and ``fun_creative``
    questions where factual evidence is unnecessary.

    Selection cap: at most 1 framing chunk + 1 stat chunk + 1 example chunk
    are injected downstream, ensuring concise, signal-dense evidence blocks.

    Args:
        state: Current graph state.  Reads ``question`` and
               ``question_analysis``.

    Returns:
        Dict with keys:
            - ``rag_evidence`` (str | None): Formatted evidence block for
              prompt injection, or None if retrieval was skipped/failed.
            - ``rag_question_type`` (str): Inferred question type label.
    """
    question: str = state["question"]
    question_analysis: str = state.get("question_analysis", "")
    q_type = _parse_question_type(question_analysis)

    logger.info("rag_research: question_type=%s", q_type)

    if q_type not in _RAG_ELIGIBLE:
        logger.info(
            "rag_research: skipping retrieval — question_type '%s' does not use evidence",
            q_type,
        )
        return {"rag_evidence": None, "rag_question_type": q_type}

    raw_chunks = retrieve_evidence(question, n_results=6)
    if not raw_chunks:
        logger.info("rag_research: no chunks retrieved from store")
        return {"rag_evidence": None, "rag_question_type": q_type}

    # Grade each chunk for relevance using a low-temperature LLM call
    llm = get_llm("critic")
    graded: list[dict[str, Any]] = [
        chunk for chunk in raw_chunks if _grade_chunk(llm, question, chunk)
    ]
    logger.info(
        "rag_research: %d/%d chunk(s) passed relevance grading",
        len(graded),
        len(raw_chunks),
    )

    if not graded:
        return {"rag_evidence": None, "rag_question_type": q_type}

    # Select at most 1 chunk per type to keep the evidence block focused
    selected: list[dict[str, Any]] = []
    seen_types: set[str] = set()
    for chunk in graded:
        ctype = chunk.get("chunk_type", "general")
        if ctype not in seen_types:
            selected.append(chunk)
            seen_types.add(ctype)
        if len(selected) >= 3:
            break

    evidence_block = _format_evidence_block(selected)
    logger.info(
        "rag_research: %d chunk(s) selected — types: [%s]",
        len(selected),
        ", ".join(c.get("chunk_type", "?") for c in selected),
    )
    return {"rag_evidence": evidence_block, "rag_question_type": q_type}


# ---------------------------------------------------------------------------
# Node: claim_verifier
# ---------------------------------------------------------------------------


def claim_verifier(state: RefinerState) -> dict[str, Any]:
    """Verify factual claims in the refined answer against retrieved evidence.

    Only activates when evidence was retrieved (``rag_evidence`` is not None).
    Skips gracefully when the question type did not use retrieval or when
    parsing fails.

    Args:
        state: Current graph state.  Reads ``refined_answer`` and
               ``rag_evidence``.

    Returns:
        Dict with key:
            - ``claim_flags`` (list[str]): Factual claims found in the refined
              answer that are not supported by the retrieved evidence.  Empty
              list when verification passes or is skipped.
    """
    evidence: str | None = state.get("rag_evidence")
    refined: str = state.get("refined_answer", "")

    if not evidence or not refined:
        logger.info(
            "claim_verifier: skipping — evidence=%s refined_answer_len=%d",
            "present" if evidence else "absent",
            len(refined),
        )
        return {"claim_flags": []}

    llm = get_llm("critic")
    try:
        prompt = CLAIM_VERIFY_PROMPT.format(
            answer=refined,
            evidence_block=evidence,
        )
        response = llm.invoke(prompt)
        content = response.content.strip()
        # Strip markdown code fences
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content.strip())
        data: dict[str, Any] = json.loads(content)
        flags: list[str] = data.get("claim_flags", [])
        verdict: str = data.get("verdict", "grounded")
        logger.info("claim_verifier: verdict=%s — %d flag(s)", verdict, len(flags))
        return {"claim_flags": flags}
    except (json.JSONDecodeError, KeyError) as exc:
        logger.warning("claim_verifier: parse error (%s) — returning empty flags", exc)
        return {"claim_flags": []}
