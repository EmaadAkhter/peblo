"""Adaptive difficulty engine.

Tracks per-student, per-topic difficulty using a rolling window of the
last 5 answers. Promotes on 4/5 correct, demotes on 3/5 incorrect.
"""

import logging
from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

DIFFICULTY_LEVELS = ["easy", "medium", "hard"]
WINDOW_SIZE = 5
PROMOTE_THRESHOLD = 4  # 4 out of 5 correct to promote
DEMOTE_THRESHOLD = 3  # 3 out of 5 incorrect to demote


def _next_difficulty(current: str) -> str:
    """Get the next higher difficulty level."""
    idx = DIFFICULTY_LEVELS.index(current)
    return DIFFICULTY_LEVELS[min(idx + 1, len(DIFFICULTY_LEVELS) - 1)]


def _prev_difficulty(current: str) -> str:
    """Get the next lower difficulty level."""
    idx = DIFFICULTY_LEVELS.index(current)
    return DIFFICULTY_LEVELS[max(idx - 1, 0)]


def compute_new_difficulty(
    current_difficulty: str, recent_answers: list[bool]
) -> str:
    """Compute new difficulty based on a window of recent correctness values.

    Args:
        current_difficulty: Current difficulty level (easy/medium/hard).
        recent_answers: List of is_correct booleans, most recent last.
                       Should be at most WINDOW_SIZE items.

    Returns:
        The new difficulty level.
    """
    if not recent_answers:
        return current_difficulty

    # Take only the last WINDOW_SIZE answers
    window = recent_answers[-WINDOW_SIZE:]
    correct_count = sum(window)
    incorrect_count = len(window) - correct_count

    if correct_count >= PROMOTE_THRESHOLD:
        return _next_difficulty(current_difficulty)
    elif incorrect_count >= DEMOTE_THRESHOLD:
        return _prev_difficulty(current_difficulty)

    return current_difficulty


async def get_student_difficulty(
    db: AsyncIOMotorDatabase, student_id: str, subject: str, topic: str
) -> str:
    """Get a student's current difficulty for a subject::topic.

    Creates a profile with default 'easy' if none exists.
    """
    topic_key = f"{subject}::{topic}"
    profile = await db.student_profiles.find_one({"_id": student_id})

    if profile is None:
        # Create a new profile with default difficulty
        await db.student_profiles.insert_one(
            {
                "_id": student_id,
                "difficulty_state": {topic_key: "easy"},
                "last_updated": datetime.utcnow(),
            }
        )
        return "easy"

    return profile.get("difficulty_state", {}).get(topic_key, "easy")


async def update_difficulty_after_answer(
    db: AsyncIOMotorDatabase,
    student_id: str,
    question_id: str,
    is_correct: bool,
    subject: str,
    topic: str,
) -> str:
    """Process an answer and potentially update the student's difficulty.

    Returns the student's new difficulty for this topic.
    """
    topic_key = f"{subject}::{topic}"

    # Get current difficulty
    current = await get_student_difficulty(db, student_id, subject, topic)

    # Get the last WINDOW_SIZE answers for this student + topic
    # We need to join through question_id to get topic info,
    # but since we already know the topic, we query answers that
    # reference questions with this topic
    pipeline = [
        {"$match": {"student_id": student_id}},
        {
            "$lookup": {
                "from": "questions",
                "localField": "question_id",
                "foreignField": "_id",
                "as": "question",
            }
        },
        {"$unwind": "$question"},
        {
            "$match": {
                "question.subject": subject,
                "question.topic": topic,
            }
        },
        {"$sort": {"submitted_at": -1}},
        {"$limit": WINDOW_SIZE},
        {"$project": {"is_correct": 1}},
    ]

    cursor = db.answers.aggregate(pipeline)
    recent_docs = await cursor.to_list(length=WINDOW_SIZE)

    # recent_docs are newest-first, reverse for chronological order
    recent_answers = [doc["is_correct"] for doc in reversed(recent_docs)]

    new_difficulty = compute_new_difficulty(current, recent_answers)

    if new_difficulty != current:
        logger.info(
            f"Student {student_id} difficulty for {topic_key}: "
            f"{current} → {new_difficulty}"
        )

    # Update the student profile
    await db.student_profiles.update_one(
        {"_id": student_id},
        {
            "$set": {
                f"difficulty_state.{topic_key}": new_difficulty,
                "last_updated": datetime.utcnow(),
            }
        },
        upsert=True,
    )

    return new_difficulty
