"""Ingestion service entry point. Handles PDF upload and question generation."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import close_client, create_indexes
from app.routes import ingest
from app.services.embeddings import get_model
from app.vector_store import get_qdrant_client, init_collections

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Ingestion service starting")
    logger.info("Loading embedding model...")
    get_model()
    logger.info("Embedding model loaded")

    try:
        client = get_qdrant_client()
        init_collections(client)
        logger.info("Qdrant collections initialized")
    except Exception as e:
        logger.warning(f"Qdrant init failed (will retry on demand): {e}")

    await create_indexes()
    logger.info("MongoDB indexes created")

    yield
    await close_client()
    logger.info("Ingestion service stopped")


app = FastAPI(title="Peblo Ingestion Service", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ingestion"}
