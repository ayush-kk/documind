"""
services/embedding_service.py
==============================
Generates vector embeddings using a locally-run HuggingFace sentence-transformer.

Model choice: 'all-MiniLM-L6-v2'
  - 384-dimensional embeddings
  - ~22 MB model size (downloads once, then cached)
  - Fast inference, excellent retrieval quality for Q&A workloads
  - Completely FREE — runs on CPU, no API call needed

This keeps embedding costs at exactly $0.
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import List

from langchain_community.embeddings import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)

# Model to use — can be overridden via environment variable
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class EmbeddingService:
    """
    Wraps LangChain's HuggingFaceEmbeddings to provide:
      - Lazy model loading (model downloads only on first use)
      - Batch embedding for efficiency
      - Single-query embedding for search

    This is a lightweight class; it's safe to instantiate per-request.
    The underlying model is cached at the process level via lru_cache.
    """

    def __init__(self, model_name: Optional[str] = None):
        model = model_name or os.getenv("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)
        # _get_model is module-level cached → model loads only once per process
        self._model = _get_model(model)
        logger.debug(f"EmbeddingService using model: {model}")

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a batch of text strings.

        Args:
            texts: List of strings to embed.

        Returns:
            List of embedding vectors (each a list of floats).
        """
        if not texts:
            return []
        embeddings = self._model.embed_documents(texts)
        logger.debug(f"Embedded {len(texts)} text(s) → dim={len(embeddings[0])}")
        return embeddings

    def embed_query(self, query: str) -> List[float]:
        """
        Embed a single query string.
        LangChain uses a different internal method for queries vs documents
        (some models apply asymmetric encoding for better retrieval).

        Args:
            query: The user's question string.

        Returns:
            Single embedding vector.
        """
        embedding = self._model.embed_query(query)
        logger.debug(f"Embedded query → dim={len(embedding)}")
        return embedding


# ---------------------------------------------------------------------------
# Module-level cached model loader
# ---------------------------------------------------------------------------

@lru_cache(maxsize=4)  # cache up to 4 different models across hot-reloads
def _get_model(model_name: str) -> HuggingFaceEmbeddings:
    """
    Load (or retrieve from cache) a HuggingFace embedding model.

    The @lru_cache decorator ensures this expensive operation runs only once
    per model name per process lifetime — critical for a web server.
    """
    logger.info(f"Loading embedding model '{model_name}' … (first run may download ~22 MB)")
    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={"device": "cpu"},   # switch to 'cuda' if GPU available
        encode_kwargs={"normalize_embeddings": True},  # normalise for cosine similarity
    )


# Fix missing Optional import
from typing import Optional
