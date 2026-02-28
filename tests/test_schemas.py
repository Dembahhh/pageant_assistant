"""Tests for Pydantic schema models."""

import pytest
from pydantic import ValidationError

from pageant_assistant.schemas.rubric import (
    CriticFix,
    CriticOutput,
    DimensionScore,
    ExemplarReference,
)
from pageant_assistant.personas.models import Persona, PersonalStory


class TestDimensionScore:
    def test_valid_score(self):
        ds = DimensionScore(name="Clarity", score=8.5, reason="Clear and direct")
        assert ds.score == 8.5

    def test_score_out_of_range_high(self):
        with pytest.raises(ValidationError):
            DimensionScore(name="Clarity", score=11, reason="Too high")

    def test_score_out_of_range_low(self):
        with pytest.raises(ValidationError):
            DimensionScore(name="Clarity", score=-1, reason="Too low")


class TestCriticOutput:
    def test_valid_critic_output(self):
        output = CriticOutput(
            overall_score=7.5,
            dimension_scores=[
                DimensionScore(name="Clarity", score=8, reason="Good"),
                DimensionScore(name="Structure", score=7, reason="Decent"),
            ],
            time_fit_estimate_words=75,
            top_fixes=[
                CriticFix(type="strengthen_close", target="Closing Strength", instruction="End with impact")
            ],
        )
        assert output.overall_score == 7.5
        assert len(output.dimension_scores) == 2

    def test_overall_score_validation(self):
        with pytest.raises(ValidationError):
            CriticOutput(overall_score=15, dimension_scores=[])

    def test_defaults(self):
        output = CriticOutput(overall_score=5, dimension_scores=[])
        assert output.genericness_flags == []
        assert output.risk_flags == []
        assert output.exemplar_reference is None


class TestExemplarReference:
    def test_defaults(self):
        ref = ExemplarReference()
        assert ref.match_type == "none"
        assert ref.exemplar_id == ""
        assert ref.structural_takeaways == []


class TestPersonaModel:
    def test_auto_generates_id(self):
        p = Persona(name="Test", country="Kenya", platform="Education")
        assert len(p.id) == 12

    def test_name_required(self):
        with pytest.raises(ValidationError):
            Persona(country="Kenya", platform="Education")

    def test_personal_stories(self):
        p = Persona(
            name="Test",
            country="Kenya",
            platform="Education",
            personal_stories=[
                PersonalStory(
                    title="My Journey",
                    text="I traveled across the country to teach students about science.",
                    key_lesson="Education opens doors.",
                )
            ],
        )
        assert len(p.personal_stories) == 1
        assert p.personal_stories[0].title == "My Journey"

    def test_story_title_min_length(self):
        with pytest.raises(ValidationError):
            PersonalStory(title="", text="A valid story text here.", key_lesson="A valid lesson here.")
