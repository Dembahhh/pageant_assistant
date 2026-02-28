"""Tests for the ChromaDB vector store (no API key required)."""

import pytest

import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction


@pytest.fixture
def chroma_collection(tmp_path):
    """Create a temporary Chroma collection for test isolation."""
    client = chromadb.PersistentClient(path=str(tmp_path / "chroma"))
    collection = client.get_or_create_collection(
        name="test_evidence",
        embedding_function=DefaultEmbeddingFunction(),
    )
    return collection


@pytest.fixture
def seeded_collection(chroma_collection):
    """Seed the test collection with sample chunks."""
    chunks = [
        {
            "id": "test-mental-health-01",
            "text": "One in seven adolescents globally experiences a mental health condition.",
            "metadata": {"topic": "mental_health", "chunk_type": "stat", "source": "WHO 2021"},
        },
        {
            "id": "test-education-01",
            "text": "244 million children and youth are out of school worldwide.",
            "metadata": {"topic": "education", "chunk_type": "stat", "source": "UNESCO 2022"},
        },
        {
            "id": "test-leadership-01",
            "text": "Companies with women in leadership outperform peers by 39 percent.",
            "metadata": {"topic": "leadership", "chunk_type": "stat", "source": "McKinsey 2023"},
        },
    ]
    chroma_collection.upsert(
        ids=[c["id"] for c in chunks],
        documents=[c["text"] for c in chunks],
        metadatas=[c["metadata"] for c in chunks],
    )
    return chroma_collection


class TestChromaBasics:
    def test_empty_collection_has_zero_count(self, chroma_collection):
        assert chroma_collection.count() == 0

    def test_add_and_count(self, seeded_collection):
        assert seeded_collection.count() == 3

    def test_upsert_is_idempotent(self, seeded_collection):
        # Re-upsert the same chunk — count should not increase
        seeded_collection.upsert(
            ids=["test-mental-health-01"],
            documents=["Updated text for the same ID."],
            metadatas=[{"topic": "mental_health", "chunk_type": "stat", "source": "WHO 2021"}],
        )
        assert seeded_collection.count() == 3


class TestRetrieval:
    def test_query_returns_results(self, seeded_collection):
        results = seeded_collection.query(
            query_texts=["youth mental health"],
            n_results=2,
            include=["documents", "metadatas"],
        )
        assert len(results["documents"][0]) <= 2
        assert len(results["documents"][0]) >= 1

    def test_query_relevance_order(self, seeded_collection):
        results = seeded_collection.query(
            query_texts=["women in leadership positions"],
            n_results=3,
            include=["documents", "metadatas"],
        )
        # The leadership chunk should be the top result
        top_doc = results["documents"][0][0]
        assert "leadership" in top_doc.lower() or "women" in top_doc.lower()

    def test_metadata_preserved(self, seeded_collection):
        results = seeded_collection.query(
            query_texts=["education access"],
            n_results=1,
            include=["documents", "metadatas"],
        )
        meta = results["metadatas"][0][0]
        assert "source" in meta
        assert "topic" in meta

    def test_query_n_results_capped(self, seeded_collection):
        # Ask for more results than exist
        results = seeded_collection.query(
            query_texts=["any topic"],
            n_results=100,
            include=["documents"],
        )
        assert len(results["documents"][0]) == 3
