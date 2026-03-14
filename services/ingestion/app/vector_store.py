"""Qdrant vector store client and collection setup."""

import hashlib
import logging

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from app.config import settings

logger = logging.getLogger(__name__)

QUESTION_COLLECTION = "questions"
CHUNK_COLLECTION = "chunks"
VECTOR_SIZE = 384  # all-MiniLM-L6-v2 output dimension


_qdrant_client: QdrantClient | None = None


def get_qdrant_client() -> QdrantClient:
    """Get or create the Qdrant client singleton."""
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
        )
    return _qdrant_client


def init_collections(client: QdrantClient | None = None) -> None:
    """Create Qdrant collections if they don't already exist. Idempotent."""
    if client is None:
        client = get_qdrant_client()

    existing = {c.name for c in client.get_collections().collections}

    for name in (QUESTION_COLLECTION, CHUNK_COLLECTION):
        if name not in existing:
            client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(
                    size=VECTOR_SIZE, distance=Distance.COSINE
                ),
            )
            # Create payload indexes for filtering
            from qdrant_client.models import PayloadSchemaType
            if name == QUESTION_COLLECTION:
                client.create_payload_index(name, field_name="topic", field_schema=PayloadSchemaType.KEYWORD)
                client.create_payload_index(name, field_name="subject", field_schema=PayloadSchemaType.KEYWORD)
            elif name == CHUNK_COLLECTION:
                client.create_payload_index(name, field_name="source_id", field_schema=PayloadSchemaType.KEYWORD)
            logger.info(f"Created Qdrant collection: {name}")
        else:
            logger.info(f"Qdrant collection already exists: {name}")


def str_to_point_id(s: str) -> int:
    """Convert a string ID to a deterministic uint64 for Qdrant point IDs."""
    return int(hashlib.md5(s.encode()).hexdigest(), 16) % (2**63)
