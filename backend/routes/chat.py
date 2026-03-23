
import logging

from fastapi import APIRouter, HTTPException, status
from models.schemas import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)
router = APIRouter()

_llm_service = None


def get_llm_service():
    global _llm_service
    if _llm_service is None:
        from services.llm_service import LLMService
        _llm_service = LLMService()
    return _llm_service


@router.post(
    "/ask",
    response_model=ChatResponse,
    summary="Ask a question about uploaded documents",
)
async def ask_question(request: ChatRequest):

    logger.info(f"Chat request | question='{request.question[:80]}' | doc_ids={request.doc_ids}")

    try:
        svc      = get_llm_service()
        response = await svc.ask(
            question=request.question,
            doc_ids=request.doc_ids if request.doc_ids else None,
            history=request.history,
            top_k=request.top_k,
        )
    except EnvironmentError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception:
        logger.exception("Error during chat request")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while generating the answer.")

    return response