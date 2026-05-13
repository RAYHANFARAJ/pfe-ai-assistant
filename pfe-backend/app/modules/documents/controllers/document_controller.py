"""Documents controller — handles upload orchestration."""
from __future__ import annotations

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def handle_upload(filename: str, content: bytes) -> Dict[str, Any]:
    """Extract text from an uploaded file and return the result."""
    from app.modules.documents.services.image_extractor import is_image_file, extract_text_from_image
    from app.modules.documents.services.document_extractor import _extract_text

    if is_image_file(filename):
        text = extract_text_from_image(filename, content, use_openai_vision=True)
    else:
        text = _extract_text(filename, content)

    if not text.strip():
        return {"status": "error", "detail": "Could not extract text from file."}

    return {
        "status":  "ok",
        "label":   filename,
        "text":    text,
        "chars":   len(text),
        "preview": text[:300].strip(),
    }
