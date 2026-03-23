"""
services/embedding_service.py
==============================
Generates vector embeddings using a locally-run HuggingFace sentence-transformer.
Model: all-MiniLM-L6-v2 — 384-dim, ~22MB, free, runs on CPU.
"""
from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import List, Optional

logger = logging.getLogger(__name__)

DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class EmbeddingService:
    """
    Wraps HuggingFaceEmbeddings with LAZY loading.
    Model is NOT downloaded on __init__ — only on first embed call.
    This prevents Render port-scan timeout on startup.
    """

    def __init__(self, model_name: Optional[str] = None):
        # FIX: store model name only — do NOT load model here
        self._model_name = model_name or os.getenv(
            "EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL
        )
        self._model = None  # loaded lazily on first use
        logger.debug(f"EmbeddingService created (model not loaded yet): {self._model_name}")

    def _get_or_load_model(self):
        """Load model on first call — cached at module level after that."""
        if self._model is None:
            self._model = _load_model(self._model_name)
        return self._model

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of text strings."""
        if not texts:
            return []
        model = self._get_or_load_model()
        embeddings = model.embed_documents(texts)
        logger.debug(f"Embedded {len(texts)} text(s) → dim={len(embeddings[0])}")
        return embeddings

    def embed_query(self, query: str) -> List[float]:
        """Embed a single query string."""
        model = self._get_or_load_model()
        embedding = model.embed_query(query)
        logger.debug(f"Embedded query → dim={len(embedding)}")
        return embedding


@lru_cache(maxsize=4)
def _load_model(model_name: str):
    """
    Load HuggingFace model — cached at process level via lru_cache.
    Runs only once per model name no matter how many times it's called.
    """
    # Import here so it does NOT run at module import time
    from langchain_community.embeddings import HuggingFaceEmbeddings

    logger.info(f"Loading embedding model '{model_name}' (downloading if needed)...")
    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )