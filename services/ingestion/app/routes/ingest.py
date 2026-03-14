"""PDF ingestion routes.

POST /ingest — Upload a PDF, start background extraction.
GET /ingest/{source_id}/status — Check ingestion status.
"""

import logging
import os
import tempfile

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile

from app.database import get_database
from app.models.source import IngestResponse, Source
from app.models.question import GenerateQuizRequest, GenerateQuizResponse
from app.models.user import UserInDB
from app.services.auth import get_current_teacher
from app.services.pdf_extractor import process_pdf
from app.services.quiz_generator import generate_questions_for_source
from app.utils.id_generator import generate_source_id

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Ingestion"])


async def _ingest_background(source_id: str, file_path: str, grade: int, subject: str, topic: str | None):
    """Background task: extract text, chunk, and store."""
    db = get_database()
    try:
        chunk_count = await process_pdf(db, source_id, file_path, grade, subject, topic)
        await db.sources.update_one(
            {"_id": source_id},
            {"$set": {"status": "completed", "chunk_count": chunk_count}},
        )
        logger.info(f"Ingestion completed for {source_id}: {chunk_count} chunks")
    except Exception as e:
        logger.error(f"Ingestion failed for {source_id}: {e}")
        await db.sources.update_one(
            {"_id": source_id},
            {"$set": {"status": "failed"}},
        )
    finally:
        # Clean up temp file
        try:
            os.unlink(file_path)
        except OSError:
            pass


@router.post("/ingest", response_model=IngestResponse)
async def ingest_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    grade: int = Form(1),
    subject: str = Form("General"),
    topic: str | None = Form(None),
    current_user: UserInDB = Depends(get_current_teacher),
):
    """Upload a PDF for ingestion.

    The PDF is saved to a temp path, a source document is created
    immediately, and extraction runs as a background task.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    db = get_database()

    # Generate source ID
    source_id = await generate_source_id(db)

    # Save uploaded file to a temp path
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    # Create source document in MongoDB
    source = Source(
        _id=source_id,
        filename=file.filename,
        grade=grade,
        subject=subject,
        status="processing",
    )
    # We can store the manually specified topic if we want, but letting chunks hold it is enough
    await db.sources.insert_one(source.model_dump(by_alias=True))

    # Schedule background extraction
    background_tasks.add_task(_ingest_background, source_id, tmp_path, grade, subject, topic)

    return IngestResponse(source_id=source_id, status="processing")


@router.get("/sources")
async def get_sources(
    current_user: UserInDB = Depends(get_current_teacher),
):
    """Get all uploaded sources."""
    db = get_database()
    cursor = db.sources.find().sort("uploaded_at", -1)
    sources = await cursor.to_list(length=100)
    for s in sources:
        s["source_id"] = s.pop("_id", s.get("id", ""))
    return sources


@router.get("/ingest/{source_id}/status")
async def get_ingest_status(
    source_id: str,
    current_user: UserInDB = Depends(get_current_teacher),
):
    """Check the status of a PDF ingestion."""
    db = get_database()
    source = await db.sources.find_one({"_id": source_id})

    if not source:
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found")

    return {
        "source_id": source["_id"],
        "status": source["status"],
        "filename": source["filename"],
        "chunk_count": source.get("chunk_count", 0),
    }

async def _generate_quiz_background(source_id: str, chunk_ids: list[str] | None):
    """Background task: generate questions for a source."""
    db = get_database()
    try:
        count = await generate_questions_for_source(db, source_id, chunk_ids)
        logger.info(f"Quiz generation completed for {source_id}: {count} questions")
    except Exception as e:
        logger.error(f"Quiz generation failed for {source_id}: {e}")
        await db.sources.update_one(
            {"_id": source_id},
            {"$set": {"status": "failed"}},
        )

@router.post("/generate-quiz", response_model=GenerateQuizResponse)
async def generate_quiz(
    request: GenerateQuizRequest,
    background_tasks: BackgroundTasks,
    current_user: UserInDB = Depends(get_current_teacher),
):
    """Start question generation for all chunks of a source.

    The source must have status 'completed' (ingestion finished).
    """
    db = get_database()

    source = await db.sources.find_one({"_id": request.source_id})
    if not source:
        raise HTTPException(
            status_code=404, detail=f"Source {request.source_id} not found"
        )
    if source["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Source {request.source_id} is still '{source['status']}'. "
            f"Wait for ingestion to complete.",
        )

    background_tasks.add_task(
        _generate_quiz_background, request.source_id, request.chunk_ids
    )

    return GenerateQuizResponse(
        status="generating", source_id=request.source_id
    )
