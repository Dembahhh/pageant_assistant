"""RAG-specific prompt strings for the evidence pipeline.

Kept separate from llm/prompts.py to isolate retrieval and verification
concerns from the main generation prompts.
"""

# ---------------------------------------------------------------------------
# Relevance grader — called per-chunk inside rag_research
# ---------------------------------------------------------------------------

RELEVANCE_GRADE_PROMPT = """\
You are a relevance assessor for a pageant coaching assistant.

QUESTION:
{question}

EVIDENCE CHUNK:
{chunk_text}

Does this chunk contain information that could support, frame, or ground an \
answer to the question above?

Respond with ONLY valid JSON — no markdown, no commentary, no extra keys:
{{"relevant": true}}
or
{{"relevant": false}}

Be generous: mark relevant if the chunk provides context, framing, statistics, \
named programmes, or examples related to the question topic. \
Mark irrelevant ONLY if the chunk is completely off-topic."""

# ---------------------------------------------------------------------------
# Claim verifier — called once per refined answer inside claim_verifier
# ---------------------------------------------------------------------------

CLAIM_VERIFY_PROMPT = """\
You are a pageant coaching fact-checker. Identify specific factual claims in \
the answer that are NOT supported by the retrieved evidence below.

ANSWER:
{answer}

RETRIEVED EVIDENCE:
{evidence_block}

Respond with ONLY valid JSON — no markdown, no commentary:
{{
  "claim_flags": ["<unsupported claim 1>", ...],
  "verdict": "grounded" | "partially_grounded" | "ungrounded"
}}

RULES:
- Flag ONLY specific factual claims: percentages, statistics, named \
  organisations, named policies, or concrete measured outcomes \
  (e.g. "45% of Kenyan women...", "the Anti-FGM Act 2011").
- Do NOT flag opinions, values, aspirations, or subjective statements.
- Do NOT flag claims clearly supported by one of the evidence chunks above.
- If the answer makes no specific factual claims, return \
  {{"claim_flags": [], "verdict": "grounded"}}.
- "grounded": all factual claims are supported by evidence.
- "partially_grounded": most claims are supported; 1–2 are not.
- "ungrounded": key factual claims are absent from the evidence."""
