"""Vector-based similarity detection using Qdrant.

Handles duplicate detection for both questions and chunks,
with fallback to hash-based detection on Qdrant unavailability.
"""

import logging

from qdrant_client import QdrantClient
from qdrant_client.models import (
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
)

from app.vector_store import (
    CHUNK_COLLECTION,
    QUESTION_COLLECTION,
    str_to_point_id,
)

logger = logging.getLogger(__name__)

QUESTION_SIMILARITY_THRESHOLD = 0.92
CHUNK_SIMILARITY_THRESHOLD = 0.95


def is_duplicate_question(
    client: QdrantClient, vector: list[float], topic: str, subject: str
) -> bool:
    """Check if a semantically similar question already exists for this topic+subject."""
    results = client.query_points(
        collection_name=QUESTION_COLLECTION,
        query=vector,
        query_filter=Filter(
            must=[
                FieldCondition(key="topic", match=MatchValue(value=topic)),
                FieldCondition(key="subject", match=MatchValue(value=subject)),
            ]
        ),
        limit=1,
        score_threshold=QUESTION_SIMILARITY_THRESHOLD,
    )
    return len(results.points) > 0


def store_question_vector(
    client: QdrantClient, question_id: str, vector: list[float], payload: dict
) -> None:
    """Store a question's embedding vector in Qdrant."""
    client.upsert(
        collection_name=QUESTION_COLLECTION,
        points=[
            PointStruct(
                id=str_to_point_id(question_id),
                vector=vector,
                payload=payload,
            )
        ],
    )


def is_duplicate_chunk(
    client: QdrantClient, vector: list[float], source_id: str
) -> bool:
    """Check if a near-identical chunk exists from a different source (catches re-uploads)."""
    results = client.query_points(
        collection_name=CHUNK_COLLECTION,
        query=vector,
        query_filter=Filter(
            must_not=[
                FieldCondition(
                    key="source_id", match=MatchValue(value=source_id)
                )
            ]
        ),
        limit=1,
        score_threshold=CHUNK_SIMILARITY_THRESHOLD,
    )
    return len(results.points) > 0


def store_chunk_vector(
    client: QdrantClient, chunk_id: str, vector: list[float], payload: dict
) -> None:
    """Store a chunk's embedding vector in Qdrant."""
    client.upsert(
        collection_name=CHUNK_COLLECTION,
        points=[
            PointStruct(
                id=str_to_point_id(chunk_id),
                vector=vector,
                payload=payload,
            )
        ],
    )


def check_question_duplicate_safe(
    client: QdrantClient | None,
    vector: list[float],
    topic: str,
    subject: str,
) -> bool:
    """Check for duplicate question with Qdrant fallback.

    If Qdrant is unavailable, returns False (caller should then check hash via MongoDB).
    """
    if client is None:
        return False
    try:
        return is_duplicate_question(client, vector, topic, subject)
    except Exception as e:
        logger.warning(f"Qdrant unavailable, falling back to hash check: {e}")
        return False


def check_chunk_duplicate_safe(
    client: QdrantClient | None,
    vector: list[float],
    source_id: str,
) -> bool:
    """Check for duplicate chunk with Qdrant fallback.

    If Qdrant is unavailable, returns False (skip vector dedup).
    """
    if client is None:
        return False
    try:
        return is_duplicate_chunk(client, vector, source_id)
    except Exception as e:
        logger.warning(f"Qdrant unavailable for chunk dedup: {e}")
        return False


def store_question_vector_safe(
    client: QdrantClient | None,
    question_id: str,
    vector: list[float],
    payload: dict,
) -> None:
    """Store question vector with graceful failure."""
    if client is None:
        return
    try:
        store_question_vector(client, question_id, vector, payload)
    except Exception as e:
        logger.warning(f"Failed to store question vector in Qdrant: {e}")


def store_chunk_vector_safe(
    client: QdrantClient | None,
    chunk_id: str,
    vector: list[float],
    payload: dict,
) -> None:
    """Store chunk vector with graceful failure."""
    if client is None:
        return
    try:
        store_chunk_vector(client, chunk_id, vector, payload)
    except Exception as e:
        logger.warning(f"Failed to store chunk vector in Qdrant: {e}")
