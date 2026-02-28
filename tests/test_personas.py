"""Tests for persona CRUD operations and context formatting."""

import json

import pytest

from pageant_assistant.personas.models import Persona, PersonalStory
from pageant_assistant.personas.manager import (
    delete_persona,
    format_persona_context,
    list_personas,
    load_persona,
    save_persona,
)


@pytest.fixture
def sample_persona():
    """Create a test persona instance."""
    return Persona(
        id="test00000001",
        name="Test Contestant",
        country="Kenya",
        platform="Youth mental health awareness",
        values=["resilience", "empathy", "education"],
        personal_stories=[
            PersonalStory(
                title="Teaching in Rural Zambia",
                text="I spent six months teaching math in a rural school with no electricity. "
                     "The students' determination changed my perspective on education access.",
                key_lesson="Education is a privilege I will never take for granted.",
            )
        ],
    )


@pytest.fixture
def personas_dir(tmp_path, monkeypatch):
    """Redirect PERSONAS_DIR to a temporary directory for test isolation."""
    monkeypatch.setattr("pageant_assistant.personas.manager.PERSONAS_DIR", tmp_path)
    return tmp_path


class TestSaveAndLoad:
    def test_save_creates_file(self, sample_persona, personas_dir):
        save_persona(sample_persona)
        path = personas_dir / f"{sample_persona.id}.json"
        assert path.exists()

    def test_saved_file_is_valid_json(self, sample_persona, personas_dir):
        save_persona(sample_persona)
        path = personas_dir / f"{sample_persona.id}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["name"] == "Test Contestant"

    def test_load_returns_persona(self, sample_persona, personas_dir):
        save_persona(sample_persona)
        loaded = load_persona(sample_persona.id)
        assert loaded is not None
        assert loaded.name == sample_persona.name
        assert loaded.country == sample_persona.country

    def test_load_nonexistent_returns_none(self, personas_dir):
        assert load_persona("nonexistent999") is None

    def test_load_corrupted_json_returns_none(self, personas_dir):
        bad_file = personas_dir / "corrupted001.json"
        bad_file.write_text("{invalid json", encoding="utf-8")
        assert load_persona("corrupted001") is None


class TestListPersonas:
    def test_empty_dir_returns_empty(self, personas_dir):
        assert list_personas() == []

    def test_lists_saved_personas(self, sample_persona, personas_dir):
        save_persona(sample_persona)
        result = list_personas()
        assert len(result) == 1
        assert result[0]["id"] == sample_persona.id
        assert result[0]["name"] == sample_persona.name

    def test_sorted_alphabetically(self, personas_dir):
        save_persona(Persona(id="aaa000000001", name="Zara", country="UK", platform="Arts"))
        save_persona(Persona(id="bbb000000002", name="Alice", country="US", platform="STEM"))
        result = list_personas()
        assert result[0]["name"] == "Alice"
        assert result[1]["name"] == "Zara"

    def test_skips_corrupted_files(self, sample_persona, personas_dir):
        save_persona(sample_persona)
        bad_file = personas_dir / "bad.json"
        bad_file.write_text("not json", encoding="utf-8")
        result = list_personas()
        assert len(result) == 1


class TestDeletePersona:
    def test_delete_existing(self, sample_persona, personas_dir):
        save_persona(sample_persona)
        assert delete_persona(sample_persona.id) is True
        assert not (personas_dir / f"{sample_persona.id}.json").exists()

    def test_delete_nonexistent_returns_false(self, personas_dir):
        assert delete_persona("doesnotexist") is False


class TestFormatPersonaContext:
    def test_format_includes_name_and_country(self, sample_persona):
        text = format_persona_context(sample_persona)
        assert "Test Contestant" in text
        assert "Kenya" in text

    def test_format_includes_platform(self, sample_persona):
        text = format_persona_context(sample_persona)
        assert "Youth mental health" in text

    def test_format_includes_values(self, sample_persona):
        text = format_persona_context(sample_persona)
        assert "resilience" in text

    def test_format_includes_stories(self, sample_persona):
        text = format_persona_context(sample_persona)
        assert "Teaching in Rural Zambia" in text
        assert "Key lesson" in text.lower() or "key_lesson" in text.lower()

    def test_format_none_returns_empty(self):
        assert format_persona_context(None) == ""
