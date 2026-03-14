"""Deterministic, human-readable ID generation.

ID formats:
- Source:   SRC_001, SRC_002, ...
- Chunk:    SRC_001_CH_01, SRC_001_CH_02, ...
- Question: Q_SRC001_CH01_001, Q_SRC001_CH01_002, ...
"""

from pymongo import ReturnDocument
from motor.motor_asyncio import AsyncIOMotorDatabase


async def generate_source_id(db: AsyncIOMotorDatabase) -> str:
    """Generate the next sequential source ID (SRC_001, SRC_002, ...)."""
    # Use find_one_and_update for atomic increment to prevent race conditions
    doc = await db.counters.find_one_and_update(
        {"_id": "source_id"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER
    )
    return f"SRC_{doc['seq']:03d}"


def generate_chunk_id(source_id: str, chunk_index: int) -> str:
    """Generate a chunk ID from its parent source ID and index.

    Example: SRC_001, 0 → SRC_001_CH_01
    """
    return f"{source_id}_CH_{chunk_index + 1:02d}"


def generate_question_id(source_id: str, chunk_id: str, question_index: int) -> str:
    """Generate a question ID from source, chunk, and question index.

    Example: SRC_001, SRC_001_CH_01, 0 → Q_SRC001_CH01_001
    """
    # Strip prefixes for compact ID: SRC_001 → SRC001, SRC_001_CH_01 → CH01
    src_compact = source_id.replace("_", "")
    # Extract just the CH_XX part from the chunk ID
    ch_part = chunk_id.split("_CH_")[-1]
    ch_compact = f"CH{ch_part}"
    return f"Q_{src_compact}_{ch_compact}_{question_index + 1:03d}"
