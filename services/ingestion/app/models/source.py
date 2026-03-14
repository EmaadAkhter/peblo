"""Pydantic models for sources and chunks."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class Source(BaseModel):
    """A PDF source document."""

    id: str = Field(..., alias="_id")
    filename: str
    grade: int
    subject: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    status: Literal["processing", "completed", "failed"] = "processing"
    chunk_count: int = 0

    model_config = {"populate_by_name": True}


class Chunk(BaseModel):
    """A text chunk extracted from a PDF source."""

    id: str = Field(..., alias="_id")
    source_id: str
    grade: int
    subject: str
    topic: str = ""
    text: str
    chunk_index: int

    model_config = {"populate_by_name": True}


class IngestResponse(BaseModel):
    """Response returned immediately after starting ingestion."""

    source_id: str
    status: str = "processing"
