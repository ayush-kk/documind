"""
services/embedding_service.py
==============================
Uses ChromaDB's built-in ONNX embedding function.
No torch. No sentence-transformers. Fast startup.
"""
from __future__ import annotations

import logging
from typing import List

logger = logging.getLogger(__name__)

_embedding_fn = None


def _get_embedding_fn():
    global _embedding_fn
    if _embedding_fn is None:
        from chromadb.utils.embedding_functions.onnx_mini_lm_l6_v2 import ONNXMiniLM_L6_V2
        _embedding_fn = ONNXMiniLM_L6_V2()
        logger.info("ONNX embedding function loaded")
    return _embedding_fn


class EmbeddingService:

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        fn = _get_embedding_fn()
        # ChromaDB embedding functions accept a list and return a list
        result = fn(texts)
        return [list(map(float, e)) for e in result]

    def embed_query(self, query: str) -> List[float]:
        fn = _get_embedding_fn()
        result = fn([query])
        return list(map(float, result[0]))