from __future__ import annotations

"""
Document Router — Layer 3 automatic client detection.

For every "orphan" file in client_documents/ root (no folder, no filename match),
this service:
  1. Extracts the text (PDF → pypdf, image → OpenAI Vision, text → read)
  2. Searches Elasticsearch for the company name mentioned in the document
  3. Uses GPT-4o-mini to confirm the best candidate
  4. Caches the result in client_documents/.routing_cache.json
     so the LLM is only called once per file

Result: any document placed in client_documents/ is automatically
assigned to the right client without manual folder placement.
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DOCUMENTS_DIR  = Path(__file__).parent.parent.parent.parent / "client_documents"
_CACHE_FILE    = DOCUMENTS_DIR / ".routing_cache.json"
_ALL_EXT       = {".pdf", ".txt", ".md", ".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp", ".webp"}


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------

def _load_cache() -> Dict[str, Optional[str]]:
    """filename → client_id (or None if unresolved)"""
    if _CACHE_FILE.exists():
        try:
            return json.loads(_CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_cache(cache: Dict[str, Optional[str]]) -> None:
    _CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_documents_for_client(client_id: str) -> List[Dict[str, Any]]:
    """
    Return all documents that belong to client_id.
    Combines:
      - Layer 1: files in client_documents/{client_id}/
      - Layer 2: root files whose name contains client_id
      - Layer 3: root orphan files automatically classified by the LLM
    """
    from app.services.documents.local_document_loader import (
        load_documents_for_client, _load_file, _ALL_EXTENSIONS,
    )

    # Layers 1 & 2 — existing logic
    docs = load_documents_for_client(client_id)
    already_loaded = {d["label"] for d in docs}

    # Layer 3 — classify orphans and include those matching this client
    orphans = _find_orphans()
    if orphans:
        cache = _load_cache()
        changed = False

        for path in orphans:
            fname = path.name
            if fname in already_loaded:
                continue

            # Use cached result if available
            if fname in cache:
                assigned_id = cache[fname]
            else:
                # Extract text and classify
                assigned_id = _classify_orphan(path)
                cache[fname] = assigned_id
                changed = True
                logger.info(
                    "DocumentRouter: '%s' → client_id=%s",
                    fname, assigned_id or "UNKNOWN",
                )

            if assigned_id == client_id:
                src = _load_file(path)
                if src:
                    docs.append(src)
                    logger.info(
                        "DocumentRouter[%s]: auto-assigned '%s' via LLM classification",
                        client_id, fname,
                    )

        if changed:
            _save_cache(cache)

    return docs


def classify_all_orphans() -> Dict[str, Optional[str]]:
    """
    Classify every orphan file and return the full mapping.
    Useful for admin inspection or pre-warming the cache.
    """
    cache = _load_cache()
    changed = False
    for path in _find_orphans():
        if path.name not in cache:
            cache[path.name] = _classify_orphan(path)
            changed = True
    if changed:
        _save_cache(cache)
    return cache


def clear_cache() -> None:
    """Force re-classification of all orphan files."""
    if _CACHE_FILE.exists():
        _CACHE_FILE.unlink()
    logger.info("DocumentRouter: cache cleared")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _find_orphans() -> List[Path]:
    """Root-level files that are NOT in a client subfolder."""
    if not DOCUMENTS_DIR.exists():
        return []
    return [
        p for p in sorted(DOCUMENTS_DIR.iterdir())
        if p.is_file()
        and p.suffix.lower() in _ALL_EXT
        and not p.name.upper().startswith("README")
        and not p.name.startswith(".")
    ]


def _extract_text(path: Path) -> str:
    """Extract text from any supported file type."""
    ext = path.suffix.lower()
    try:
        if ext == ".pdf":
            import io, pypdf
            reader = pypdf.PdfReader(io.BytesIO(path.read_bytes()))
            return " ".join((p.extract_text() or "") for p in reader.pages)[:3000]
        if ext in {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp", ".webp"}:
            from app.services.documents.image_extractor import extract_text_from_image
            return extract_text_from_image(path.name, path.read_bytes(), use_openai_vision=True)[:3000]
        return path.read_text(encoding="utf-8", errors="replace")[:3000]
    except Exception as exc:
        logger.warning("DocumentRouter: could not extract text from '%s': %s", path.name, exc)
        return ""


def _extract_company_name(text: str) -> str:
    """
    Use GPT-4o-mini to extract the company name from document text.
    Falls back to the first clean line if GPT is unavailable.
    """
    try:
        from openai import OpenAI
        from app.core.config import settings
        if not settings.openai_api_key:
            raise RuntimeError("no key")

        client = OpenAI(api_key=settings.openai_api_key, timeout=15.0)
        snippet = re.sub(r"```[a-z]*\n?", "", text[:600]).strip()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=30,
            temperature=0.0,
            messages=[
                {"role": "system", "content": "Extract ONLY the company name from the document. Reply with the company name only, nothing else."},
                {"role": "user", "content": f"Document excerpt:\n{snippet}"},
            ],
        )
        name = response.choices[0].message.content.strip()
        logger.info("DocumentRouter: GPT extracted company name: '%s'", name)
        return name
    except Exception:
        # Fallback: first clean non-markdown line
        clean = re.sub(r"```[a-z]*\n?", "", text).strip()
        for line in clean.splitlines():
            line = line.strip()
            if len(line) > 3 and not line.startswith(("#", "-", "*", "`", "|")):
                if not re.match(r"^[\d\s€%,\.\*]+$", line):
                    return line
        return clean[:80]


def _search_candidates(text: str) -> List[Dict[str, str]]:
    """
    Search Elasticsearch for companies mentioned in the document text.
    Returns up to 5 candidates: [{"client_id": ..., "client_name": ...}]
    """
    try:
        from app.modules.elasticsearch.client import AbstractElasticsearchClient
        from app.modules.elasticsearch.indexes import ElasticsearchIndexes

        company_name = _extract_company_name(text)
        logger.info("DocumentRouter: searching ES for company name: '%s'", company_name)

        es = AbstractElasticsearchClient()
        hits = es._search(
            ElasticsearchIndexes.ACCOUNT,
            {
                "multi_match": {
                    "query":  company_name,
                    "fields": ["Name^3", "client_name^3"],
                    "type":   "best_fields",
                    "fuzziness": "AUTO",
                }
            },
            size=5,
            source_fields=["Name", "client_name", "Id"],
        )

        candidates = []
        for h in hits:
            src = h.get("_source", {})
            name = src.get("Name") or src.get("client_name") or ""
            cid  = src.get("Id") or h.get("_id") or ""
            if name and cid:
                candidates.append({"client_id": cid, "client_name": name})
        return candidates

    except Exception as exc:
        logger.warning("DocumentRouter: ES candidate search failed: %s", exc)
        return []


def _classify_orphan(path: Path) -> Optional[str]:
    """
    Full classification pipeline for one orphan file.
    Returns client_id if confident, else None.
    """
    text = _extract_text(path)
    if not text.strip():
        return None

    candidates = _search_candidates(text)
    if not candidates:
        logger.info("DocumentRouter: no ES candidates found for '%s'", path.name)
        return None

    # Ask GPT-4o-mini to confirm the best match
    return _llm_classify(path.name, text, candidates)


def _llm_classify(filename: str, text: str, candidates: List[Dict[str, str]]) -> Optional[str]:
    """Use GPT-4o-mini to identify which candidate client this document belongs to."""
    try:
        from openai import OpenAI
        from app.core.config import settings

        if not settings.openai_api_key:
            return None

        snippet = text[:1000].strip()
        candidates_str = "\n".join(
            f"  - ID: {c['client_id']} | Name: {c['client_name']}"
            for c in candidates
        )

        client = OpenAI(api_key=settings.openai_api_key, timeout=20.0)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=60,
            temperature=0.0,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a document routing assistant. "
                        "Given a document excerpt and a list of companies, "
                        "output ONLY the client_id that best matches, "
                        "or 'UNKNOWN' if you are not confident."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"DOCUMENT: '{filename}'\n"
                        f"EXCERPT:\n{snippet}\n\n"
                        f"CANDIDATE CLIENTS:\n{candidates_str}\n\n"
                        "Which client_id does this document belong to? "
                        "Reply with ONLY the client_id or UNKNOWN."
                    ),
                },
            ],
        )

        answer = response.choices[0].message.content.strip()
        valid_ids = {c["client_id"] for c in candidates}

        if answer in valid_ids:
            return answer

        logger.info("DocumentRouter: LLM returned '%s' for '%s' — not in candidates", answer, filename)
        return None

    except Exception as exc:
        logger.warning("DocumentRouter: LLM classification failed for '%s': %s", filename, exc)
        return None
