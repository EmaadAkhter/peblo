"""Student profile routes.

GET /student/{student_id}/profile — View a student's difficulty state.
"""

from fastapi import APIRouter, Depends, HTTPException

from app.database import get_database
from app.models.user import UserInDB
from app.services.auth import get_current_user

router = APIRouter(tags=["Students"])


@router.get("/student/{student_id}/profile")
async def get_student_profile(
    student_id: str,
    current_user: UserInDB = Depends(get_current_user),
):
    """Get a student's profile including their per-topic difficulty state."""
    db = get_database()
    profile = await db.student_profiles.find_one({"_id": student_id})

    if not profile:
        raise HTTPException(
            status_code=404,
            detail=f"Student {student_id} not found. "
            f"Profiles are created on first answer submission.",
        )

    return {
        "student_id": profile["_id"],
        "difficulty_state": profile.get("difficulty_state", {}),
        "last_updated": profile.get("last_updated"),
    }
