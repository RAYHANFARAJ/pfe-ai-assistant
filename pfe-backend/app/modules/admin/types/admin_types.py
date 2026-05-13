"""Pydantic request/response schemas for the admin module."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ProductCreate(BaseModel):
    """Payload required to create a new product."""

    name: str


class ProductUpdate(BaseModel):
    """Partial payload for updating a product."""

    name: Optional[str] = None


class CriterionCreate(BaseModel):
    """Payload required to create a criterion under a product."""

    label: str
    answer_type: str = "single_choice"
    unit: Optional[str] = None
    order: int = 1
    section_number: int = 1
    default_score: float = 0
    is_main: bool = True
    comment_enable: bool = True
    agent_prompt: Optional[str] = None


class CriterionUpdate(BaseModel):
    """Partial payload for updating a criterion."""

    label: Optional[str] = None
    answer_type: Optional[str] = None
    unit: Optional[str] = None
    order: Optional[int] = None
    section_number: Optional[int] = None
    default_score: Optional[float] = None
    is_main: Optional[bool] = None
    agent_prompt: Optional[str] = None


class ChoiceCreate(BaseModel):
    """Payload required to create a choice for a criterion."""

    label: str
    score: float = 0
    is_blocking: bool = False
    condition_body: Optional[str] = None


class ChoiceUpdate(BaseModel):
    """Partial payload for updating a choice."""

    label: Optional[str] = None
    score: Optional[float] = None
    is_blocking: Optional[bool] = None
    condition_body: Optional[str] = None


class CampaignCreate(BaseModel):
    """Payload required to create a campaign."""

    name: str
    description: Optional[str] = None
    product_ids: List[str] = []
    status: str = "draft"
    pole: Optional[str] = None
    type: str = "national"
    interlocutor: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class CampaignUpdate(BaseModel):
    """Partial payload for updating a campaign."""

    name: Optional[str] = None
    description: Optional[str] = None
    product_ids: Optional[List[str]] = None
    status: Optional[str] = None
    pole: Optional[str] = None
    interlocutor: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class DataSourceCreate(BaseModel):
    """Payload required to create a data source configuration."""

    label: str
    source_type: str
    client_id: Optional[str] = None
    url: Optional[str] = None
    enabled: bool = True
    config: Optional[Dict[str, Any]] = None


class DataSourceUpdate(BaseModel):
    """Partial payload for updating a data source."""

    label: Optional[str] = None
    url: Optional[str] = None
    enabled: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None
