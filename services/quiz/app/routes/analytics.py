from datetime import datetime
from fastapi import APIRouter, Depends, Query
import logging

from app.database import get_database
from app.services.auth import get_current_teacher
from app.models.user import UserInDB

router = APIRouter(prefix="/analytics", tags=["analytics"])
logger = logging.getLogger(__name__)

@router.get("/students")
async def get_student_analytics(
    current_user: UserInDB = Depends(get_current_teacher),
):
    """Get aggregated analytics for all students across all topics."""
    db = get_database()
    
    # We will use an aggregation pipeline to group answers by student and topic
    pipeline = [
        # Lookup question details to get the topic and subject
        {
            "$lookup": {
                "from": "questions",
                "localField": "question_id",
                "foreignField": "_id",
                "as": "question"
            }
        },
        {"$unwind": "$question"},
        
        # Group by student_id and topic
        {
            "$group": {
                "_id": {
                    "student_id": "$student_id",
                    "topic": "$question.topic"
                },
                "total_questions": {"$sum": 1},
                "correct_answers": {
                    "$sum": {"$cond": [{"$eq": ["$is_correct", True]}, 1, 0]}
                },
                "subject": {"$first": "$question.subject"},
                "last_activity": {"$max": "$submitted_at"},
                "answers": {
                    "$push": {
                        "question_id": "$question_id",
                        "question_text": "$question.question",
                        "selected_answer": "$selected_answer",
                        "correct_answer": "$question.answer",
                        "is_correct": "$is_correct",
                        "submitted_at": "$submitted_at"
                    }
                }
            }
        },
        
        # Format the result document
        {
            "$project": {
                "_id": 0,
                "student_id": "$_id.student_id",
                "topic": "$_id.topic",
                "subject": 1,
                "total_questions": 1,
                "correct_answers": 1,
                "score_percentage": {
                    "$multiply": [
                        {"$divide": ["$correct_answers", "$total_questions"]},
                        100
                    ]
                },
                "last_activity": 1,
                "answers": 1
            }
        },
        
        # Sort by last_activity descending
        {"$sort": {"last_activity": -1}}
    ]

    results = await db.answers.aggregate(pipeline).to_list(length=None)

    # Collect all unique student IDs to fetch usernames
    student_ids = {r["student_id"] for r in results}
    
    users = await db.users.find(
        {"_id": {"$in": list(student_ids)}}, 
        {"username": 1}
    ).to_list(length=None)
    
    user_map = {u["_id"]: u["username"] for u in users}

    # Attach usernames to results
    for r in results:
        r["student_name"] = user_map.get(r["student_id"], "Unknown Student")

    return results
