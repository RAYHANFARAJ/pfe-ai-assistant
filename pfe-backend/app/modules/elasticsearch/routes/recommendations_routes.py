"""Recommendations — aggregates the scoring cache into ranked opportunities."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, Depends

from app.core.auth import TokenData, require_auth

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])

_CACHE_FILE = Path("output") / "scoring_cache.json"


@router.get("")
def get_recommendations(user: TokenData = Depends(require_auth)) -> Dict[str, Any]:
    """
    Read the scoring cache and return:
    - Top client+product opportunities ranked by score
    - Per-client summary (how many products eligible)
    - Per-product summary (how many clients eligible)
    """
    if not _CACHE_FILE.exists():
        return {"clients": [], "by_product": [], "top_matches": [], "stats": {}}

    try:
        raw = json.loads(_CACHE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"clients": [], "by_product": [], "top_matches": [], "stats": {}}

    # ── Parse all cache entries ──────────────────────────────────────────────
    entries = []
    for key, entry in raw.items():
        result = entry.get("result", entry)   # handle both wrapped and flat
        if not result:
            continue
        summary = result.get("summary", {})
        client  = result.get("client", {})
        product = result.get("product", {})
        if not client.get("client_name") or not product.get("product_id"):
            continue
        entries.append({
            "client_id":         client.get("client_id", ""),
            "client_name":       client.get("client_name", ""),
            "sector":            client.get("sector", ""),
            "product_id":        product.get("product_id", ""),
            "product_name":      product.get("product_name", ""),
            "eligibility":       summary.get("eligibility_status", "not_eligible"),
            "normalized_score":  summary.get("normalized_score", 0) or 0,
            "total_score":       summary.get("total_score", 0),
            "max_score":         summary.get("max_score", 1),
            "cached_at":         entry.get("cached_at", ""),
        })

    if not entries:
        return {"clients": [], "by_product": [], "top_matches": [], "stats": {}}

    # ── Top matches (eligible + to_review, sorted by score) ─────────────────
    top = sorted(
        [e for e in entries if e["eligibility"] in ("eligible", "to_review")],
        key=lambda x: (x["eligibility"] == "eligible", x["normalized_score"]),
        reverse=True,
    )[:30]

    # ── Per-client summary ───────────────────────────────────────────────────
    clients_map: Dict[str, Dict] = {}
    for e in entries:
        cid = e["client_id"]
        if cid not in clients_map:
            clients_map[cid] = {
                "client_id":   cid,
                "client_name": e["client_name"],
                "sector":      e["sector"],
                "eligible":    [],
                "to_review":   [],
                "not_eligible": [],
                "total":       0,
            }
        clients_map[cid]["total"] += 1
        clients_map[cid][e["eligibility"]].append({
            "product_id":   e["product_id"],
            "product_name": e["product_name"],
            "score":        round(e["normalized_score"] * 100),
        })

    clients = sorted(
        clients_map.values(),
        key=lambda c: (len(c["eligible"]), len(c["to_review"])),
        reverse=True,
    )

    # ── Per-product summary ──────────────────────────────────────────────────
    products_map: Dict[str, Dict] = {}
    for e in entries:
        pid = e["product_id"]
        if pid not in products_map:
            products_map[pid] = {
                "product_id":   pid,
                "product_name": e["product_name"],
                "eligible":     0,
                "to_review":    0,
                "not_eligible": 0,
                "total":        0,
            }
        products_map[pid]["total"]      += 1
        products_map[pid][e["eligibility"]] += 1

    by_product = sorted(
        products_map.values(),
        key=lambda p: (p["eligible"], p["to_review"]),
        reverse=True,
    )

    # ── Global stats ─────────────────────────────────────────────────────────
    stats = {
        "total_scorings":  len(entries),
        "unique_clients":  len(clients_map),
        "unique_products": len(products_map),
        "eligible_matches": sum(1 for e in entries if e["eligibility"] == "eligible"),
        "to_review_matches": sum(1 for e in entries if e["eligibility"] == "to_review"),
    }

    return {
        "top_matches": top,
        "clients":     clients,
        "by_product":  by_product,
        "stats":       stats,
    }
