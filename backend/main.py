"""
DocuMind — Chat with Any Document (RAG Pipeline)
================================================
Main FastAPI application entry point.

Architecture:
  Client → FastAPI → LangChain → ChromaDB (vector search)
                              → Groq LLM (answer generation)

Author: DocuMind Team
"""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ---------------------------------------------------------------------------
# Local route imports
# ---------------------------------------------------------------------------
from routes.upload import router as upload_router
from routes.chat import router as chat_router
from routes.documents import router as documents_router

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan: startup / shutdown hooks
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs once on startup and once on shutdown.
    Use this to initialise expensive resources (DB connections, model loading).
    """
    logger.info("🚀 DocuMind backend starting up …")

    # Ensure ChromaDB persistence directory exists
    chroma_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    os.makedirs(chroma_dir, exist_ok=True)
    logger.info(f"✅ ChromaDB persistence directory ready at: {chroma_dir}")

    yield  # <-- application runs here

    logger.info("🛑 DocuMind backend shutting down …")


# ---------------------------------------------------------------------------
# FastAPI app initialisation
# ---------------------------------------------------------------------------
app = FastAPI(
    title="DocuMind API",
    description=(
        "RAG-powered document Q&A backend. "
        "Upload PDFs/DOCX, ask questions, get grounded answers."
    ),
    version="1.0.0",
    docs_url="/docs",      # Swagger UI
    redoc_url="/redoc",    # ReDoc UI
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

# GZip compression for large responses
app.add_middleware(GZipMiddleware, minimum_size=1000)

# CORS — allow the React frontend (and Vercel previews) to call the API
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:3000",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(upload_router,    prefix="/api/upload",    tags=["Upload"])
app.include_router(chat_router,      prefix="/api/chat",      tags=["Chat"])
app.include_router(documents_router, prefix="/api/documents", tags=["Documents"])


# ---------------------------------------------------------------------------
# Health-check endpoint
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Health"])
async def health_check():
    """Simple liveness probe used by Render and load balancers."""
    return {"status": "healthy", "service": "DocuMind API", "version": "1.0.0"}


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint — points developers to the docs."""
    return {
        "message": "Welcome to DocuMind API 🧠",
        "docs": "/docs",
        "health": "/health",
    }
