from __future__ import annotations

import io
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DOCUMENTS_DIR = Path(__file__).parent.parent.parent.parent / "client_documents"

_DOC_EXTENSIONS = {".pdf", ".txt", ".md"}
_IMG_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp", ".webp"}
_ALL_EXTENSIONS = _DOC_EXTENSIONS | _IMG_EXTENSIONS


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_local_documents() -> List[Dict[str, Any]]:
    """
    Load all documents from client_documents/ that have no specific client.
    These are applied to every pipeline run (global documents).
    Only files at the ROOT of client_documents/ are returned here.
    Files inside a subfolder are client-specific (use load_documents_for_client).
    """
    return _load_from_directory(DOCUMENTS_DIR, recursive=False)


def load_documents_for_client(client_id: str) -> List[Dict[str, Any]]:
    """
    Return documents specifically assigned to this client.

    Resolution order (3 layers):
      1. Folder match  — client_documents/{client_id}/
      2. Filename match — any root file whose name contains the client_id
      3. LLM classification — reads file content to detect the client

    Only Layer 1 is implemented by default (reliable + instant).
    Layer 3 (LLM) is opt-in via classify_orphans=True to avoid API costs.
    """
    docs: List[Dict[str, Any]] = []

    # ── Layer 1: dedicated subfolder ────────────────────────────────────────
    client_dir = DOCUMENTS_DIR / client_id
    if client_dir.exists() and client_dir.is_dir():
        found = _load_from_directory(client_dir, recursive=True)
        if found:
            logger.info(
                "ClientDocs[%s]: %d document(s) found in dedicated folder",
                client_id, len(found),
            )
            docs.extend(found)

    # ── Layer 2: filename contains client_id ────────────────────────────────
    if DOCUMENTS_DIR.exists():
        for path in sorted(DOCUMENTS_DIR.iterdir()):
            if path.is_file() and client_id.lower() in path.name.lower():
                src = _load_file(path)
                if src:
                    docs.append(src)
                    logger.info(
                        "ClientDocs[%s]: matched by filename — '%s'",
                        client_id, path.name,
                    )

    return docs


def classify_document_client(
    filename: str,
    text: str,
    candidate_clients: List[Dict[str, Any]],
) -> Optional[str]:
    """
    Layer 3 — LLM classification.

    Given extracted document text and a list of candidate clients
    (each with client_id + client_name), ask gpt-4o-mini to identify
    which client this document belongs to.

    Returns client_id if matched with confidence, else None.
    Only call this when Layers 1 and 2 fail.

    candidate_clients: [{"client_id": "...", "client_name": "..."}]
    """
    if not candidate_clients or not text.strip():
        return None

    from openai import OpenAI
    from app.core.config import settings

    if not settings.openai_api_key:
        return None

    # Use the first 800 chars of the document — enough to identify the company
    snippet = text[:800].strip()

    # Build the candidates list for the prompt
    candidates_str = "\n".join(
        f"  - ID: {c['client_id']} | Name: {c['client_name']}"
        for c in candidate_clients
    )

    client = OpenAI(api_key=settings.openai_api_key, timeout=15.0)
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=50,
            temperature=0.0,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a document routing assistant. "
                        "Given a document excerpt and a list of companies, "
                        "output ONLY the client_id that matches, or 'UNKNOWN' if unsure."
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
        # Validate the answer is one of the candidates
        valid_ids = {c["client_id"] for c in candidate_clients}
        if answer in valid_ids:
            logger.info(
                "LLM classified '%s' → client_id=%s", filename, answer
            )
            return answer
        logger.info("LLM returned UNKNOWN for '%s'", filename)
        return None
    except Exception as exc:
        logger.warning("LLM document classification failed: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_from_directory(
    directory: Path,
    recursive: bool = False,
) -> List[Dict[str, Any]]:
    sources: List[Dict[str, Any]] = []
    if not directory.exists():
        return sources

    paths = directory.rglob("*") if recursive else directory.iterdir()
    for path in sorted(paths):
        if not path.is_file():
            continue
        if path.suffix.lower() not in _ALL_EXTENSIONS:
            continue
        if path.name.upper().startswith("README"):
            continue
        src = _load_file(path)
        if src:
            sources.append(src)
    return sources


def _load_file(path: Path) -> Optional[Dict[str, Any]]:
    try:
        text = _extract(path)
        if not text or len(text.split()) < 10:
            logger.warning("LocalDocs: skipped '%s' — too short", path.name)
            return None
        # Images get line-by-line sections so each fact has its own embedding
        is_image = path.suffix.lower() in _IMG_EXTENSIONS
        sections = _build_image_sections(text) if is_image else _build_sections(text)
        source = {
            "type":     "document",
            "url":      None,
            "label":    path.name,
            "text":     text,
            "sections": sections,
            "anchors":  {},
        }
        logger.info(
            "LocalDocs: loaded '%s' — %d chars, %d sections",
            path.name, len(text), len(source["sections"]),
        )
        return source
    except Exception as exc:
        logger.error("LocalDocs: failed to load '%s': %s", path.name, exc)
        return None


def _extract(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".pdf":
        return _extract_pdf(path.read_bytes())
    if ext in _IMG_EXTENSIONS:
        from app.services.documents.image_extractor import extract_text_from_image
        return extract_text_from_image(path.name, path.read_bytes(), use_openai_vision=True)
    return path.read_text(encoding="utf-8", errors="replace")


def _extract_pdf(content: bytes) -> str:
    import pypdf
    reader = pypdf.PdfReader(io.BytesIO(content))
    pages = [
        (page.extract_text() or "").strip()
        for page in reader.pages
    ]
    return re.sub(r"\s+", " ", "\n\n".join(p for p in pages if p)).strip()


def _build_image_sections(text: str) -> List[Dict[str, str]]:
    """
    For image documents, create one section per fact line.
    Skips markdown fences, section headings, and lines too short to be useful.
    Prefixes each line with its section for better semantic matching.
    """
    sections = []
    current_heading = ""

    # Remove markdown code fences
    import re as _re
    text = _re.sub(r"```[a-z]*\n?", "", text).strip()

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # Section headings — all caps, no colon (no value)
        if line.isupper() and len(line) > 5 and ":" not in line:
            current_heading = line
            continue
        # Skip lines that are just a number, date, or too short to be meaningful
        if len(line.split()) < 4:
            continue
        # Each key:value fact becomes its own chunk with section context
        prefix = f"{current_heading} — " if current_heading else ""
        sections.append({"heading": current_heading, "text": f"{prefix}{line}"})

    return sections or [{"heading": "", "text": text[:1200]}]


def _build_sections(text: str) -> List[Dict[str, str]]:
    sections = []
    qa_blocks = re.split(r"(?=\bQ\d{1,2}[\.\)])", text)
    if len(qa_blocks) > 2:
        for block in qa_blocks:
            block = block.strip()
            if len(block.split()) >= 10:
                sections.append({"heading": "", "text": block[:1200]})
        if sections:
            return sections
    for para in re.split(r"\n{2,}", text):
        para = para.strip()
        if len(para.split()) >= 8:
            sections.append({"heading": "", "text": para[:1200]})
        if len(sections) >= 30:
            break
    return sections or [{"heading": "", "text": text[:1200]}]
