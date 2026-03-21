"""
models/schemas.py
=================
Pydantic v2 schemas used across request bodies and API responses.
Keeping schemas in one place makes it easy to version the API contract.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Document schemas
# ---------------------------------------------------------------------------

class DocumentMeta(BaseModel):
    """Metadata stored alongside each ingested document."""

    doc_id: str = Field(..., description="Unique document identifier (UUID4 as str)")
    filename: str = Field(..., description="Original filename as uploaded by the user")
    file_type: str = Field(..., description="MIME type, e.g. application/pdf")
    num_chunks: int = Field(..., description="Number of text chunks stored in ChromaDB")
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    size_bytes: int = Field(..., description="Raw file size in bytes")


class DocumentListResponse(BaseModel):
    """Response envelope for the document listing endpoint."""

    documents: List[DocumentMeta]
    total: int


class UploadResponse(BaseModel):
    """Returned after a successful document upload & ingestion."""

    doc_id: str
    filename: str
    num_chunks: int
    message: str = "Document ingested successfully"


# ---------------------------------------------------------------------------
# Chat / Q&A schemas
# ---------------------------------------------------------------------------

class SourceChunk(BaseModel):
    """
    A single retrieved document chunk shown to the user as a source reference.
    Enables 'source highlighting' in the frontend.
    """

    chunk_id: str = Field(..., description="ChromaDB document ID for this chunk")
    doc_id: str = Field(..., description="Parent document identifier")
    filename: str
    page_content: str = Field(..., description="The raw text of this chunk")
    score: float = Field(..., description="Cosine similarity score (0–1, higher = more relevant)")
    page_number: Optional[int] = Field(None, description="Page number if available (PDF only)")


class ChatMessage(BaseModel):
    """A single turn in the conversation history."""

    role: str = Field(..., pattern="^(user|assistant)$")
    content: str


class ChatRequest(BaseModel):
    """
    Request body for the /api/chat/ask endpoint.

    doc_ids: if provided, restricts retrieval to those documents.
             If empty, searches across all ingested documents.
    history:  previous turns for multi-turn conversation context.
    """

    question: str = Field(..., min_length=1, max_length=2000)
    doc_ids: List[str] = Field(default_factory=list)
    history: List[ChatMessage] = Field(default_factory=list)
    top_k: int = Field(default=4, ge=1, le=10, description="Number of chunks to retrieve")


class ChatResponse(BaseModel):
    """Full response envelope returned by the RAG pipeline."""

    answer: str = Field(..., description="LLM-generated answer grounded in retrieved chunks")
    sources: List[SourceChunk] = Field(..., description="Chunks used to generate the answer")
    model_used: str = Field(..., description="Groq model identifier")
    tokens_used: Optional[int] = None


# ---------------------------------------------------------------------------
# Error schema
# ---------------------------------------------------------------------------

class ErrorResponse(BaseModel):
    """Standard error envelope."""

    detail: str
    error_code: Optional[str] = None
