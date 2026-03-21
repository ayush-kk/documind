"""
services/document_processor.py
================================
Responsible for:
  1. Detecting file type (PDF / DOCX)
  2. Extracting raw text
  3. Splitting text into overlapping chunks ready for embedding

Design decision — overlapping chunks:
  Overlap ensures that sentences split across chunk boundaries are still
  retrievable. 200-character overlap on 1000-character chunks is a safe default.
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass
from typing import List, Tuple

import docx                          # python-docx
from pypdf import PdfReader          # pypdf (actively maintained fork of PyPDF2)
from langchain.text_splitter import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data container for a single chunk
# ---------------------------------------------------------------------------

@dataclass
class TextChunk:
    """A piece of text extracted from a document, ready to be embedded."""

    content: str
    page_number: int | None  # available for PDFs, None for DOCX
    chunk_index: int          # position of this chunk within the document


# ---------------------------------------------------------------------------
# Main processor class
# ---------------------------------------------------------------------------

class DocumentProcessor:
    """
    Handles all document ingestion logic.

    Usage:
        processor = DocumentProcessor()
        chunks = processor.process(file_bytes, filename="report.pdf")
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        """
        Args:
            chunk_size:    Maximum characters per chunk.
            chunk_overlap: Characters shared between adjacent chunks.
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # RecursiveCharacterTextSplitter tries to split on paragraphs, then
        # sentences, then words — preserving semantic coherence.
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process(self, file_bytes: bytes, filename: str) -> List[TextChunk]:
        """
        Entry point. Detects file type and delegates to the right extractor.

        Returns:
            List[TextChunk] — ordered list of text chunks with metadata.
        Raises:
            ValueError: if the file type is not supported.
        """
        lower = filename.lower()

        if lower.endswith(".pdf"):
            raw_pages = self._extract_pdf(file_bytes)
        elif lower.endswith(".docx"):
            raw_pages = self._extract_docx(file_bytes)
        elif lower.endswith(".txt"):
            raw_pages = self._extract_txt(file_bytes)
        else:
            raise ValueError(
                f"Unsupported file type: {filename}. "
                "Supported: .pdf, .docx, .txt"
            )

        chunks = self._split_into_chunks(raw_pages)
        logger.info(
            f"Processed '{filename}': {len(raw_pages)} page(s) → {len(chunks)} chunk(s)"
        )
        return chunks

    # ------------------------------------------------------------------
    # Private extractors
    # ------------------------------------------------------------------

    def _extract_pdf(self, file_bytes: bytes) -> List[Tuple[str, int]]:
        """
        Extract text page-by-page from a PDF.

        Returns:
            List of (text, page_number) tuples. Page numbers are 1-indexed.
        """
        reader = PdfReader(io.BytesIO(file_bytes))
        pages: List[Tuple[str, int]] = []

        for i, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            text = text.strip()
            if text:  # skip blank pages
                pages.append((text, i))

        if not pages:
            raise ValueError("PDF appears to contain no extractable text. Is it scanned?")

        return pages

    def _extract_docx(self, file_bytes: bytes) -> List[Tuple[str, int]]:
        """
        Extract text from a DOCX file. DOCX has no native page concept,
        so all paragraphs are treated as page 1.
        """
        doc = docx.Document(io.BytesIO(file_bytes))
        full_text = "\n".join(
            para.text for para in doc.paragraphs if para.text.strip()
        )
        if not full_text:
            raise ValueError("DOCX appears to contain no text.")
        return [(full_text, None)]  # no page numbers for DOCX

    def _extract_txt(self, file_bytes: bytes) -> List[Tuple[str, int]]:
        """Extract plain text — used for .txt uploads."""
        text = file_bytes.decode("utf-8", errors="replace").strip()
        if not text:
            raise ValueError("Text file is empty.")
        return [(text, None)]

    # ------------------------------------------------------------------
    # Chunking
    # ------------------------------------------------------------------

    def _split_into_chunks(
        self, pages: List[Tuple[str, int]]
    ) -> List[TextChunk]:
        """
        Split page texts into overlapping chunks using LangChain's splitter.
        Page number metadata is preserved per chunk.
        """
        all_chunks: List[TextChunk] = []
        global_index = 0

        for text, page_num in pages:
            splits = self._splitter.split_text(text)
            for split in splits:
                if split.strip():
                    all_chunks.append(
                        TextChunk(
                            content=split.strip(),
                            page_number=page_num,
                            chunk_index=global_index,
                        )
                    )
                    global_index += 1

        return all_chunks
