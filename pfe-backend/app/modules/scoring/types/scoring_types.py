"""Pydantic schemas for the scoring module."""
from __future__ import annotations

from typing import List

from pydantic import BaseModel


class ScoringRequest(BaseModel):
    """Payload for scoring a single product for a client."""

    client_id: str
    product_id: str


class DocumentPayload(BaseModel):
    """Inline document uploaded with a scoring request."""

    label: str
    text: str


class BatchScoringRequest(BaseModel):
    """Payload for batch-scoring products for a client.

    If product_ids is empty or None → score ALL products.
    If product_ids is provided → score only the listed products.
    """

    client_id: str
    document_ids: List[str] = []
    documents: List[DocumentPayload] = []
    product_ids: List[str] = []   # empty = all products
