"""Reports HTTP routes — PDF generation, history and re-download."""
from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from app.core.auth import TokenData, require_auth
from app.modules.reports.controllers.report_controller import generate_pdf
from app.modules.reports.types.report_types import PdfReportRequest
from app.modules.reports.services.report_history_service import (
    delete_report, get_history, get_pdf, save_report,
)

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post("/pdf")
def download_pdf(
    body: PdfReportRequest,
    user: TokenData = Depends(require_auth),
) -> Response:
    """Generate PDF, save to history and return it for download."""
    pdf_bytes = generate_pdf(body.client.model_dump(), body.batch_result)
    filename  = f"sellynx_{body.client.client_name.replace(' ', '_')}.pdf"

    # Persist PDF + metadata
    try:
        save_report(
            body.client.model_dump(),
            body.batch_result,
            user.name,
            pdf_bytes=pdf_bytes,
        )
    except Exception:
        pass   # never block the download because of history failure

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/history")
def report_history(user: TokenData = Depends(require_auth)) -> List[Dict[str, Any]]:
    """Return all saved reports (newest first)."""
    return get_history()


@router.get("/download/{report_id}")
def redownload_pdf(
    report_id: str,
    user: TokenData = Depends(require_auth),
) -> Response:
    """Re-download a previously generated PDF by its report ID."""
    pdf_bytes = get_pdf(report_id)
    if not pdf_bytes:
        raise HTTPException(status_code=404, detail="PDF not found for this report.")

    history = get_history()
    entry   = next((e for e in history if e["id"] == report_id), {})
    filename = entry.get("filename", f"sellynx_{report_id}.pdf")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete("/{report_id}")
def remove_report(
    report_id: str,
    user: TokenData = Depends(require_auth),
) -> Dict[str, Any]:
    """Delete a report from history and remove its PDF file."""
    found = delete_report(report_id)
    if not found:
        raise HTTPException(status_code=404, detail="Report not found.")
    return {"status": "deleted", "id": report_id}
