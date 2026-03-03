"""Tests for rubric loading and formatting."""

import pytest

from pageant_assistant.rubrics.loader import format_rubric_for_prompt, load_rubric


class TestLoadRubric:
    def test_load_miss_universe(self):
        rubric = load_rubric("miss_universe")
        assert "dimensions" in rubric
        assert len(rubric["dimensions"]) == 8

    def test_each_dimension_has_required_fields(self):
        rubric = load_rubric("miss_universe")
        for dim in rubric["dimensions"]:
            assert "name" in dim
            assert "weight" in dim
            assert "description" in dim
            assert isinstance(dim["weight"], (int, float))

    def test_fallback_on_missing_rubric(self):
        rubric = load_rubric("miss_nonexistent_pageant")
        assert "dimensions" in rubric
        assert rubric["version"] == "fallback"
        assert len(rubric["dimensions"]) == 8

    def test_cap_rules_present_for_miss_universe(self):
        rubric = load_rubric("miss_universe")
        assert "cap_rules" in rubric


class TestFormatRubricForPrompt:
    def test_output_contains_scoring_header(self):
        rubric = load_rubric("miss_universe")
        text = format_rubric_for_prompt(rubric)
        assert "SCORING DIMENSIONS" in text

    def test_output_contains_all_dimensions(self):
        rubric = load_rubric("miss_universe")
        text = format_rubric_for_prompt(rubric)
        for dim in rubric["dimensions"]:
            assert dim["name"] in text

    def test_weighted_dimensions_show_weight(self):
        rubric = load_rubric("miss_universe")
        text = format_rubric_for_prompt(rubric)
        # Authenticity has weight 1.2 — should show weight note
        assert "1.2x" in text

    def test_fallback_rubric_formats_correctly(self):
        rubric = load_rubric("miss_nonexistent")
        text = format_rubric_for_prompt(rubric)
        assert "SCORING DIMENSIONS" in text
        assert len(text) > 100


class TestNewRubrics:
    @pytest.mark.parametrize("rubric_name", ["miss_grand", "miss_earth", "miss_charm"])
    def test_load_new_rubric(self, rubric_name):
        rubric = load_rubric(rubric_name)
        assert "dimensions" in rubric
        assert len(rubric["dimensions"]) == 8
        assert rubric["version"] != "fallback"

    @pytest.mark.parametrize("rubric_name", ["miss_grand", "miss_earth", "miss_charm"])
    def test_new_rubric_dimensions_have_required_fields(self, rubric_name):
        rubric = load_rubric(rubric_name)
        for dim in rubric["dimensions"]:
            assert "name" in dim
            assert "weight" in dim
            assert "description" in dim
            assert isinstance(dim["weight"], (int, float))

    @pytest.mark.parametrize("rubric_name", ["miss_grand", "miss_earth", "miss_charm"])
    def test_new_rubric_has_cap_rules(self, rubric_name):
        rubric = load_rubric(rubric_name)
        assert "cap_rules" in rubric
        assert len(rubric["cap_rules"]) > 0

    @pytest.mark.parametrize("rubric_name", ["miss_grand", "miss_earth", "miss_charm"])
    def test_new_rubric_has_genericness_signals(self, rubric_name):
        rubric = load_rubric(rubric_name)
        assert "genericness_signals" in rubric
        assert len(rubric["genericness_signals"]) > 0

    @pytest.mark.parametrize("rubric_name", ["miss_grand", "miss_earth", "miss_charm"])
    def test_new_rubric_formats_for_prompt(self, rubric_name):
        rubric = load_rubric(rubric_name)
        text = format_rubric_for_prompt(rubric)
        assert "SCORING DIMENSIONS" in text
        for dim in rubric["dimensions"]:
            assert dim["name"] in text
