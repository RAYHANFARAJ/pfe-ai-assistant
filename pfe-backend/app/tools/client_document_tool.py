from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.services.documents.document_router import get_documents_for_client

logger = logging.getLogger(__name__)


class ClientDocumentTool:
    """
    Tool that loads client-specific documents (PDFs, images, text files)
    and returns them as page dicts — same output format as SemanticCrawlTool,
    LinkedInPlaywrightTool, and NewsSearchTool.

    This makes documents a first-class source in the scoring pipeline,
    treated exactly like a website page or a LinkedIn page.

    Source resolution (in order):
      1. Files inside client_documents/{client_id}/   (folder match)
      2. Files whose name contains client_id           (filename match)
      3. Orphan files auto-classified by LLM           (automatic routing)
      4. Files uploaded inline via the API             (inline documents)

    Usage in the orchestrator:
        doc_tool = ClientDocumentTool()
        doc_data = doc_tool.run(client_id, inline_documents=[...])
        # → {"client_id": "...", "pages": [{url, title, full_text, sections, ...}]}
    """

    def run(
        self,
        client_id: str,
        inline_documents: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Load all documents for this client.

        Parameters
        ----------
        client_id:
            The Salesforce/CRM client identifier. Used to look up
            the client-specific subfolder in client_documents/.
        inline_documents:
            Optional list of documents uploaded via the API at request time.
            Each item: {"label": str, "text": str}

        Returns
        -------
        {"client_id": client_id, "pages": [page_dict, ...]}

        Each page_dict matches the format used by other tools:
            url, title, snippet, full_text, sections, anchors
        """
        pages: List[Dict[str, Any]] = []

        # ── Layers 1, 2, 3: folder match → filename match → LLM auto-routing ──
        try:
            file_sources = get_documents_for_client(client_id)
            for src in file_sources:
                pages.append(self._source_to_page(src))
            if file_sources:
                logger.info(
                    "ClientDocumentTool[%s]: %d file(s) loaded (folder/filename/auto-routing)",
                    client_id, len(file_sources),
                )
        except Exception as exc:
            logger.error(
                "ClientDocumentTool[%s]: disk load failed: %s", client_id, exc
            )

        # ── Layer 3: inline documents uploaded at request time ───────────────
        for doc in (inline_documents or []):
            label = doc.get("label", "Document")
            text  = doc.get("text", "").strip()
            if not text:
                continue
            pages.append({
                "url":       None,
                "title":     label,
                "snippet":   text[:300],
                "full_text": text,
                "sections":  self._build_sections(text),
                "anchors":   {},
                "source":    "inline_upload",
            })
            logger.info(
                "ClientDocumentTool[%s]: inline doc '%s' (%d chars)",
                client_id, label, len(text),
            )

        logger.info(
            "ClientDocumentTool[%s]: total %d document page(s) ready",
            client_id, len(pages),
        )
        return {"client_id": client_id, "pages": pages}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _source_to_page(src: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a source dict (loader format) to a page dict (tool format)."""
        text = src.get("text", "")
        return {
            "url":       src.get("url"),
            "title":     src.get("label", "Document"),
            "snippet":   text[:300],
            "full_text": text,
            "sections":  src.get("sections", []),
            "anchors":   src.get("anchors", {}),
            "source":    "local_file",
        }

    @staticmethod
    def _build_sections(text: str) -> List[Dict[str, str]]:
        import re
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
            if len(sections) >= 20:
                break
        return sections or [{"heading": "", "text": text[:1200]}]
