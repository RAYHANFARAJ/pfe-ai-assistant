"""Elasticsearch controller — orchestrates service calls and raises HTTP exceptions."""
from __future__ import annotations

from typing import Any, Dict, List

from app.modules.elasticsearch.business.client_tool import ESClientTool
from app.modules.elasticsearch.tools.reference_tool import ESReferenceTool
from app.modules.elasticsearch.services.account_service import AccountReferenceService


def search_accounts(query: str) -> List[Dict[str, Any]]:
    """Search Salesforce accounts by name or ID and return up to 10 matches."""
    return ESClientTool().search(query)


def build_account_reference() -> Dict[str, Any]:
    """Rebuild the account reference index from the raw Salesforce pipeline index."""
    return AccountReferenceService().run()


def get_products_with_criteria_count() -> List[Dict[str, Any]]:
    """Return all products annotated with their criteria count."""
    ref = ESReferenceTool()
    products = ref._load_json(ref._products_path)
    criteria = ref._load_json(ref._criteria_path)
    counts: Dict[str, int] = {}
    for c in criteria:
        counts[c["product_id"]] = counts.get(c["product_id"], 0) + 1
    return [
        {"id": p["id"], "name": p["name"], "criteria_count": counts.get(p["id"], 0)}
        for p in products
    ]


def check_es_health() -> Dict[str, Any]:
    """Return Elasticsearch cluster connectivity status."""
    return ESClientTool().health()


def debug_client_lookup(client_id: str) -> Dict[str, Any]:
    """Return per-strategy diagnostics for a Salesforce client ID."""
    return ESClientTool().debug_lookup(client_id)
