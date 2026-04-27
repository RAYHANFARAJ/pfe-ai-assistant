from __future__ import annotations

import io
import logging
import re
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# Folder where the user drops PDF/TXT files manually
DOCUMENTS_DIR = Path(__file__).parent.parent.parent.parent / "client_documents"


def load_local_documents() -> List[Dict[str, Any]]:
    """
    Read every PDF and TXT file from client_documents/ and return
    them as source dicts — same format used by the scoring pipeline.

    Drop any file into pfe-backend/client_documents/ and it will be
    automatically picked up on the next pipeline run (no restart needed).
    """
    sources: List[Dict[str, Any]] = []

    if not DOCUMENTS_DIR.exists():
        return sources

    for path in sorted(DOCUMENTS_DIR.iterdir()):
        if path.suffix.lower() not in (".pdf", ".txt", ".md"):
            continue
        if path.name.upper().startswith("README"):
            continue
        try:
            text = _extract(path)
            if not text or len(text.split()) < 20:
                logger.warning("LocalDocs: skipped '%s' — too short or empty", path.name)
                continue
            sources.append({
                "type":     "document",
                "url":      None,
                "label":    path.name,
                "text":     text,
                "sections": _build_sections(text),
                "anchors":  {},
            })
            logger.info(
                "LocalDocs: loaded '%s' — %d chars, %d sections",
                path.name, len(text), len(sources[-1]["sections"]),
            )
        except Exception as exc:
            logger.error("LocalDocs: failed to load '%s': %s", path.name, exc)

    return sources


def _extract(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        return _extract_pdf(path.read_bytes())
    return path.read_text(encoding="utf-8", errors="replace")


def _extract_pdf(content: bytes) -> str:
    import pypdf
    reader = pypdf.PdfReader(io.BytesIO(content))
    pages = []
    for page in reader.pages:
        text = (page.extract_text() or "").strip()
        if text:
            pages.append(text)
    return re.sub(r"\s+", " ", "\n\n".join(pages)).strip()


def _build_sections(text: str) -> List[Dict[str, str]]:
    """
    Smart section builder:
    1. If the document has Q&A structure (Q1. / Q2. / …), split on question numbers
       so each question + full answer stays together in one section.
    2. Otherwise, split on paragraph boundaries (double newlines).
    Each section is kept up to 1 200 chars so the LLM sees the complete answer.
    """
    sections = []

    # Try Q&A split first: detect "Q1." … "Q99." markers
    qa_blocks = re.split(r"(?=\bQ\d{1,2}[\.\)])", text)
    if len(qa_blocks) > 2:
        for block in qa_blocks:
            block = block.strip()
            if len(block.split()) >= 10:
                sections.append({"heading": "", "text": block[:1200]})
        if sections:
            return sections

    # Fallback: split on paragraph breaks
    for para in re.split(r"\n{2,}", text):
        para = para.strip()
        if len(para.split()) >= 8:
            sections.append({"heading": "", "text": para[:1200]})
        if len(sections) >= 30:
            break

    return sections or [{"heading": "", "text": text[:1200]}]
