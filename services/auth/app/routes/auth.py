"""Auth routes: register, login, and current user retrieval."""

from datetime import timedelta
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.config import settings
from app.database import get_database
from app.models.user import Token, UserCreate, UserInDB, UserResponse
from app.services.auth import create_access_token, get_current_user, get_password_hash, verify_password

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_in: UserCreate):
    """Create a new user account."""
    db = get_database()

    if await db.users.find_one({"username": user_in.username}):
        raise HTTPException(status_code=400, detail="Username already registered")

    if user_in.role not in {"teacher", "student"}:
        raise HTTPException(status_code=400, detail="Role must be 'teacher' or 'student'")

    count = await db.users.count_documents({})
    user_id = f"U_{count + 1:04d}"

    hashed_password = get_password_hash(user_in.password)
    user_doc = {
        "_id": user_id,
        "username": user_in.username,
        "hashed_password": hashed_password,
        "role": user_in.role,
        "grade": user_in.grade if user_in.role == "student" else None,
    }

    await db.users.insert_one(user_doc)
    return UserResponse(id=user_id, username=user_in.username, role=user_in.role, grade=user_doc["grade"])


@router.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Verify credentials and return a JWT access token."""
    db = get_database()
    user_doc = await db.users.find_one({"username": form_data.username})

    if not user_doc or not verify_password(form_data.password, user_doc["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_payload = {"sub": user_doc["username"], "role": user_doc["role"]}
    if user_doc["role"] == "student":
        token_payload["grade"] = user_doc.get("grade")
        token_payload["student_id"] = user_doc["_id"]

    access_token = create_access_token(
        data=token_payload,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: UserInDB = Depends(get_current_user)):
    """Return the currently authenticated user profile."""
    return UserResponse(id=current_user.id, username=current_user.username, role=current_user.role, grade=current_user.grade)
