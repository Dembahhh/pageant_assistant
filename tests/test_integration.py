"""Integration tests that require a real GROQ_API_KEY.

These are skipped in CI when the secret is unavailable and marked with
@pytest.mark.integration so they can be excluded with: pytest -m "not integration"
"""

import pytest


@pytest.mark.integration
def test_groq_llm_responds(groq_key):
    """Verify the Groq LLM returns a response."""
    from pageant_assistant.llm.providers import get_llm

    llm = get_llm("question_analysis")
    response = llm.invoke("What is 2 + 2? Reply with just the number.")
    assert response.content.strip()
    assert "4" in response.content


@pytest.mark.integration
def test_full_pipeline_shape(groq_key):
    """Verify the refiner graph produces all expected output fields."""
    from pageant_assistant.graphs.refiner import build_refiner_graph

    graph = build_refiner_graph()
    result = graph.invoke({
        "question": "What is the most important quality a leader should have?",
        "raw_answer": "I think a leader should be kind and listen to people.",
        "time_limit": 20,
        "style_preset": "structured_narrative",
        "question_id": "test-integration-001",
        "input_mode": "text",
        "persona_id": "",
        "persona_context": "",
        "iteration_count": 0,
    })

    assert "refined_answer" in result
    assert "coach_report" in result
    assert "exemplar_answer" in result
    assert len(result["refined_answer"]) > 20
