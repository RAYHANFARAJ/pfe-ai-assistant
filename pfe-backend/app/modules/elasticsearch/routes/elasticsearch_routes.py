"""Elasticsearch HTTP routes — thin layer that delegates to the controller."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends

from app.core.auth import TokenData, optional_auth, require_auth
from app.core.references import ElasticsearchRoutePrefix
from app.modules.elasticsearch.controllers import elasticsearch_controller as ctrl

router = APIRouter()


@router.get(ElasticsearchRoutePrefix.ACCOUNTS + "/search")
def search_accounts(
    q:    str = "",
    name: str = "",
    user: TokenData = Depends(require_auth),
) -> List[Dict[str, Any]]:
    """Search clients by name or Salesforce ID.

    Accepts:
      ?q=<name or ID>       — unified search (default)
      ?name=<company name>  — explicit name search
    """
    query = name.strip() or q.strip()
    return ctrl.search_accounts(query)


@router.post(ElasticsearchRoutePrefix.ACCOUNTS + "/build-reference")
def build_account_reference(user: TokenData = Depends(require_auth)) -> Dict[str, Any]:
    """Rebuild the account reference index."""
    return ctrl.build_account_reference()


@router.get(ElasticsearchRoutePrefix.PRODUCTS)
def list_products(user: TokenData = Depends(require_auth)) -> List[Dict[str, Any]]:
    """Return all products with their criteria count."""
    return ctrl.get_products_with_criteria_count()


@router.get(ElasticsearchRoutePrefix.DEBUG + "/health")
def debug_es_health(user: Optional[TokenData] = Depends(optional_auth)) -> Dict[str, Any]:
    """Elasticsearch cluster connectivity check."""
    return ctrl.check_es_health()


@router.get(ElasticsearchRoutePrefix.DEBUG + "/client/{client_id}")
def debug_es_client(
    client_id: str,
    user: Optional[TokenData] = Depends(optional_auth),
) -> Dict[str, Any]:
    """Per-strategy lookup diagnostics for a Salesforce client ID."""
    return ctrl.debug_client_lookup(client_id)
