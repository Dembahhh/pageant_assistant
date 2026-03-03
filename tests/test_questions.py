"""Tests for the question bank module."""

import pytest

from pageant_assistant.questions.bank import (
    get_filter_options,
    get_random_question,
    load_questions,
)


class TestLoadQuestions:
    def test_returns_tuple(self):
        questions = load_questions()
        assert isinstance(questions, tuple)

    def test_has_at_least_45_questions(self):
        assert len(load_questions()) >= 45

    def test_each_question_has_required_fields(self):
        required = {"id", "text", "pageant_type", "question_type", "difficulty"}
        for q in load_questions():
            missing = required - set(q.keys())
            assert not missing, f"Question {q.get('id', '?')} missing fields: {missing}"

    def test_question_types_cover_all_categories(self):
        types = {q["question_type"] for q in load_questions()}
        expected = {"personal", "issues_based", "advocacy", "leadership", "fun_creative"}
        assert expected.issubset(types)


class TestGetRandomQuestion:
    def test_returns_a_dict(self):
        q = get_random_question()
        assert isinstance(q, dict)
        assert "text" in q

    def test_filter_by_question_type(self):
        q = get_random_question(question_type="personal")
        assert q["question_type"] == "personal"

    def test_filter_by_pageant_type(self):
        q = get_random_question(pageant_type="miss_universe")
        assert q["pageant_type"] == "miss_universe"

    def test_filter_by_difficulty(self):
        q = get_random_question(difficulty="beginner")
        assert q["difficulty"] == "beginner"

    def test_any_filter_returns_any(self):
        q = get_random_question(pageant_type="any", question_type="any", difficulty="any")
        assert isinstance(q, dict)

    def test_exclude_ids_works(self):
        all_ids = {q["id"] for q in load_questions()}
        # Exclude all but potentially a few — should still return something (fallback)
        q = get_random_question(exclude_ids=all_ids)
        assert isinstance(q, dict)

    def test_impossible_filter_falls_back(self):
        # Nonexistent filter value should hit the fallback branch
        q = get_random_question(pageant_type="miss_intergalactic")
        assert isinstance(q, dict)


class TestGetFilterOptions:
    def test_returns_dict_with_expected_keys(self):
        opts = get_filter_options()
        assert "pageant_type" in opts
        assert "question_type" in opts
        assert "difficulty" in opts

    def test_each_filter_has_any_option(self):
        opts = get_filter_options()
        for key, values in opts.items():
            ids = [v[0] for v in values]
            assert "any" in ids, f"Missing 'any' option for {key}"

    def test_new_pageant_types_in_filter_options(self):
        opts = get_filter_options()
        pageant_ids = [v[0] for v in opts["pageant_type"]]
        assert "miss_grand" in pageant_ids
        assert "miss_earth" in pageant_ids
        assert "miss_charm" in pageant_ids


class TestNewPageantQuestions:
    @pytest.mark.parametrize("pageant_type", ["miss_grand", "miss_earth", "miss_charm"])
    def test_new_pageant_type_exists_in_bank(self, pageant_type):
        types = {q["pageant_type"] for q in load_questions()}
        assert pageant_type in types

    @pytest.mark.parametrize("pageant_type", ["miss_grand", "miss_earth", "miss_charm"])
    def test_new_pageant_has_5_questions(self, pageant_type):
        count = sum(1 for q in load_questions() if q["pageant_type"] == pageant_type)
        assert count == 5

    @pytest.mark.parametrize("pageant_type", ["miss_grand", "miss_earth", "miss_charm"])
    def test_filter_by_new_pageant_type(self, pageant_type):
        q = get_random_question(pageant_type=pageant_type)
        assert q["pageant_type"] == pageant_type
