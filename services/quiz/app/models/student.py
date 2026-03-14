"""Pydantic models for students and answer submissions."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class StudentProfile(BaseModel):
    """Student profile with per-topic difficulty state."""

    id: str = Field(..., alias="_id")
    difficulty_state: dict[str, Literal["easy", "medium", "hard"]] = Field(
        default_factory=dict
    )
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"populate_by_name": True}


class Answer(BaseModel):
    """A student's answer to a question."""

    student_id: str
    question_id: str
    selected_answer: str
    is_correct: bool
    submitted_at: datetime = Field(default_factory=datetime.utcnow)


class SubmitAnswerRequest(BaseModel):
    """Request body for POST /submit-answer."""

    question_id: str
    selected_answer: str


class SubmitAnswerResponse(BaseModel):
    """Response from POST /submit-answer."""

    is_correct: bool
    correct_answer: str
    new_difficulty: str
    topic: str
