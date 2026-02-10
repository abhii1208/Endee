from functools import lru_cache
from typing import List

from loguru import logger
from sentence_transformers import SentenceTransformer

from backend.app.config import get_settings


@lru_cache()
def get_embedding_model() -> SentenceTransformer:
    """
    Load and cache the embedding model.

    Using a process-wide cache avoids re-loading the model for every request
    and keeps latency predictable.
    """

    settings = get_settings()
    model_name = settings.embedding_model_name
    logger.info(f"Loading embedding model: {model_name}")
    try:
        model = SentenceTransformer(model_name)
    except Exception as exc:
        logger.exception(f"Failed to load embedding model {model_name}: {exc}")
        raise
    return model


def embed_text(text: str) -> List[float]:
    """
    Embed a single text string into a dense vector.
    """

    model = get_embedding_model()
    vector = model.encode(text, convert_to_numpy=True)
    return vector.astype(float).tolist()


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Embed a batch of texts into dense vectors.
    """

    if not texts:
        return []
    model = get_embedding_model()
    vectors = model.encode(texts, convert_to_numpy=True)
    return [v.astype(float).tolist() for v in vectors]

