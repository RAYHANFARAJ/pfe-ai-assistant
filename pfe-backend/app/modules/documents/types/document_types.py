"""Pydantic schemas for the documents module."""
from __future__ import annotations

from pydantic import BaseModel


class UploadResponse(BaseModel):
    """Response returned after a document upload."""

    status: str
    label: str
    text: str
    chars: int
    preview: str
