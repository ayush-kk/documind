"""
routes/upload.py
=================
Handles document upload, processing, embedding, and storage.

Flow:
  POST /api/upload
    → validate file type & size
    → DocumentProcessor: extract text + chunk
    → VectorStore: embed + upsert into ChromaDB
    → doc_registry: save metadata
    → return UploadResponse
"""

import logging
import uuid
from typing import List

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from models.schemas import UploadResponse
from services.document_processor import DocumentProcessor
from services.vector_store import VectorStore
from utils.doc_registry import register_document

logger = logging.getLogger(__name__)

router = APIRouter()

# Configuration constants
MAX_FILE_SIZE_MB = 20
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
}
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}

# Lazy-initialised singletons (created once per worker process)
_processor: DocumentProcessor | None = None
_vector_store: VectorStore | None = None


def get_processor() -> DocumentProcessor:
    global _processor
    if _processor is None:
        _processor = DocumentProcessor()
    return _processor


def get_vector_store() -> VectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store


# ---------------------------------------------------------------------------
# Endpoint: upload single document
# ---------------------------------------------------------------------------

@router.post(
    "/",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and ingest a document",
    description=(
        "Upload a PDF, DOCX, or TXT file. "
        "The file is chunked, embedded, and stored in ChromaDB for Q&A."
    ),
)
async def upload_document(file: UploadFile = File(...)):
    """
    Main upload endpoint.

    Validates → extracts text → chunks → embeds → stores.
    """
    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    filename = file.filename or "unknown"
    extension = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"Unsupported file type '{extension}'. "
                f"Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            ),
        )

    # Read file bytes
    file_bytes = await file.read()
    size_bytes = len(file_bytes)

    if size_bytes == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    if size_bytes > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE_MB} MB.",
        )

    logger.info(f"Upload received: '{filename}' ({size_bytes / 1024:.1f} KB)")

    # ------------------------------------------------------------------
    # Processing
    # ------------------------------------------------------------------
    try:
        processor = get_processor()
        chunks = processor.process(file_bytes, filename)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except Exception as e:
        logger.exception(f"Unexpected error processing '{filename}'")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document processing failed. Please try again.",
        )

    # ------------------------------------------------------------------
    # Storage
    # ------------------------------------------------------------------
    doc_id = str(uuid.uuid4())

    try:
        vector_store = get_vector_store()
        num_stored = vector_store.add_document(doc_id, filename, chunks)
    except Exception as e:
        logger.exception(f"Failed to store chunks for '{filename}'")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store document embeddings. Please try again.",
        )

    # Determine MIME type for registry
    mime_map = {
        ".pdf":  "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".txt":  "text/plain",
    }

    register_document(
        doc_id=doc_id,
        filename=filename,
        file_type=mime_map.get(extension, "unknown"),
        num_chunks=num_stored,
        size_bytes=size_bytes,
    )

    logger.info(f"✅ Upload complete: doc_id={doc_id} | chunks={num_stored}")

    return UploadResponse(
        doc_id=doc_id,
        filename=filename,
        num_chunks=num_stored,
    )


# ---------------------------------------------------------------------------
# Endpoint: batch upload (convenience)
# ---------------------------------------------------------------------------

@router.post(
    "/batch",
    response_model=List[UploadResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Upload multiple documents at once",
)
async def upload_documents_batch(files: List[UploadFile] = File(...)):
    """Upload up to 5 documents in a single request."""
    if len(files) > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 5 files per batch upload.",
        )

    results = []
    for file in files:
        # Reuse single-upload logic per file
        result = await upload_document(file)
        results.append(result)

    return results
