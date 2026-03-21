"""
services/llm_service.py
========================
Orchestrates the full RAG pipeline:
  1. Retrieve relevant chunks from ChromaDB
  2. Build a grounded prompt (retrieved context + conversation history)
  3. Call Groq LLM via LangChain
  4. Return the answer + source chunks for display

Why Groq?
  - Completely free tier (generous rate limits)
  - Extremely fast inference via custom LPU hardware
  - Supports Llama 3, Mixtral, Gemma — all powerful open models
  - Drop-in replacement for OpenAI client
"""

from __future__ import annotations

import logging
import os
from typing import Dict, List, Optional, Any

from langchain_groq import ChatGroq
from langchain.schema import HumanMessage, SystemMessage, AIMessage

from services.vector_store import VectorStore
from models.schemas import ChatMessage, ChatResponse, SourceChunk

logger = logging.getLogger(__name__)

# Default Groq model — llama-3.1-70b-versatile gives the best quality/speed ratio
DEFAULT_MODEL = "llama-3.1-70b-versatile"

# System prompt that instructs the LLM to stay grounded in retrieved context
SYSTEM_PROMPT = """You are DocuMind, an expert document analyst AI assistant.

Your job is to answer user questions **based only on the provided document context**.

Rules:
1. Answer ONLY from the context provided below. Do NOT use outside knowledge.
2. If the context does not contain enough information, say: "I couldn't find enough information in the uploaded documents to answer this."
3. Always be concise, accurate, and cite the relevant part of the context in your answer.
4. If multiple documents are provided, distinguish which document each piece of information comes from.
5. Format your answer clearly with markdown when helpful (bullet points, bold key terms, etc.).

Context from retrieved document chunks:
{context}
"""


class LLMService:
    """
    High-level RAG service.

    Exposes a single `ask()` method that orchestrates retrieval + generation.
    """

    def __init__(self):
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise EnvironmentError(
                "GROQ_API_KEY is not set. "
                "Get a free key at https://console.groq.com"
            )

        model_name = os.getenv("GROQ_MODEL", DEFAULT_MODEL)

        # Initialise the Groq LLM via LangChain
        self._llm = ChatGroq(
            api_key=groq_api_key,
            model_name=model_name,
            temperature=0.1,        # low temperature for factual Q&A
            max_tokens=2048,        # generous output limit
            timeout=30,             # seconds before giving up
        )

        self._vector_store = VectorStore()
        self._model_name = model_name
        logger.info(f"LLMService initialised with model: {model_name}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def ask(
        self,
        question: str,
        doc_ids: Optional[List[str]] = None,
        history: Optional[List[ChatMessage]] = None,
        top_k: int = 4,
    ) -> ChatResponse:
        """
        Full RAG pipeline: retrieve → augment → generate.

        Args:
            question: User's natural language question.
            doc_ids:  Optional list of doc_ids to restrict retrieval to.
            history:  Previous conversation turns for multi-turn context.
            top_k:    How many document chunks to retrieve.

        Returns:
            ChatResponse with answer text + source chunks.
        """
        # ----------------------------------------------------------
        # Step 1: Retrieve relevant chunks from ChromaDB
        # ----------------------------------------------------------
        raw_results = self._vector_store.similarity_search(
            query=question,
            top_k=top_k,
            doc_ids=doc_ids if doc_ids else None,
        )

        if not raw_results:
            return ChatResponse(
                answer=(
                    "No documents have been uploaded yet, or the query returned no results. "
                    "Please upload a document first."
                ),
                sources=[],
                model_used=self._model_name,
            )

        # ----------------------------------------------------------
        # Step 2: Build context string from retrieved chunks
        # ----------------------------------------------------------
        context_parts: List[str] = []
        for i, result in enumerate(raw_results, start=1):
            page_info = (
                f" (page {result['page_number']})"
                if result.get("page_number") and result["page_number"] != -1
                else ""
            )
            context_parts.append(
                f"[Source {i} — {result['filename']}{page_info}]\n"
                f"{result['page_content']}"
            )

        context_str = "\n\n---\n\n".join(context_parts)

        # ----------------------------------------------------------
        # Step 3: Build the message list for the LLM
        # ----------------------------------------------------------
        messages = [
            SystemMessage(content=SYSTEM_PROMPT.format(context=context_str))
        ]

        # Inject previous conversation turns for multi-turn support
        if history:
            for turn in history[-6:]:  # keep last 6 turns to manage token budget
                if turn.role == "user":
                    messages.append(HumanMessage(content=turn.content))
                elif turn.role == "assistant":
                    messages.append(AIMessage(content=turn.content))

        # Append the current user question
        messages.append(HumanMessage(content=question))

        # ----------------------------------------------------------
        # Step 4: Call the Groq LLM
        # ----------------------------------------------------------
        logger.info(
            f"Calling Groq ({self._model_name}) | chunks={len(raw_results)} | "
            f"history_turns={len(history or [])}"
        )

        response = await self._llm.ainvoke(messages)
        answer_text = response.content

        # ----------------------------------------------------------
        # Step 5: Build SourceChunk objects for source highlighting
        # ----------------------------------------------------------
        sources = [
            SourceChunk(
                chunk_id=r["chunk_id"],
                doc_id=r["doc_id"],
                filename=r["filename"],
                page_content=r["page_content"],
                score=r["score"],
                page_number=r.get("page_number"),
            )
            for r in raw_results
        ]

        # Extract token usage if available
        tokens_used = None
        if hasattr(response, "response_metadata"):
            usage = response.response_metadata.get("token_usage", {})
            tokens_used = usage.get("total_tokens")

        return ChatResponse(
            answer=answer_text,
            sources=sources,
            model_used=self._model_name,
            tokens_used=tokens_used,
        )
