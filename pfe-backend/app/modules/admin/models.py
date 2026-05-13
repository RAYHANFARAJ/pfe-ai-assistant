from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


def _uid(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4()}"


def _now() -> int:
    return int(time.time() * 1000)


# ── Products ──────────────────────────────────────────────────────────────────

class ProductCreate(BaseModel):
    name: str


class ProductUpdate(BaseModel):
    name: Optional[str] = None


# ── Criteria ──────────────────────────────────────────────────────────────────

class CriterionCreate(BaseModel):
    label: str
    answer_type: str = "single_choice"   # numeric | single_choice | multiple_choice | text
    unit: Optional[str] = None
    order: int = 1
    section_number: int = 1
    default_score: float = 0
    is_main: bool = True
    comment_enable: bool = True
    agent_prompt: Optional[str] = None


class CriterionUpdate(BaseModel):
    label: Optional[str] = None
    answer_type: Optional[str] = None
    unit: Optional[str] = None
    order: Optional[int] = None
    section_number: Optional[int] = None
    default_score: Optional[float] = None
    is_main: Optional[bool] = None
    agent_prompt: Optional[str] = None


# ── Choices ───────────────────────────────────────────────────────────────────

class ChoiceCreate(BaseModel):
    label: str
    score: float = 0
    is_blocking: bool = False
    condition_body: Optional[str] = None   # JS condition, e.g. "return a >= 500"


class ChoiceUpdate(BaseModel):
    label: Optional[str] = None
    score: Optional[float] = None
    is_blocking: Optional[bool] = None
    condition_body: Optional[str] = None


# ── Data Sources ─────────────────────────────────────────────────────────────

class DataSourceCreate(BaseModel):
    label: str
    source_type: str              # website | linkedin | news | document | crm
    client_id: Optional[str] = None   # None = global (all clients)
    url: Optional[str] = None
    enabled: bool = True
    config: Optional[Dict[str, Any]] = None


class DataSourceUpdate(BaseModel):
    label: Optional[str] = None
    url: Optional[str] = None
    enabled: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None


# ── Campaigns ─────────────────────────────────────────────────────────────────

class CampaignCreate(BaseModel):
    name: str
    description: Optional[str] = None
    product_ids: List[str] = []
    status: str = "draft"   # draft | active | archived


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    product_ids: Optional[List[str]] = None
    status: Optional[str] = None
