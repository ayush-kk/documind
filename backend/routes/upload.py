
import logging
import uuid
from typing import List, TYPE_CHECKING

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from models.schemas import UploadResponse

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_FILE_SIZE_MB    = 20
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_EXTENSIONS  = {".pdf", ".docx", ".txt"}

_processor    = None
_vector_store = None


def get_processor():
    global _processor
    if _processor is None:
        from services.document_processor import DocumentProcessor
        _processor = DocumentProcessor()
    return _processor


def get_vector_store():
    global _vector_store
    if _vector_store is None:
        from services.vector_store import VectorStore
        _vector_store = VectorStore()
    return _vector_store


@router.post(
    "/",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and ingest a document",
)
async def upload_document(file: UploadFile = File(...)):

    from utils.doc_registry import register_document

    filename  = file.filename or "unknown"
    extension = ("." + filename.rsplit(".", 1)[-1].lower()) if "." in filename else ""

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type '{extension}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    file_bytes = await file.read()
    size_bytes = len(file_bytes)

    if size_bytes == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    if size_bytes > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE_MB} MB.",
        )

    logger.info(f"Upload received: '{filename}' ({size_bytes / 1024:.1f} KB)")

    try:
        processor = get_processor()
        chunks    = processor.process(file_bytes, filename)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception:
        logger.exception(f"Unexpected error processing '{filename}'")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Document processing failed.")

    doc_id = str(uuid.uuid4())

    try:
        vector_store = get_vector_store()
        num_stored   = vector_store.add_document(doc_id, filename, chunks)
    except Exception:
        logger.exception(f"Failed to store chunks for '{filename}'")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to store document embeddings.")

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

    logger.info(f"Upload complete: doc_id={doc_id} | chunks={num_stored}")

    return UploadResponse(doc_id=doc_id, filename=filename, num_chunks=num_stored)


@router.post(
    "/batch",
    response_model=List[UploadResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Upload multiple documents at once",
)
async def upload_documents_batch(files: List[UploadFile] = File(...)):
    if len(files) > 5:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Maximum 5 files per batch upload.")
    results = []
    for file in files:
        result = await upload_document(file)
        results.append(result)
    return results