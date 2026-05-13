"""Report history — persists every PDF (file + metadata) when downloaded.

Each report gets:
  - A unique ID
  - Metadata saved in output/reports_history.json
  - The actual PDF file saved in output/reports/{id}.pdf
  → Users can re-download any past report from the Reports page.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

_HISTORY_FILE = Path("output") / "reports_history.json"
_PDF_DIR      = Path("output") / "reports"


def save_report(
    client: Dict[str, Any],
    batch_result: Dict[str, Any],
    user_name: str,
    pdf_bytes: Optional[bytes] = None,
) -> Dict[str, Any]:
    """Save report metadata + PDF file. Returns the new history entry."""
    results   = batch_result.get("results", [])
    succeeded = [r for r in results if r.get("status") == "success"]
    eligible  = [r for r in succeeded if r.get("summary", {}).get("eligibility_status") == "eligible"]
    to_review = [r for r in succeeded if r.get("summary", {}).get("eligibility_status") == "to_review"]
    summary   = batch_result.get("batch_summary", {})

    report_id = str(uuid.uuid4())[:8]
    entry = {
        "id":                 report_id,
        "downloaded_at":      datetime.now().isoformat(),
        "user":               user_name,
        "client_id":          client.get("client_id", ""),
        "client_name":        client.get("client_name", ""),
        "sector":             client.get("sector", ""),
        "employees":          client.get("employees"),
        "website":            client.get("website", ""),
        "products_total":     summary.get("total", len(results)),
        "products_scored":    summary.get("succeeded", len(succeeded)),
        "eligible_count":     len(eligible),
        "to_review_count":    len(to_review),
        "not_eligible_count": len(succeeded) - len(eligible) - len(to_review),
        "duration_seconds":   summary.get("duration_seconds", 0),
        "has_pdf":            False,
        "filename":           f"sellynx_{client.get('client_name','client').replace(' ', '_')}_{report_id}.pdf",
    }

    # Save the actual PDF file
    if pdf_bytes:
        _PDF_DIR.mkdir(parents=True, exist_ok=True)
        pdf_path = _PDF_DIR / f"{report_id}.pdf"
        pdf_path.write_bytes(pdf_bytes)
        entry["has_pdf"] = True

    history = _load()
    history.insert(0, entry)
    history = history[:200]             # keep last 200
    _save(history)
    return entry


def get_history() -> List[Dict[str, Any]]:
    entries = _load()
    # Normalize legacy entries that may lack newer fields
    for e in entries:
        e.setdefault("has_pdf", False)
        e.setdefault("filename", f"sellynx_{e.get('client_name','client').replace(' ','_')}_{e.get('id','')}.pdf")
    return entries


def get_pdf(report_id: str) -> Optional[bytes]:
    """Return the saved PDF bytes for a report ID, or None if not found."""
    path = _PDF_DIR / f"{report_id}.pdf"
    if path.exists():
        return path.read_bytes()
    return None


def delete_report(report_id: str) -> bool:
    """Remove a report entry and its PDF file."""
    history = _load()
    before  = len(history)
    history = [e for e in history if e.get("id") != report_id]
    if len(history) < before:
        _save(history)
        pdf = _PDF_DIR / f"{report_id}.pdf"
        if pdf.exists():
            pdf.unlink()
        return True
    return False


def _load() -> List[Dict[str, Any]]:
    try:
        if _HISTORY_FILE.exists():
            return json.loads(_HISTORY_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return []


def _save(data: List[Dict[str, Any]]) -> None:
    _HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    _HISTORY_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
