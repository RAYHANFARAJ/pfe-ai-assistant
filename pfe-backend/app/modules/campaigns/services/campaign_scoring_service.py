"""Campaign scoring service — scores multiple clients for a single product.

Flow per client:
  1. Cache hit  → return instantly (result from a previous full scoring)
  2. Cache miss → run FULL scoring pipeline (web crawl + LLM), save to cache
"""
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

_MAX_PARALLEL = 3


def score_campaign_targets(
    account_ids: List[str],
    product_id: str,
) -> Dict[str, Any]:
    """Score all account_ids for one product. Returns clients ranked by score."""
    results: List[Dict[str, Any]] = []

    with ThreadPoolExecutor(max_workers=_MAX_PARALLEL) as ex:
        future_to_id = {
            ex.submit(_score_one, cid, product_id): cid
            for cid in account_ids
        }
        for fut in as_completed(future_to_id):
            cid = future_to_id[fut]
            try:
                result = fut.result(timeout=300)
                results.append({"client_id": cid, "status": "success", **result})
            except Exception as exc:
                logger.warning("Scoring failed for client %s: %s", cid, exc)
                results.append({"client_id": cid, "status": "failed", "error": str(exc)})

    results.sort(
        key=lambda r: (r.get("summary") or {}).get("normalized_score", 0),
        reverse=True,
    )
    succeeded = [r for r in results if r["status"] == "success"]
    failed    = [r for r in results if r["status"] == "failed"]
    cached    = [r for r in succeeded if r.get("cache_hit")]

    return {
        "product_id": product_id,
        "total":      len(account_ids),
        "succeeded":  len(succeeded),
        "failed":     len(failed),
        "from_cache": len(cached),
        "results":    results,
    }


def _score_one(client_id: str, product_id: str) -> Dict[str, Any]:
    from app.services.scoring.scoring_cache_service import scoring_cache

    # ── 1. Cache hit — return immediately ────────────────────────────────────
    cached = scoring_cache.get(client_id, product_id)
    if cached:
        return cached

    # ── 2. Cache miss — run full pipeline and store result ───────────────────
    from app.services.scoring.scoring_pipeline_service import ScoringPipelineService
    result = ScoringPipelineService().run(client_id=client_id, product_id=product_id)

    if "error" not in result:
        scoring_cache.set(client_id, product_id, result)

    return result
