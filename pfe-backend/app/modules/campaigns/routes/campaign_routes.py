"""Campaigns HTTP routes — accessible to all authenticated users (no admin required)."""
from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends

from app.core.auth import TokenData, require_auth
from app.modules.campaigns.controllers.campaign_controller import (
    get_campaigns,
    get_targets,
    run_campaign_scoring,
)
from app.modules.campaigns.types.campaign_types import CampaignScoreRequest

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])


@router.get("")
def list_campaigns(user: TokenData = Depends(require_auth)) -> List[Dict[str, Any]]:
    """List all Salesforce campaigns."""
    return get_campaigns()


@router.get("/{campaign_id}/targets")
def campaign_targets(
    campaign_id: str,
    user: TokenData = Depends(require_auth),
) -> Dict[str, Any]:
    """Return all client targets for a campaign."""
    return get_targets(campaign_id)


@router.post("/{campaign_id}/score")
def score_targets(
    campaign_id: str,
    body: CampaignScoreRequest,
    user: TokenData = Depends(require_auth),
) -> Dict[str, Any]:
    """Batch-score selected campaign targets for a given product and rank them."""
    return run_campaign_scoring(campaign_id, body.account_ids, body.product_id, user.name)


@router.get("/cache/stats")
def cache_stats(user: TokenData = Depends(require_auth)) -> Dict[str, Any]:
    """Return scoring cache statistics."""
    from app.services.scoring.scoring_cache_service import scoring_cache
    return scoring_cache.stats()
