"""Quiz question generation using Groq LLM.

Generates 5 questions per chunk (2 MCQ, 1 TrueFalse, 1 FillInTheBlank, 1 any).
Includes structural validation, retry on bad JSON, quality scoring, and
semantic dedup via Qdrant embeddings.
"""

import json
import logging
from datetime import datetime

from groq import Groq
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError

from app.config import groq_key_rotator
from app.models.question import Question
from app.services.embeddings import embed
from app.services.similarity import (
    check_question_duplicate_safe,
    store_question_vector_safe,
)
from app.utils.id_generator import generate_question_id
from app.vector_store import get_qdrant_client

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = (
    "You are an educational content specialist creating quiz questions "
    "for grade {grade} students.\n"
    "Generate quiz questions strictly based on the provided text. "
    "Do not add outside knowledge.\n"
    "You must respond with valid JSON only — no markdown, no explanation, no preamble."
)

USER_PROMPT = """Text: {chunk_text}

Identify up to 2 core facts or concepts from this text. For each concept, generate exactly 3 question variants testing that same concept:
1. Multiple Choice (MCQ) - exactly 4 options
2. True / False - options must be exactly ["True", "False"]
3. Fill in the Blank - no options (null)

Return a JSON array of "Concept Groups" with exactly this schema per item:
{{
  "concept": "A short summary of the core fact being tested",
  "questions": [
    {{
      "question": "string",
      "type": "MCQ" | "TrueFalse" | "FillInTheBlank",
      "options": ["string"] or null,
      "answer": "string",
      "difficulty": "easy" | "medium" | "hard"
    }}
  ]
}}

Requirements:
- Each group's `questions` array MUST contain exactly 3 questions: one MCQ, one TrueFalse, and one FillInTheBlank.
- All 3 questions in a group must test the same core concept but be phrased independently.
- Distribute difficulties logically based on how the question is phrased."""

QUALITY_SYSTEM_PROMPT = (
    "You are an educational quality reviewer. Respond with valid JSON only."
)

QUALITY_USER_PROMPT = """Rate each of these quiz questions for a grade {grade} student.
Return a JSON array, one object per question, with:
{{ "index": int, "score": float (0.0-1.0), "reason": "one sentence" }}

Score on: clarity, age-appropriateness, answerability from the text alone.
A score below 0.6 means the question should be discarded.

Questions:
{questions_json}"""


def _get_groq_client() -> Groq:
    """Get a Groq client with the next API key in rotation."""
    return Groq(api_key=next(groq_key_rotator))


