"""Pydantic models for quiz questions."""

import hashlib
import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class Question(BaseModel):
    """A quiz question generated from a chunk."""

    id: str = Field("", alias="_id")
    source_chunk_id: str = ""
    source_id: str = ""
    subject: str = ""
    topic: str = ""
    grade: int = 0
    type: Literal["MCQ", "TrueFalse", "FillInTheBlank"]
    question: str
    options: list[str] | None = None
    answer: str
    difficulty: Literal["easy", "medium", "hard"]
    question_hash: str = ""
    quality_score: float | None = None
    quality_reason: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def validate_type_constraints(self) -> "Question":
        """Enforce type-specific constraints on options and answer."""
        if self.type == "MCQ":
            if not self.options or len(self.options) != 4:
                raise ValueError("MCQ questions must have exactly 4 options")
            if self.answer not in self.options:
                raise ValueError(
                    f"MCQ answer '{self.answer}' must be one of the options"
                )

        elif self.type == "TrueFalse":
            if self.answer not in ("True", "False"):
                raise ValueError("TrueFalse answer must be 'True' or 'False'")
            self.options = ["True", "False"]

        elif self.type == "FillInTheBlank":
            if self.options is not None:
                raise ValueError("FillInTheBlank questions must have options=null")

        return self

    def compute_hash(self) -> str:
        """Compute an MD5 hash of the normalized question text."""
        normalized = re.sub(r"[^\w\s]", "", self.question.lower())
        normalized = re.sub(r"\s+", " ", normalized).strip()
        self.question_hash = hashlib.md5(normalized.encode()).hexdigest()
        return self.question_hash


class GenerateQuizRequest(BaseModel):
    """Request body for POST /generate-quiz."""

    source_id: str
    chunk_ids: list[str] | None = None


class GenerateQuizResponse(BaseModel):
    """Response for POST /generate-quiz."""

    status: str = "generating"
    source_id: str
