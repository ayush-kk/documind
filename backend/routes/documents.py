
import logging
from typing import List

from fastapi import APIRouter, HTTPException, status
from models.schemas import DocumentListResponse, DocumentMeta

logger = logging.getLogger(__name__)
router = APIRouter()

_vector_store = None


def get_vector_store():
    global _vector_store
    if _vector_store is None:
        from services.vector_store import VectorStore
        _vector_store = VectorStore()
    return _vector_store


@router.get(
    "/",
    response_model=DocumentListResponse,
    summary="List all ingested documents",
)
async def list_all_documents():
    from utils.doc_registry import list_documents
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
    from utils.doc_registry import get_document
    doc = get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document '{doc_id}' not found.")
    return DocumentMeta(**doc)


@router.delete(
    "/{doc_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a document and its embeddings",
)
async def delete_single_document(doc_id: str):
    from utils.doc_registry import get_document, delete_document

    if not get_document(doc_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document '{doc_id}' not found.")

    vs             = get_vector_store()
    deleted_chunks = vs.delete_document(doc_id)

    delete_document(doc_id)

    logger.info(f"Deleted doc_id={doc_id} | {deleted_chunks} chunks removed")

    return {
        "message": "Document deleted successfully.",
        "doc_id": doc_id,
        "chunks_deleted": deleted_chunks,
    }