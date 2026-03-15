"""Quiz routes.

POST /generate-quiz — Start question generation for a source.
GET /quiz — Retrieve quiz questions (cached, adaptive difficulty).
POST /submit-answer — Submit an answer and update difficulty.
"""

import logging
import random
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query

from app.database import get_database
from app.models.student import SubmitAnswerRequest, SubmitAnswerResponse
from app.models.user import UserInDB
from app.services.adaptive import get_student_difficulty, update_difficulty_after_answer
from app.services.auth import get_current_student, get_current_teacher, get_current_user
from app.services.cache import quiz_cache

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Quiz"])



@router.get("/quiz")
async def get_quiz(
    topic: str = Query(..., description="Topic to filter questions by"),
    student_id: str | None = Query(None, description="Student ID for adaptive difficulty"),
    difficulty: str | None = Query(None, description="Difficulty level (easy/medium/hard)"),
    limit: int = Query(10, ge=1, le=50, description="Max questions to return"),
    grade: int | None = Query(None, description="Grade level filter"),
    current_user: UserInDB = Depends(get_current_user),
):
    """Get quiz questions filtered by topic with optional adaptive difficulty.

    If student_id is provided and difficulty is not, the student's current
    difficulty for this topic is used.
    """
    db = get_database()

    # Resolve difficulty
    effective_difficulty = difficulty
    if effective_difficulty is None and student_id:
        # Look up student's difficulty for this topic — need subject info
        # We'll query one question to get the subject
        sample = await db.questions.find_one({"topic": topic})
        subject = sample.get("subject", "General") if sample else "General"
        effective_difficulty = await get_student_difficulty(
            db, student_id, subject, topic
        )

    # Check cache
    cache_key = f"quiz::{topic}::{effective_difficulty}::{grade}::{limit}"
    cached = quiz_cache.get(cache_key)
    if cached is not None:
        # Shuffle cached results for variety
        result = list(cached)
        random.shuffle(result)
        return result

    # Build MongoDB query for specific difficulty
    query: dict = {"topic": topic}
    if grade is not None:
        query["grade"] = grade

    questions = []
    
    if effective_difficulty:
        query["difficulty"] = effective_difficulty
        cursor = db.questions.find(query).limit(limit)
        questions = await cursor.to_list(length=limit)
    
    # If we didn't get enough questions, fetch from other difficulties
    if len(questions) < limit:
        remaining = limit - len(questions)
        fallback_query = {"topic": topic}
        if grade is not None:
            fallback_query["grade"] = grade
        if effective_difficulty:
            fallback_query["difficulty"] = {"$ne": effective_difficulty}
            
        cursor = db.questions.find(fallback_query).limit(remaining)
        fallback_questions = await cursor.to_list(length=remaining)
        questions.extend(fallback_questions)

    # Clean up MongoDB _id for response
    for q in questions:
        q["id"] = q.pop("_id", q.get("id", ""))

    # Cache the results
    quiz_cache.set(cache_key, questions)

    # Shuffle for variety
    random.shuffle(questions)

    return questions

@router.get("/topics")
async def get_topics(current_user: UserInDB = Depends(get_current_user)):
    """Retrieve all distinct topics available in the database, with their subjects."""
    db = get_database()
    pipeline = [
        {"$group": {"_id": "$topic", "subject": {"$first": "$subject"}}},
        {"$project": {"_id": 0, "topic": "$_id", "subject": 1}}
    ]
    topics = await db.questions.aggregate(pipeline).to_list(length=None)
    return topics


@router.post("/submit-answer", response_model=SubmitAnswerResponse)
async def submit_answer(
    request: SubmitAnswerRequest,
    current_user: UserInDB = Depends(get_current_student),
):
    """Submit a student's answer to a question.

    Records the answer, checks correctness, and updates the
    student's adaptive difficulty for the relevant topic.
    """
    db = get_database()

    # Look up the question
    question = await db.questions.find_one({"_id": request.question_id})
    if not question:
        raise HTTPException(
            status_code=404,
            detail=f"Question {request.question_id} not found",
        )

    # Force string conversion before stripping to be absolutely safe
    student_ans = str(request.selected_answer).strip().lower()
    correct_ans = str(question.get("answer", "")).strip().lower()
    is_correct = student_ans == correct_ans
    
    topic = question.get("topic", "General")
    subject = question.get("subject", "General")

    student_id = current_user.id

    # Record the answer
    answer_doc = {
        "student_id": student_id,
        "question_id": request.question_id,
        "selected_answer": request.selected_answer,
        "is_correct": is_correct,
        "submitted_at": datetime.utcnow(),
    }
    await db.answers.insert_one(answer_doc)

    # Update adaptive difficulty
    new_difficulty = await update_difficulty_after_answer(
        db=db,
        student_id=student_id,
        question_id=request.question_id,
        is_correct=is_correct,
        subject=subject,
        topic=topic,
    )

    return SubmitAnswerResponse(
        is_correct=is_correct,
        correct_answer=question["answer"],
        new_difficulty=new_difficulty,
        topic=topic,
    )


@router.delete("/quiz/{question_id}")
async def delete_question(
    question_id: str,
    current_user: UserInDB = Depends(get_current_teacher),
):
    """Delete a single quiz question by ID."""
    db = get_database()

    result = await db.questions.delete_one({"_id": question_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"Question {question_id} not found")

    return {"deleted": True, "question_id": question_id}
