"""
routes/chat.py
===============
Q&A endpoint — the core of the RAG pipeline.

POST /api/chat/ask
  → validate request
  → LLMService.ask() [retrieval + generation]
  → return ChatResponse with answer + sources
"""

import logging

from fastapi import APIRouter, HTTPException, status

from models.schemas import ChatRequest, ChatResponse
from services.llm_service import LLMService

logger = logging.getLogger(__name__)
router = APIRouter()

# Lazy singleton
_llm_service: LLMService | None = None


def get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service


@router.post(
    "/ask",
    response_model=ChatResponse,
    summary="Ask a question about uploaded documents",
    description=(
        "Send a question (optionally with conversation history and doc filters). "
        "The RAG pipeline retrieves relevant chunks and generates a grounded answer."
    ),
)
async def ask_question(request: ChatRequest):
    """
    Main chat endpoint.

    Accepts a question + optional chat history + optional doc_id filter.
    Returns LLM-generated answer + source chunks used.
    """
    logger.info(
        f"Chat request | question='{request.question[:80]}…' "
        f"| doc_ids={request.doc_ids} | top_k={request.top_k}"
    )

    try:
        svc = get_llm_service()
        response = await svc.ask(
            question=request.question,
            doc_ids=request.doc_ids if request.doc_ids else None,
            history=request.history,
            top_k=request.top_k,
        )
    except EnvironmentError as e:
        # Missing API key
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except Exception as e:
        logger.exception("Error during chat request")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while generating the answer. Please try again.",
        )

    return response
