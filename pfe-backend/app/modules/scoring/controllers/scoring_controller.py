"""Scoring controller — orchestrates service calls for HTTP endpoints."""
from __future__ import annotations

import logging
from typing import Any, Dict, List

from app.modules.scoring.services.scoring_pipeline_service import ScoringPipelineService
from app.modules.scoring.services.batch_scoring_service import BatchScoringService

logger = logging.getLogger(__name__)


def run_single_scoring(client_id: str, product_id: str, user_name: str, user_email: str) -> Dict[str, Any]:
    """Run the scoring pipeline for one product and one client."""
    logger.info("Scoring request by %s (%s): client=%s product=%s", user_name, user_email, client_id, product_id)
    return ScoringPipelineService().run(client_id=client_id, product_id=product_id)


def run_batch_scoring(
    client_id: str,
    document_ids: List[str],
    inline_documents: List[Dict[str, str]],
    user_name: str,
    user_email: str,
) -> Dict[str, Any]:
    """Run the scoring pipeline for all products for a client."""
    logger.info("Batch scoring request by %s (%s): client=%s", user_name, user_email, client_id)
    return BatchScoringService().run_batch(
        client_id=client_id,
        document_ids=document_ids,
        inline_documents=inline_documents,
    )
