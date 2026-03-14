from typing import Optional
from pydantic import BaseModel, Field


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    role: str = Field(..., description="Must be 'teacher' or 'student'")
    grade: Optional[int] = Field(None, ge=1, le=12)


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserInDB(UserBase):
    id: str = Field(..., alias="_id")
    hashed_password: str

    model_config = {"populate_by_name": True}


class UserResponse(UserBase):
    id: str = Field(...)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None
    grade: Optional[int] = None
    student_id: Optional[str] = None
