"""Persistent document store — saves uploaded docs by client_id.

When a user uploads a PDF for client X, the extracted text is saved here.
The next time the same client is scored, the documents are reloaded
automatically without the user needing to re-upload them.

Storage: output/client_docs/{client_id}.json
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

_STORE_DIR = Path("output") / "client_docs"


def save_document(client_id: str, label: str, text: str, chars: int) -> None:
    """Persist an uploaded document for a client."""
    _STORE_DIR.mkdir(parents=True, exist_ok=True)
    path = _STORE_DIR / f"{client_id}.json"
    docs = _load(path)
    # Avoid duplicates by label
    docs = [d for d in docs if d.get("label") != label]
    docs.append({"label": label, "text": text, "chars": chars})
    path.write_text(json.dumps(docs, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("DocumentStore: saved '%s' for client %s", label, client_id)


def load_documents(client_id: str) -> List[Dict[str, Any]]:
    """Return all saved documents for a client."""
    path = _STORE_DIR / f"{client_id}.json"
    return _load(path)


def delete_document(client_id: str, label: str) -> bool:
    """Remove one document from the store. Returns True if found."""
    path = _STORE_DIR / f"{client_id}.json"
    docs = _load(path)
    before = len(docs)
    docs = [d for d in docs if d.get("label") != label]
    if len(docs) < before:
        path.write_text(json.dumps(docs, ensure_ascii=False, indent=2), encoding="utf-8")
        return True
    return False


def _load(path: Path) -> List[Dict[str, Any]]:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("DocumentStore load error: %s", exc)
    return []
