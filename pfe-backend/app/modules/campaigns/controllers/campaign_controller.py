"""Campaigns controller — orchestrates service calls for HTTP endpoints."""
from __future__ import annotations

import logging
from typing import Any, Dict, List

from app.modules.campaigns.services.campaign_scoring_service import score_campaign_targets

logger = logging.getLogger(__name__)


def get_campaigns() -> List[Dict[str, Any]]:
    from app.modules.admin.services.admin_services import list_campaigns
    return list_campaigns()


def get_targets(campaign_id: str) -> Dict[str, Any]:
    from app.modules.admin.services.admin_services import get_campaign_targets
    return get_campaign_targets(campaign_id)


def run_campaign_scoring(
    campaign_id: str,
    account_ids: List[str],
    product_id: str,
    user_name: str,
) -> Dict[str, Any]:
    logger.info(
        "Campaign scoring by %s: campaign=%s product=%s clients=%d",
        user_name, campaign_id, product_id, len(account_ids),
    )
    return score_campaign_targets(account_ids, product_id)
