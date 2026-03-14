"""Sentence-transformers embedding service.

Uses all-MiniLM-L6-v2 (384-dim, ~22MB download on first run).
Model is loaded lazily and cached globally.
"""

from sentence_transformers import SentenceTransformer

_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    """Get or load the embedding model (lazy singleton)."""
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def embed(text: str) -> list[float]:
    """Embed a single text string. Returns a 384-dim normalized vector."""
    return get_model().encode(text, normalize_embeddings=True).tolist()


def embed_batch(texts: list[str]) -> list[list[float]]:
    """Embed a batch of text strings. Returns list of 384-dim normalized vectors."""
    return (
        get_model()
        .encode(texts, normalize_embeddings=True, batch_size=32)
        .tolist()
    )
