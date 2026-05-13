"""Admin controller — orchestrates service calls and raises HTTP exceptions.

Routes call this; it never touches the database directly.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import HTTPException

from app.core.references import AdminResourceLabels
from app.modules.admin import services as svc  # package re-export
from app.services.keycloak_admin_service import KeycloakAdminService

_kc = KeycloakAdminService()


# ── Products ──────────────────────────────────────────────────────────────────

def get_products() -> List[Dict[str, Any]]:
    """Return all products."""
    return svc.list_products()


def post_product(name: str) -> Dict[str, Any]:
    """Create and return a new product."""
    return svc.create_product(name)


def put_product(product_id: str, name: str) -> Dict[str, Any]:
    """Update product name; raises 404 if not found."""
    result = svc.update_product(product_id, name)
    if not result:
        raise HTTPException(404, f"{AdminResourceLabels.PRODUCT} '{product_id}' not found.")
    return result


def remove_product(product_id: str) -> None:
    """Delete a product; raises 404 if not found."""
    if not svc.delete_product(product_id):
        raise HTTPException(404, f"{AdminResourceLabels.PRODUCT} '{product_id}' not found.")


# ── Criteria ──────────────────────────────────────────────────────────────────

def get_criteria(product_id: str) -> List[Dict[str, Any]]:
    """Return criteria for a product."""
    return svc.list_criteria(product_id)


def post_criterion(product_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a criterion; raises 404 if the product does not exist."""
    result = svc.create_criterion(product_id, data)
    if not result:
        raise HTTPException(404, f"{AdminResourceLabels.PRODUCT} '{product_id}' not found.")
    return result


def put_criterion(criterion_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Update criterion fields; raises 404 if not found."""
    result = svc.update_criterion(criterion_id, updates)
    if not result:
        raise HTTPException(404, f"{AdminResourceLabels.CRITERION} '{criterion_id}' not found.")
    return result


def remove_criterion(criterion_id: str) -> None:
    """Delete a criterion; raises 404 if not found."""
    if not svc.delete_criterion(criterion_id):
        raise HTTPException(404, f"{AdminResourceLabels.CRITERION} '{criterion_id}' not found.")


# ── Choices ───────────────────────────────────────────────────────────────────

def get_choices(criterion_id: str) -> List[Dict[str, Any]]:
    """Return choices for a criterion."""
    return svc.list_choices(criterion_id)


def post_choice(criterion_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a choice; raises 404 if the criterion does not exist."""
    result = svc.create_choice(criterion_id, data)
    if not result:
        raise HTTPException(404, f"{AdminResourceLabels.CRITERION} '{criterion_id}' not found.")
    return result


def put_choice(choice_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Update choice fields; raises 404 if not found."""
    result = svc.update_choice(choice_id, updates)
    if not result:
        raise HTTPException(404, f"{AdminResourceLabels.CHOICE} '{choice_id}' not found.")
    return result


def remove_choice(choice_id: str) -> None:
    """Delete a choice; raises 404 if not found."""
    if not svc.delete_choice(choice_id):
        raise HTTPException(404, f"{AdminResourceLabels.CHOICE} '{choice_id}' not found.")


# ── Campaigns ─────────────────────────────────────────────────────────────────

def get_campaigns() -> List[Dict[str, Any]]:
    """Return all campaigns from the verse index merged with local campaigns."""
    return svc.list_campaigns()


def post_campaign(data: Dict[str, Any]) -> Dict[str, Any]:
    """Create and persist a local campaign."""
    return svc.create_campaign(data)


def put_campaign(campaign_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Update a local campaign; raises 404 if not found."""
    result = svc.update_campaign(campaign_id, updates)
    if not result:
        raise HTTPException(404, f"{AdminResourceLabels.CAMPAIGN} '{campaign_id}' not found.")
    return result


def remove_campaign(campaign_id: str) -> None:
    """Delete a local campaign; raises 404 if not found."""
    if not svc.delete_campaign(campaign_id):
        raise HTTPException(404, f"{AdminResourceLabels.CAMPAIGN} '{campaign_id}' not found.")


def get_campaign_targets(campaign_id: str) -> Dict[str, Any]:
    """Return targets for a campaign from the verse index."""
    return svc.get_campaign_targets(campaign_id)


# ── Sources ───────────────────────────────────────────────────────────────────

def get_sources(client_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return data sources, optionally filtered by client_id."""
    return svc.list_sources(client_id)


def post_source(data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a data source configuration."""
    return svc.create_source(data)


def put_source(source_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Update a source; raises 404 if not found."""
    result = svc.update_source(source_id, updates)
    if not result:
        raise HTTPException(404, f"{AdminResourceLabels.SOURCE} '{source_id}' not found.")
    return result


def remove_source(source_id: str) -> None:
    """Delete a source; raises 404 if not found."""
    if not svc.delete_source(source_id):
        raise HTTPException(404, f"{AdminResourceLabels.SOURCE} '{source_id}' not found.")


# ── Document routing ──────────────────────────────────────────────────────────

def get_document_routing() -> Dict[str, Any]:
    """Return the auto-classification cache for orphan documents."""
    from app.services.documents.document_router import classify_all_orphans
    mapping = classify_all_orphans()
    return {"routing": mapping, "total": len(mapping)}


def clear_document_routing_cache() -> None:
    """Force re-classification of all orphan documents."""
    from app.services.documents.document_router import clear_cache
    clear_cache()


# ── Role management ───────────────────────────────────────────────────────────

def get_users() -> List[Dict[str, Any]]:
    """Return all Keycloak users with their admin role status."""
    try:
        return _kc.list_users()
    except Exception as exc:
        raise HTTPException(503, f"Keycloak unavailable: {exc}")


def assign_admin_role(user_id: str) -> None:
    """Assign the admin role to a Keycloak user."""
    try:
        _kc.assign_admin(user_id)
    except Exception as exc:
        raise HTTPException(503, f"Failed to assign role: {exc}")


def revoke_admin_role(user_id: str, requesting_user_id: str) -> None:
    """Remove the admin role; blocks self-revocation."""
    if requesting_user_id == user_id:
        raise HTTPException(400, "You cannot remove your own admin role.")
    try:
        _kc.remove_admin(user_id)
    except Exception as exc:
        raise HTTPException(503, f"Failed to remove role: {exc}")