def _parse_json_response(text: str) -> list[dict] | None:
    """Attempt to parse a JSON array from the LLM response.

    Handles common issues like markdown code fences.
    """
    # Strip markdown code fences if present
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first and last lines (``` markers)
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)

    try:
        result = json.loads(text)
        if isinstance(result, list):
            return result
        return None
    except json.JSONDecodeError:
        return None


def _generate_questions_raw(
    chunk_text: str, grade: int
) -> list[dict] | None:
    """Call Groq to generate questions, with one retry on JSON failure."""
    client = _get_groq_client()

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.format(grade=grade)},
        {"role": "user", "content": USER_PROMPT.format(chunk_text=chunk_text)},
    ]

    # First attempt
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.7,
        max_tokens=2000,
    )

    result_text = response.choices[0].message.content or ""
    parsed = _parse_json_response(result_text)

    if parsed is not None:
        return parsed

    # Retry with "fix your JSON" follow-up
    logger.warning("First Groq response wasn't valid JSON, retrying...")
    messages.append({"role": "assistant", "content": result_text})
    messages.append(
        {
            "role": "user",
            "content": (
                "Your response was not valid JSON. Please return ONLY a valid "
                "JSON array with no markdown formatting, no explanation. "
                "Just the raw JSON array."
            ),
        }
    )

    retry_response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.3,
        max_tokens=2000,
    )

    retry_text = retry_response.choices[0].message.content or ""
    return _parse_json_response(retry_text)

def _flatten_concept_groups(groups: list[dict]) -> list[dict]:
    """Flatten an array of Concept Groups into a flat list of questions."""
    flat_questions = []
    for group in groups:
        if not isinstance(group, dict):
            continue
        questions = group.get("questions", [])
        if isinstance(questions, list):
            flat_questions.extend(questions)
    return flat_questions


def _validate_questions(
    raw_questions: list[dict],
    source_id: str,
    chunk_id: str,
    subject: str,
    topic: str,
    grade: int,
) -> list[Question]:
    """Validate raw question dicts against the Pydantic Question model.

    Drops (does not raise) any question that fails validation.
    """
    valid = []
    for idx, q_dict in enumerate(raw_questions):
        try:
            question = Question(
                _id=generate_question_id(source_id, chunk_id, idx),
                source_chunk_id=chunk_id,
                source_id=source_id,
                subject=subject,
                topic=topic,
                grade=grade,
                type=q_dict.get("type", ""),
                question=q_dict.get("question", ""),
                options=q_dict.get("options"),
                answer=q_dict.get("answer", ""),
                difficulty=q_dict.get("difficulty", "easy"),
                created_at=datetime.utcnow(),
            )
            question.compute_hash()
            valid.append(question)
        except Exception as e:
            logger.warning(
                f"Question {idx} from chunk {chunk_id} failed validation: {e}"
            )

    return valid


def _score_questions(
    questions: list[Question], grade: int
) -> list[Question]:
    """Score questions for quality using Groq. Best-effort - falls back gracefully."""
    if not questions:
        return questions

    try:
        client = _get_groq_client()

        questions_data = [
            {"index": i, "question": q.question, "type": q.type, "answer": q.answer}
            for i, q in enumerate(questions)
        ]

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": QUALITY_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": QUALITY_USER_PROMPT.format(
                        grade=grade,
                        questions_json=json.dumps(questions_data),
                    ),
                },
            ],
            temperature=0,
            max_tokens=1000,
        )

        scores_text = response.choices[0].message.content or ""
        scores = _parse_json_response(scores_text)

        if scores is None:
            logger.warning("Quality scoring returned invalid JSON, keeping all questions")
            return questions

        # Build index → score mapping
        score_map = {}
        for s in scores:
            if isinstance(s, dict) and "index" in s and "score" in s:
                score_map[s["index"]] = (
                    float(s["score"]),
                    s.get("reason", ""),
                )

        # Filter and annotate
        scored_questions = []
        for i, q in enumerate(questions):
            if i in score_map:
                score, reason = score_map[i]
                if score < 0.6:
                    logger.info(
                        f"Dropping low-quality question (score={score}): {q.question[:60]}..."
                    )
                    continue
                q.quality_score = score
                q.quality_reason = reason
            scored_questions.append(q)

        return scored_questions

    except Exception as e:
        logger.warning(f"Quality scoring failed, keeping all questions: {e}")
        return questions


async def generate_questions_for_chunk(
    db: AsyncIOMotorDatabase,
    source_id: str,
    chunk_id: str,
    chunk_text: str,
    subject: str,
    topic: str,
    grade: int,
) -> int:
    """Generate, validate, score, deduplicate, and store questions for a single chunk.

    Returns the number of questions stored.
    """
    # Generate raw Concept Groups via Groq
    try:
        raw_groups = _generate_questions_raw(chunk_text, grade)
    except Exception as e:
        logger.error(f"Groq generation failed for chunk {chunk_id}: {e}")
        return 0

    if raw_groups is None:
        logger.warning(f"Could not parse groups for chunk {chunk_id} after retry")
        return 0

    # Flatten Concept Groups into a list of questions
    raw_questions = _flatten_concept_groups(raw_groups)

    if not raw_questions:
        logger.warning(f"No valid questions extracted after flattening for chunk {chunk_id}")
        return 0

    # Validate against Pydantic model
    valid_questions = _validate_questions(
        raw_questions, source_id, chunk_id, subject, topic, grade
    )

    if len(valid_questions) < 3:
        logger.warning(
            f"Only {len(valid_questions)} valid questions from chunk {chunk_id},"
            f" minimum is 3 — skipping"
        )
        return 0

    # Quality scoring (best-effort)
    scored_questions = _score_questions(valid_questions, grade)

    if len(scored_questions) < 3:
        logger.warning(
            f"Only {len(scored_questions)} questions passed quality scoring "
            f"from chunk {chunk_id}, minimum is 3 — skipping"
        )
        return 0

    # Get Qdrant client for semantic dedup
    try:
        qdrant = get_qdrant_client()
    except Exception:
        qdrant = None

    stored = 0
    for question in scored_questions:
        # Semantic dedup via Qdrant
        try:
            vector = embed(question.question)
        except Exception as e:
            logger.warning(f"Embedding failed for question: {e}")
            vector = None

        if vector and check_question_duplicate_safe(qdrant, vector, topic, subject):
            logger.info(f"Skipping semantically duplicate question: {question.question[:60]}...")
            continue

        # Insert into MongoDB (hash-based dedup as fallback)
        doc = question.model_dump(by_alias=True)
        try:
            await db.questions.insert_one(doc)
        except DuplicateKeyError:
            logger.info(f"Skipping hash-duplicate question: {question.id}")
            continue

        # Store vector in Qdrant (after successful MongoDB insert)
        if vector:
            store_question_vector_safe(
                qdrant,
                question.id,
                vector,
                {
                    "question_id": question.id,
                    "source_id": source_id,
                    "topic": topic,
                    "subject": subject,
                    "grade": grade,
                },
            )

        stored += 1

    return stored


async def generate_questions_for_source(
    db: AsyncIOMotorDatabase,
    source_id: str,
    chunk_ids: list[str] | None = None,
) -> int:
    """Generate questions for all (or specific) chunks of a source.

    Returns the total number of questions stored.
    """
    # Get the source document
    source = await db.sources.find_one({"_id": source_id})
    if not source:
        raise ValueError(f"Source {source_id} not found")

    # Query chunks
    query = {"source_id": source_id}
    if chunk_ids:
        query["_id"] = {"$in": chunk_ids}

    cursor = db.chunks.find(query)
    chunks = await cursor.to_list(length=None)

    if not chunks:
        logger.warning(f"No chunks found for source {source_id}")
        return 0

    total_stored = 0
    for chunk_doc in chunks:
        count = await generate_questions_for_chunk(
            db=db,
            source_id=source_id,
            chunk_id=chunk_doc["_id"],
            chunk_text=chunk_doc["text"],
            subject=chunk_doc.get("subject", source.get("subject", "")),
            topic=chunk_doc.get("topic", "General"),
            grade=chunk_doc.get("grade", source.get("grade", 1)),
        )
        total_stored += count

    logger.info(
        f"Generated {total_stored} questions for source {source_id} "
        f"across {len(chunks)} chunks"
    )

    return total_stored
