"""
services/vector_store.py
=========================
Wraps ChromaDB for storing and querying document embeddings.

ChromaDB runs fully embedded (no separate server needed) and persists
data to disk. This makes it zero-cost and trivial to deploy.

Design:
  - One ChromaDB collection per application ("documind_chunks").
  - Each chunk is stored with rich metadata for filtering and display.
  - Similarity search uses cosine distance (default for HuggingFace embeddings).
"""

from __future__ import annotations

import logging
import os
import uuid
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings

from services.embedding_service import EmbeddingService
from services.document_processor import TextChunk

logger = logging.getLogger(__name__)

# Name of the single ChromaDB collection used by this application
COLLECTION_NAME = "documind_chunks"


class VectorStore:
    """
    Singleton-style wrapper around ChromaDB.

    Usage:
        store = VectorStore()
        store.add_document(doc_id, filename, chunks)
        results = store.similarity_search(query, top_k=4)
    """

    def __init__(self, persist_dir: Optional[str] = None):
        """
        Args:
            persist_dir: Directory for ChromaDB to persist data.
                         Defaults to CHROMA_PERSIST_DIR env var or './chroma_db'.
        """
        self._persist_dir = persist_dir or os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
        self._embedding_svc = EmbeddingService()

        # Initialise ChromaDB client with disk persistence
        self._client = chromadb.PersistentClient(
            path=self._persist_dir,
            settings=Settings(anonymized_telemetry=False),
        )

        # Get-or-create the collection
        # cosine distance is best for normalised HuggingFace embeddings
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
        """
        Embed all chunks and upsert them into ChromaDB.

        Args:
            doc_id:   Unique document identifier (UUID string).
            filename: Human-readable filename for display in sources.
            chunks:   TextChunk objects produced by DocumentProcessor.

        Returns:
            Number of chunks successfully stored.
        """
        if not chunks:
            logger.warning(f"No chunks to add for doc_id={doc_id}")
            return 0

        # Extract raw text for batch embedding (one API call)
        texts = [chunk.content for chunk in chunks]
        embeddings = self._embedding_svc.embed_texts(texts)

        # Build ChromaDB inputs
        ids: List[str] = []
        metadatas: List[Dict[str, Any]] = []

        for chunk in chunks:
            chunk_id = f"{doc_id}_{chunk.chunk_index}"
            ids.append(chunk_id)
            metadatas.append(
                {
                    "doc_id": doc_id,
                    "filename": filename,
                    "chunk_index": chunk.chunk_index,
                    "page_number": chunk.page_number or -1,  # -1 = unknown
                }
            )

        # Upsert handles duplicates gracefully (re-processing same doc is safe)
        self._collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        logger.info(f"Stored {len(chunks)} chunks for doc_id={doc_id} ({filename})")
        return len(chunks)

    def delete_document(self, doc_id: str) -> int:
        """
        Remove all chunks belonging to a specific document.

        Returns:
            Number of chunks deleted.
        """
        # ChromaDB where-clause filter
        results = self._collection.get(where={"doc_id": doc_id})
        ids_to_delete = results["ids"]

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
        """
        Embed the query and retrieve the top_k most similar chunks.

        Args:
            query:   Natural language question.
            top_k:   Number of chunks to return.
            doc_ids: Optional allow-list of doc_ids to restrict search.

        Returns:
            List of dicts, each containing:
              - chunk_id, doc_id, filename, page_content, score, page_number
        """
        query_embedding = self._embedding_svc.embed_query(query)

        # Build optional where-filter for multi-document support
        where_filter = None
        if doc_ids:
            if len(doc_ids) == 1:
                where_filter = {"doc_id": doc_ids[0]}
            else:
                # ChromaDB uses MongoDB-style $in operator
                where_filter = {"doc_id": {"$in": doc_ids}}

        query_kwargs: Dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": min(top_k, self._collection.count() or 1),
            "include": ["documents", "metadatas", "distances"],
        }
        if where_filter:
            query_kwargs["where"] = where_filter

        raw = self._collection.query(**query_kwargs)

        # Flatten and normalise results
        results: List[Dict[str, Any]] = []
        for i, chunk_id in enumerate(raw["ids"][0]):
            distance = raw["distances"][0][i]
            # Convert cosine distance (0=identical, 2=opposite) → similarity (0–1)
            similarity_score = max(0.0, 1.0 - distance / 2.0)
            meta = raw["metadatas"][0][i]

            results.append(
                {
                    "chunk_id": chunk_id,
                    "doc_id": meta["doc_id"],
                    "filename": meta["filename"],
                    "page_content": raw["documents"][0][i],
                    "score": round(similarity_score, 4),
                    "page_number": meta.get("page_number") or None,
                }
            )

        # Sort by score descending (highest relevance first)
        results.sort(key=lambda x: x["score"], reverse=True)
        return results

    def get_all_doc_ids(self) -> List[str]:
        """Return a deduplicated list of all doc_ids present in the store."""
        if self._collection.count() == 0:
            return []
        all_meta = self._collection.get(include=["metadatas"])["metadatas"]
        return list({m["doc_id"] for m in all_meta})

    def chunk_count(self) -> int:
        """Total number of chunks stored."""
        return self._collection.count()
