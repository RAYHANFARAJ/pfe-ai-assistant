"""Request types for the reports module."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class ClientInfo(BaseModel):
    client_id: str
    client_name: str
    sector: Optional[str] = None
    employees: Optional[int] = None
    website: Optional[str] = None


class PdfReportRequest(BaseModel):
    client: ClientInfo
    batch_result: Dict[str, Any]
