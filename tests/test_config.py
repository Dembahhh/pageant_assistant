"""Tests for configuration and settings module."""

from pathlib import Path


def test_project_root_found():
    from pageant_assistant.config.settings import PROJECT_ROOT

    assert PROJECT_ROOT.exists()
    assert (PROJECT_ROOT / "pyproject.toml").exists()


def test_data_directories_exist():
    from pageant_assistant.config.settings import (
        CHROMA_DIR,
        DATA_DIR,
        EXEMPLARS_DIR,
        PERSONAS_DIR,
        QUESTIONS_DIR,
    )

    for d in (DATA_DIR, CHROMA_DIR, QUESTIONS_DIR, PERSONAS_DIR, EXEMPLARS_DIR):
        assert d.exists(), f"Missing data directory: {d}"
        assert d.is_dir()


def test_rubrics_dir_exists():
    from pageant_assistant.config.settings import RUBRICS_DIR

    assert RUBRICS_DIR.exists()
    assert RUBRICS_DIR.is_dir()


def test_style_presets_non_empty():
    from pageant_assistant.config.settings import DEFAULT_STYLE, STYLE_PRESETS

    assert len(STYLE_PRESETS) >= 2
    assert DEFAULT_STYLE in STYLE_PRESETS


def test_temperature_roles():
    from pageant_assistant.config.settings import TEMPERATURE

    expected_roles = {"supervisor", "question_analysis", "drafting", "critic", "rewrite", "exemplar"}
    assert expected_roles.issubset(TEMPERATURE.keys())
    for role, temp in TEMPERATURE.items():
        assert 0.0 <= temp <= 1.0, f"Temperature out of range for {role}: {temp}"


def test_valid_time_limits():
    from pageant_assistant.config.settings import DEFAULT_TIME_LIMIT, VALID_TIME_LIMITS

    assert DEFAULT_TIME_LIMIT in VALID_TIME_LIMITS
    assert all(isinstance(t, int) and t > 0 for t in VALID_TIME_LIMITS)


def test_groq_model_is_set():
    from pageant_assistant.config.settings import GROQ_MODEL

    assert GROQ_MODEL
    assert isinstance(GROQ_MODEL, str)
