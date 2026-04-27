from __future__ import annotations

import io
import re
import uuid
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# In-memory store: document_id → source dict
# Fine for demo / single-process use. Replace with Redis or DB for production.
_DOCUMENT_STORE: Dict[str, Dict[str, Any]] = {}


def extract_and_store(filename: str, file_bytes: bytes) -> Dict[str, Any]:
    """
    Extract text from a PDF (or plain text) file, build a source dict,
    store it in memory, and return the document metadata.
    """
    text = _extract_text(filename, file_bytes)
    if not text.strip():
        raise ValueError(f"Could not extract any text from '{filename}'.")

    doc_id = str(uuid.uuid4())
    source = {
        "type":     "document",
        "url":      None,
        "label":    filename,
        "text":     text,
        "sections": _build_sections(text),
        "anchors":  {},
        "doc_id":   doc_id,
    }
    _DOCUMENT_STORE[doc_id] = source
    logger.info("Document stored: id=%s label=%s chars=%d", doc_id, filename, len(text))

    return {
        "doc_id":   doc_id,
        "label":    filename,
        "chars":    len(text),
        "preview":  text[:300].strip(),
    }


def get_sources(doc_ids: List[str]) -> List[Dict[str, Any]]:
    """Retrieve stored sources by their IDs. Silently skips unknown IDs."""
    sources = []
    for doc_id in doc_ids:
        src = _DOCUMENT_STORE.get(doc_id)
        if src:
            sources.append(src)
        else:
            logger.warning("Document id=%s not found in store (expired or unknown)", doc_id)
    return sources


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------

def _extract_text(filename: str, file_bytes: bytes) -> str:
    name_lower = filename.lower()
    if name_lower.endswith(".pdf"):
        return _extract_pdf(file_bytes)
    if name_lower.endswith((".txt", ".md")):
        return file_bytes.decode("utf-8", errors="replace")
    # Fallback: try as UTF-8 text
    return file_bytes.decode("utf-8", errors="replace")


def _extract_pdf(file_bytes: bytes) -> str:
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        pages = []
        for page in reader.pages:
            text = page.extract_text() or ""
            if text.strip():
                pages.append(text.strip())
        return "\n\n".join(pages)
    except Exception as exc:
        logger.error("PDF extraction failed: %s", exc)
        raise ValueError(f"PDF extraction failed: {exc}") from exc


def _build_sections(text: str) -> list:
    sections = []
    for para in re.split(r"\n{2,}", text):
        para = para.strip()
        if len(para.split()) >= 5:
            sections.append({"heading": "", "text": para[:600]})
        if len(sections) >= 20:
            break
    return sections
