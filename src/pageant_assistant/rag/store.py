"""Chroma vector store: initialisation, retrieval, and chunk management.

Provides a module-level singleton client and collection, lazily initialised
on first access.  All public functions degrade gracefully on failure so that
the coaching pipeline always continues even if the evidence store is unavailable.
"""

from __future__ import annotations

import logging
from typing import Any

import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

from pageant_assistant.config.settings import CHROMA_DIR, RAG_COLLECTION_NAME

logger = logging.getLogger(__name__)

# Module-level singletons — lazily initialised by _get_collection()
_client: chromadb.PersistentClient | None = None
_collection: chromadb.Collection | None = None


def _get_collection() -> chromadb.Collection:
    """Return (or create) the singleton Chroma collection.

    Creates CHROMA_DIR on disk if it does not exist.  The collection uses
    Chroma's DefaultEmbeddingFunction (all-MiniLM-L6-v2 via onnxruntime) so
    no additional API keys are required.

    Returns:
        The active Chroma Collection instance.

    Raises:
        Exception: Propagates any Chroma initialisation error to the caller.
    """
    global _client, _collection
    if _collection is None:
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        logger.debug("Initialising Chroma persistent client at %s", CHROMA_DIR)
        _client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        _collection = _client.get_or_create_collection(
            name=RAG_COLLECTION_NAME,
            embedding_function=DefaultEmbeddingFunction(),
        )
        logger.info(
            "Chroma collection '%s' ready — %d chunk(s) on disk",
            RAG_COLLECTION_NAME,
            _collection.count(),
        )
    return _collection


def collection_size() -> int:
    """Return the number of documents in the collection.

    Returns:
        Document count, or 0 if the collection cannot be accessed.

    Example:
        >>> collection_size()
        18
    """
    try:
        return _get_collection().count()
    except Exception as exc:
        logger.warning("collection_size() failed: %s", exc)
        return 0


def retrieve_evidence(query: str, n_results: int = 6) -> list[dict[str, Any]]:
    """Retrieve the top-n most semantically similar chunks for *query*.

    Args:
        query: The natural-language question or topic to search for.
        n_results: Maximum number of candidates to return.

    Returns:
        List of dicts with keys ``text``, ``source``, ``chunk_type``, and
        ``topic``.  Returns an empty list if the collection is empty or if
        retrieval fails for any reason.

    Example:
        >>> chunks = retrieve_evidence("women's rights in Kenya", n_results=3)
        >>> len(chunks) <= 3
        True
    """
    try:
        col = _get_collection()
        count = col.count()
        if count == 0:
            logger.debug("retrieve_evidence: collection empty — skipping query")
            return []
        actual_n = min(n_results, count)
        logger.debug(
            "retrieve_evidence: querying top-%d for %r …", actual_n, query[:80]
        )
        results = col.query(
            query_texts=[query],
            n_results=actual_n,
            include=["documents", "metadatas"],
        )
        chunks: list[dict[str, Any]] = [
            {
                "text": doc,
                "source": meta.get("source", ""),
                "chunk_type": meta.get("chunk_type", "general"),
                "topic": meta.get("topic", ""),
            }
            for doc, meta in zip(results["documents"][0], results["metadatas"][0])
        ]
        logger.info("retrieve_evidence: returned %d candidate chunk(s)", len(chunks))
        return chunks
    except Exception as exc:
        logger.warning("retrieve_evidence failed: %s", exc)
        return []


def add_chunks(chunks: list[dict[str, Any]]) -> None:
    """Upsert evidence chunks into the collection.

    Args:
        chunks: List of dicts, each requiring keys:
            - ``id`` (str): Unique chunk identifier (used for upsert dedup).
            - ``text`` (str): The document content to embed and store.
            - ``metadata`` (dict): String-valued metadata (topic, chunk_type, source).

    Example:
        >>> add_chunks([{"id": "test-01", "text": "Hello world", "metadata": {}}])
    """
    if not chunks:
        logger.debug("add_chunks: empty list — nothing to upsert")
        return
    col = _get_collection()
    col.upsert(
        ids=[c["id"] for c in chunks],
        documents=[c["text"] for c in chunks],
        metadatas=[c["metadata"] for c in chunks],
    )
    logger.info(
        "add_chunks: upserted %d chunk(s) into collection '%s'",
        len(chunks),
        RAG_COLLECTION_NAME,
    )
