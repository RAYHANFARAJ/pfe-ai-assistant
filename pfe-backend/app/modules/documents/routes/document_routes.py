"""Documents HTTP routes — file upload + persistent store endpoints."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Query, UploadFile

from app.core.auth import TokenData, require_auth
from app.modules.documents.controllers.document_controller import handle_upload
from app.modules.documents.services.document_store import (
    delete_document, load_documents, save_document,
)

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    client_id: Optional[str] = Query(None),
    user: TokenData = Depends(require_auth),
) -> Dict[str, Any]:
    """Upload a PDF, image, or text file. If client_id is given, saves persistently."""
    content = await file.read()
    result = handle_upload(file.filename or "document", content)
    if result.get("status") == "ok" and client_id:
        save_document(client_id, result["label"], result["text"], result["chars"])
    return result


@router.get("/client/{client_id}")
def get_client_documents(
    client_id: str,
    user: TokenData = Depends(require_auth),
) -> List[Dict[str, Any]]:
    """Return all previously uploaded documents for a client."""
    return load_documents(client_id)


@router.delete("/client/{client_id}/{label}")
def remove_client_document(
    client_id: str,
    label: str,
    user: TokenData = Depends(require_auth),
) -> Dict[str, Any]:
    """Remove a saved document for a client."""
    found = delete_document(client_id, label)
    return {"status": "ok" if found else "not_found"}
