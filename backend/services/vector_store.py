"""
services/vector_store.py
=========================
Wraps ChromaDB for storing and querying document embeddings.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional
from chromadb import Documents, EmbeddingFunction, Embeddings
from chromadb.api.types import Metadata

import chromadb

from services.embedding_service import EmbeddingService
from services.document_processor import TextChunk

# pyright : reportArgumentType = false

logger = logging.getLogger(__name__)

COLLECTION_NAME = "documind_chunks"


class VectorStore:

    def __init__(self, persist_dir: Optional[str] = None):
        self._persist_dir = persist_dir or os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
        self._embedding_svc = EmbeddingService()

        # FIX 1: newer chromadb removed Settings import — use just PersistentClient
        self._client = chromadb.PersistentClient(path=self._persist_dir)

        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

        logger.info(
            f"ChromaDB ready at '{self._persist_dir}' "
            f"| collection '{COLLECTION_NAME}' "
            f"| {self._collection.count()} existing chunks"
        )

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def add_document(
        self,
        doc_id: str,
        filename: str,
        chunks: List[TextChunk],
    ) -> int:

        if not chunks:
            logger.warning(f"No chunks to add for doc_id={doc_id}")
            return 0

        texts: List[str] = [chunk.content for chunk in chunks]

        # FIX 2: embed_texts returns List[List[float]] — cast explicitly
        embeddings: List[List[float]] = self._embedding_svc.embed_texts(texts)

        ids: List[str] = []
        metadatas: List[Metadata] = []

        for chunk in chunks:
            chunk_id = f"{doc_id}_{chunk.chunk_index}"
            ids.append(chunk_id)
            metadatas.append(
                {
                    "doc_id":       doc_id,
                    "filename":     filename,
                    "chunk_index":  chunk.chunk_index,
                    # FIX 3: page_number can be None — store as -1 (ChromaDB
                    # metadata values must be str, int, float, or bool — not None)
                    "page_number":  chunk.page_number if chunk.page_number is not None else -1,
                }
            )

        self._collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings,  # type: ignore[arg-type]
            metadatas=metadatas,
        )

        logger.info(f"Stored {len(chunks)} chunks for doc_id={doc_id} ({filename})")
        return len(chunks)

    def delete_document(self, doc_id: str) -> int:

        results = self._collection.get(where={"doc_id": doc_id})
        ids_to_delete: List[str] = results["ids"]

        if ids_to_delete:
            self._collection.delete(ids=ids_to_delete)
            logger.info(f"Deleted {len(ids_to_delete)} chunks for doc_id={doc_id}")

        return len(ids_to_delete)

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def similarity_search(
        self,
        query: str,
        top_k: int = 4,
        doc_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:

        # FIX 4: embed_query returns List[float] — wrap in list for ChromaDB
        query_embedding: List[float] = self._embedding_svc.embed_query(query)

        where_filter: Optional[Dict[str, Any]] = None
        if doc_ids:
            if len(doc_ids) == 1:
                where_filter = {"doc_id": doc_ids[0]}
            else:
                where_filter = {"doc_id": {"$in": doc_ids}}

        # FIX 5: collection.count() can return 0 — guard against n_results=0
        total_chunks = self._collection.count()
        if total_chunks == 0:
            return []

        n_results = min(top_k, total_chunks)

        query_kwargs: Dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results":        n_results,
            "include":          ["documents", "metadatas", "distances"], # type: ignore[list-item]
        }
        if where_filter:
            query_kwargs["where"] = where_filter

        raw = self._collection.query(**query_kwargs)

        results: List[Dict[str, Any]] = []

        # FIX 6: guard against empty results
        if not raw["ids"] or not raw["ids"][0]:
            return []

        for i, chunk_id in enumerate(raw["ids"][0]):
            distance: float = raw["distances"][0][i]  # type: ignore[index]
            # Convert cosine distance (0=identical) → similarity score (0–1)
            similarity_score = max(0.0, 1.0 - distance / 2.0)
            meta: Dict[str, Any] = raw["metadatas"][0][i]  # type: ignore[index]

            # FIX 7: convert -1 back to None for page_number
            raw_page = meta.get("page_number")
            page_number = None if raw_page == -1 else raw_page

            results.append(
                {
                    "chunk_id":    chunk_id,
                    "doc_id":      meta["doc_id"],
                    "filename":    meta["filename"],
                    "page_content": raw["documents"][0][i],  # type: ignore[index]
                    "score":       round(similarity_score, 4),
                    "page_number": page_number,
                }
            )

        results.sort(key=lambda x: x["score"], reverse=True)
        return results

    def get_all_doc_ids(self) -> List[str]:
        if self._collection.count() == 0:
            return []
        all_meta = self._collection.get(
            include=["metadatas"] # type: ignore[list-item]
        )["metadatas"]  or []
        return list({str(m["doc_id"]) for m in all_meta})

    def chunk_count(self) -> int:
        return self._collection.count()