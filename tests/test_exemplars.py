"""Tests for the exemplar library."""

from pageant_assistant.exemplars.library import (
    find_exemplar,
    format_exemplar_reference,
    load_exemplars,
)


class TestLoadExemplars:
    def test_returns_list(self):
        exemplars = load_exemplars()
        assert isinstance(exemplars, list)

    def test_has_7_exemplars(self):
        assert len(load_exemplars()) == 7

    def test_each_exemplar_has_required_fields(self):
        required = {"id", "pageant", "year", "question_type", "winner_name", "answer_text"}
        for ex in load_exemplars():
            missing = required - set(ex.keys())
            assert not missing, f"Exemplar {ex.get('id', '?')} missing: {missing}"

    def test_years_span_2018_to_2024(self):
        years = {ex["year"] for ex in load_exemplars()}
        assert min(years) == 2018
        assert max(years) == 2024


class TestFindExemplar:
    def test_find_by_question_type(self):
        ex = find_exemplar("personal")
        assert ex is not None
        assert ex["question_type"] == "personal"

    def test_find_advocacy(self):
        ex = find_exemplar("advocacy")
        assert ex is not None
        assert ex["question_type"] == "advocacy"

    def test_find_leadership(self):
        ex = find_exemplar("leadership")
        assert ex is not None
        assert ex["question_type"] == "leadership"

    def test_theme_tags_improve_match(self):
        ex_no_tags = find_exemplar("advocacy")
        ex_with_tags = find_exemplar("advocacy", theme_tags=["education", "empowerment"])
        # Both should return something; with tags may return a different (better) match
        assert ex_no_tags is not None
        assert ex_with_tags is not None

    def test_nonexistent_type_returns_fallback(self):
        ex = find_exemplar("nonexistent_type")
        # Should return most recent exemplar as fallback
        assert ex is not None


class TestFormatExemplarReference:
    def test_format_with_exemplar(self):
        ex = find_exemplar("personal")
        text = format_exemplar_reference(ex)
        assert "EXEMPLAR REFERENCE" in text
        assert ex["winner_name"] in text

    def test_format_with_none(self):
        text = format_exemplar_reference(None)
        assert text == ""

    def test_structural_notes_included(self):
        ex = find_exemplar("personal")
        text = format_exemplar_reference(ex)
        if ex.get("structural_notes"):
            assert "Structural notes" in text
