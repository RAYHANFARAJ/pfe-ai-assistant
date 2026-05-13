"""Reports controller — delegates PDF generation to the service."""
from __future__ import annotations

from typing import Any, Dict

from app.modules.reports.services.pdf_service import build_pdf


def generate_pdf(client: Dict[str, Any], batch_result: Dict[str, Any]) -> bytes:
    """Build and return PDF bytes for a client qualification report."""
    return build_pdf(client, batch_result)
