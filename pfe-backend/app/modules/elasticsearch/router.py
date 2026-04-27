from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends

from app.core.auth import TokenData, optional_auth, require_auth
from app.modules.elasticsearch.services.account_service import AccountReferenceService
from app.modules.elasticsearch.services.xtra_service import XtraReferenceService
from app.modules.elasticsearch.tools.client_tool import ESClientTool
from app.modules.elasticsearch.tools.reference_tool import ESReferenceTool

logger = logging.getLogger(__name__)

router = APIRouter()


# ------------------------------------------------------------------
# Accounts — search and reference build
# ------------------------------------------------------------------

@router.get("/api/accounts/search")
def search_accounts(
    q: str = "",
    user: TokenData = Depends(require_auth),
):
    """Search clients by name or Salesforce ID — returns up to 10 matches."""
    return ESClientTool().search(q)


@router.post("/api/accounts/build-reference")
def build_account_reference(user: TokenData = Depends(require_auth)):
    """Rebuild the account reference index from the raw Salesforce pipeline index."""
    return AccountReferenceService().run()


# ------------------------------------------------------------------
# Products (reference data read from pre-built JSON files)
# ------------------------------------------------------------------

@router.get("/api/products")
def list_products(user: TokenData = Depends(require_auth)):
    """Return all available products with their criteria count."""
    ref = ESReferenceTool()
    products  = ref._load_json(ref._products_path)
    criteria  = ref._load_json(ref._criteria_path)
    counts: dict = {}
    for c in criteria:
        counts[c["product_id"]] = counts.get(c["product_id"], 0) + 1
    return [
        {"id": p["id"], "name": p["name"], "criteria_count": counts.get(p["id"], 0)}
        for p in products
    ]


# ------------------------------------------------------------------
# Debug / diagnostics
# ------------------------------------------------------------------

@router.get("/api/debug/es/health")
def debug_es_health(user: Optional[TokenData] = Depends(optional_auth)):
    """Connectivity check against the Elasticsearch cluster."""
    return ESClientTool().health()


@router.get("/api/debug/es/client/{client_id}")
def debug_es_client(
    client_id: str,
    user: Optional[TokenData] = Depends(optional_auth),
):
    """Return per-strategy lookup diagnostics for a given Salesforce client ID."""
    return ESClientTool().debug_lookup(client_id)
