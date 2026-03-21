"""
routes/documents.py
====================
CRUD operations for the document registry.

GET    /api/documents        → list all documents
GET    /api/documents/{id}   → get single document metadata
DELETE /api/documents/{id}   → delete document + its embeddings
"""

import logging
from typing import List

from fastapi import APIRouter, HTTPException, status

from models.schemas import DocumentListResponse, DocumentMeta
from services.vector_store import VectorStore
from utils.doc_registry import delete_document, get_document, list_documents

logger = logging.getLogger(__name__)
router = APIRouter()

_vector_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store


@router.get(
    "/",
    response_model=DocumentListResponse,
    summary="List all ingested documents",
)
async def list_all_documents():
    """Return metadata for every document that has been uploaded."""
    docs = list_documents()
    return DocumentListResponse(
        documents=[DocumentMeta(**d) for d in docs],
        total=len(docs),
    )


@router.get(
    "/{doc_id}",
    response_model=DocumentMeta,
    summary="Get metadata for a single document",
)
async def get_single_document(doc_id: str):
    """Retrieve metadata for a specific document by its ID."""
    doc = get_document(doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{doc_id}' not found.",
        )
    return DocumentMeta(**doc)


@router.delete(
    "/{doc_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a document and its embeddings",
)
async def delete_single_document(doc_id: str):
    """
    Remove a document from:
      1. The JSON registry (metadata)
      2. ChromaDB (all embedding chunks)
    """
    # Verify it exists first
    if not get_document(doc_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{doc_id}' not found.",
        )

    # Delete from ChromaDB
    vs = get_vector_store()
    deleted_chunks = vs.delete_document(doc_id)

    # Delete from registry
    delete_document(doc_id)

    logger.info(f"Deleted doc_id={doc_id} | {deleted_chunks} chunks removed")

    return {
        "message": f"Document deleted successfully.",
        "doc_id": doc_id,
        "chunks_deleted": deleted_chunks,
    }
