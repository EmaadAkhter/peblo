"""MongoDB connection for the auth service."""

import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import settings

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


def get_client() -> AsyncIOMotorClient:
    """Return the MongoDB client singleton."""
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(settings.mongodb_uri)
    return _client


def get_database() -> AsyncIOMotorDatabase:
    """Return the application database handle."""
    global _db
    if _db is None:
        _db = get_client()[settings.database_name]
    return _db


async def close_client() -> None:
    """Close the MongoDB client."""
    global _client, _db
    if _client is not None:
        _client.close()
        _client = None
        _db = None

async def create_indexes() -> None:
    """Create all required MongoDB indexes."""
    db = get_database()

    # chunks: { source_id: 1, topic: 1 }
    await db.chunks.create_index(
        [("source_id", 1), ("topic", 1)],
        name="idx_chunks_source_topic",
    )

    # questions: { topic: 1, difficulty: 1, grade: 1 }
    await db.questions.create_index(
        [("topic", 1), ("difficulty", 1), ("grade", 1)],
        name="idx_questions_topic_diff_grade",
    )

    # questions: unique on question_hash
    await db.questions.create_index(
        "question_hash",
        name="idx_questions_hash_unique",
        unique=True,
    )

    # answers: { student_id: 1, submitted_at: -1 }
    await db.answers.create_index(
        [("student_id", 1), ("submitted_at", -1)],
        name="idx_answers_student_time",
    )

    logger.info("MongoDB indexes created/verified")
