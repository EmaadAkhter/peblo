"""PDF text extraction with intelligent chunking and topic detection.

Chunking strategy (per spec):
1. Extract text page by page with pdfplumber.
2. Split by double newline into paragraphs.
3. Merge short paragraphs (< 100 chars) with the next.
4. If a chunk exceeds 600 chars, split at nearest sentence boundary
   with last-sentence overlap.
5. Strip headers, page numbers, and purely numeric lines.
"""

import logging
import re
import tempfile

import pdfplumber
from groq import Groq
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config import groq_key_rotator
from app.models.source import Chunk
from app.services.embeddings import embed
from app.services.similarity import (
    check_chunk_duplicate_safe,
    store_chunk_vector_safe,
)
from app.utils.id_generator import generate_chunk_id
from app.vector_store import get_qdrant_client

logger = logging.getLogger(__name__)

# Regex to strip headers, page numbers, purely numeric lines
_NOISE_RE = re.compile(
    r"^\s*(?:page\s*\d+|\d+\s*$|chapter\s+\d+|table\s+of\s+contents)\s*$",
    re.IGNORECASE | re.MULTILINE,
)
_NUMERIC_LINE_RE = re.compile(r"^\s*\d+\s*$", re.MULTILINE)


def _clean_text(text: str) -> str:
    """Remove headers, page numbers, and purely numeric lines."""
    text = _NOISE_RE.sub("", text)
    text = _NUMERIC_LINE_RE.sub("", text)
    return text.strip()


def _split_into_paragraphs(text: str) -> list[str]:
    """Split text by double newline into paragraphs."""
    paragraphs = re.split(r"\n\s*\n", text)
    return [p.strip() for p in paragraphs if p.strip()]


def _merge_short_paragraphs(paragraphs: list[str], min_length: int = 100) -> list[str]:
    """Merge consecutive short paragraphs with the next one."""
    if not paragraphs:
        return []

    merged = []
    buffer = ""

    for para in paragraphs:
        if buffer:
            buffer = buffer + "\n\n" + para
        else:
            buffer = para

        if len(buffer) >= min_length:
            merged.append(buffer)
            buffer = ""

    # Don't lose trailing buffer
    if buffer:
        if merged:
            merged[-1] = merged[-1] + "\n\n" + buffer
        else:
            merged.append(buffer)

    return merged


def _find_sentence_boundary(text: str) -> int:
    """Find the last sentence boundary (. ! ?) in the text.

    Returns the index after the sentence-ending punctuation, or -1 if none found.
    """
    matches = list(re.finditer(r"[.!?]\s", text))
    if matches:
        return matches[-1].end()
    return -1


def _split_long_chunks(chunks: list[str], max_length: int = 1500) -> list[str]:
    """Split chunks exceeding max_length at sentence boundaries with overlap."""
    result = []

    for chunk in chunks:
        if len(chunk) <= max_length:
            result.append(chunk)
            continue

        # Split at sentence boundary
        remaining = chunk
        while len(remaining) > max_length:
            # Find sentence boundary within the max_length window
            boundary = _find_sentence_boundary(remaining[:max_length])
            if boundary == -1:
                # No sentence boundary found — force split at max_length
                boundary = max_length

            current_chunk = remaining[:boundary].strip()
            if current_chunk:
                result.append(current_chunk)

            # Find the last sentence of the current chunk for overlap
            last_sentence_match = re.search(r"[^.!?]*[.!?]\s*$", current_chunk)
            overlap = ""
            if last_sentence_match:
                overlap = last_sentence_match.group().strip() + " "

            remaining = overlap + remaining[boundary:].strip()

        if remaining.strip():
            result.append(remaining.strip())

    return result


def extract_text_from_pdf(file_path: str) -> list[str]:
    """Extract and chunk text from a PDF file.

    Returns a list of clean text chunks.
    """
    all_chunks = []

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            text = _clean_text(text)
            if not text:
                continue

            paragraphs = _split_into_paragraphs(text)
            merged = _merge_short_paragraphs(paragraphs)
            chunks = _split_long_chunks(merged)
            all_chunks.extend(chunks)

    return [c for c in all_chunks if c.strip()]


from groq import AsyncGroq

async def detect_topic(chunk_text: str, subject: str = "") -> str:
    """Use Groq to detect a 1-3 word topic label for a chunk."""
    try:
        client = AsyncGroq(api_key=next(groq_key_rotator))
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a topic classifier. Given a text chunk, you MUST extract a 1-3 word topic representing its core focus. "
                        "Respond with ONLY the exact topic string. No explanation, no punctuation."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Subject: {subject}\n\nText:\n{chunk_text[:500]}",
                },
            ],
            temperature=0,
            max_tokens=20,
        )
        topic = response.choices[0].message.content.strip()
        # Clean up — remove any quotes or extra punctuation
        topic = re.sub(r'^["\']|["\']$', "", topic).strip()
        
        return topic.title() if topic else "General"
    except Exception as e:
        logger.warning(f"Topic detection failed: {e}")
        return "General"


async def process_pdf(
    db: AsyncIOMotorDatabase,
    source_id: str,
    file_path: str,
    grade: int,
    subject: str,
    topic: str | None = None,
) -> int:
    """Extract, chunk, deduplicate, and store chunks from a PDF.

    Returns the number of chunks stored.
    """
    # Extract text chunks
    raw_chunks = extract_text_from_pdf(file_path)
    logger.info(f"Extracted {len(raw_chunks)} raw chunks from {file_path}")

    if not raw_chunks:
        logger.warning(f"No text extracted from {file_path}")
        return 0

    # Get Qdrant client (may be None if unavailable)
    try:
        qdrant = get_qdrant_client()
    except Exception as e:
        logger.warning(f"Qdrant unavailable, skipping vector dedup: {e}")
        qdrant = None

    stored_count = 0

    enforced_topic = topic.title() if topic else None

    for idx, chunk_text in enumerate(raw_chunks):
        chunk_id = generate_chunk_id(source_id, idx)

        # Embed the chunk for dedup check
        try:
            vector = embed(chunk_text)
        except Exception as e:
            logger.warning(f"Embedding failed for chunk {chunk_id}: {e}")
            vector = None

        # Check for duplicate chunk from another source
        if vector and check_chunk_duplicate_safe(qdrant, vector, source_id):
            logger.info(f"Skipping duplicate chunk {chunk_id}")
            continue

        # Detect topic
        chunk_topic = enforced_topic or await detect_topic(chunk_text, subject)

        # Create chunk model
        chunk = Chunk(
            _id=chunk_id,
            source_id=source_id,
            grade=grade,
            subject=subject,
            topic=chunk_topic,
            text=chunk_text,
            chunk_index=idx,
        )

        # Store in MongoDB
        from pymongo.errors import DuplicateKeyError as ChunkDupError
        try:
            await db.chunks.insert_one(chunk.model_dump(by_alias=True))
        except ChunkDupError:
            logger.info(f"Chunk {chunk_id} already exists in MongoDB, skipping")
            continue

        # Store vector in Qdrant
        if vector:
            store_chunk_vector_safe(
                qdrant,
                chunk_id,
                vector,
                {
                    "chunk_id": chunk_id,
                    "source_id": source_id,
                    "topic": chunk_topic,
                    "subject": subject,
                    "grade": grade,
                },
            )

        stored_count += 1

    return stored_count
