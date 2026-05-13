"""Request/response types for the campaigns module."""
from __future__ import annotations

from typing import List
from pydantic import BaseModel


class CampaignScoreRequest(BaseModel):
    account_ids: List[str]
    product_id: str
