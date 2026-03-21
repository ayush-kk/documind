"""
utils/doc_registry.py
======================
Lightweight JSON-based document registry.

Stores document metadata (filename, doc_id, chunk count, etc.) in a simple
JSON file so we can serve the document listing endpoint without querying
ChromaDB for metadata each time.

In production you would replace this with a proper database (PostgreSQL,
SQLite, etc.), but for a portfolio project this is perfectly sufficient.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

REGISTRY_PATH = os.getenv("DOC_REGISTRY_PATH", "./doc_registry.json")


def _load_registry() -> Dict[str, dict]:
    """Load the JSON registry from disk. Returns empty dict if not found."""
    path = Path(REGISTRY_PATH)
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _save_registry(data: Dict[str, dict]) -> None:
    """Atomically save the registry to disk."""
    path = Path(REGISTRY_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Write to temp file first, then rename (atomic on POSIX)
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    tmp.replace(path)


def register_document(
    doc_id: str,
    filename: str,
    file_type: str,
    num_chunks: int,
    size_bytes: int,
) -> dict:
    """
    Add a new document entry to the registry.

    Returns the created metadata dict.
    """
    registry = _load_registry()
    entry = {
        "doc_id": doc_id,
        "filename": filename,
        "file_type": file_type,
        "num_chunks": num_chunks,
        "size_bytes": size_bytes,
        "uploaded_at": datetime.utcnow().isoformat(),
    }
    registry[doc_id] = entry
    _save_registry(registry)
    logger.info(f"Registered document: {filename} (doc_id={doc_id})")
    return entry


def get_document(doc_id: str) -> Optional[dict]:
    """Retrieve metadata for a single document by ID. Returns None if not found."""
    return _load_registry().get(doc_id)


def list_documents() -> List[dict]:
    """Return all registered documents, newest first."""
    registry = _load_registry()
    docs = list(registry.values())
    docs.sort(key=lambda d: d.get("uploaded_at", ""), reverse=True)
    return docs


def delete_document(doc_id: str) -> bool:
    """
    Remove a document from the registry.

    Returns:
        True if removed, False if not found.
    """
    registry = _load_registry()
    if doc_id not in registry:
        return False
    del registry[doc_id]
    _save_registry(registry)
    logger.info(f"Unregistered document: doc_id={doc_id}")
    return True
