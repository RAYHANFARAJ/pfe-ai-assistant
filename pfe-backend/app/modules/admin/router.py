from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import TokenData, require_admin
from app.modules.admin import service as svc
from app.services.keycloak_admin_service import KeycloakAdminService

_kc = KeycloakAdminService()
from app.modules.admin.models import (
    CampaignCreate, CampaignUpdate,
    ChoiceCreate, ChoiceUpdate,
    CriterionCreate, CriterionUpdate,
    ProductCreate, ProductUpdate,
    DataSourceCreate, DataSourceUpdate,
)

router = APIRouter(prefix="/api/admin", tags=["admin"])

# Every route in this module requires the 'admin' role.
_admin = Depends(require_admin)


# ── Products ──────────────────────────────────────────────────────────────────

@router.get("/products")
def list_products(_: TokenData = _admin) -> List[Dict[str, Any]]:
    return svc.list_products()


@router.post("/products", status_code=201)
def create_product(body: ProductCreate, _: TokenData = _admin) -> Dict[str, Any]:
    return svc.create_product(body.name)


@router.put("/products/{product_id}")
def update_product(product_id: str, body: ProductUpdate, _: TokenData = _admin) -> Dict[str, Any]:
    result = svc.update_product(product_id, body.name)
    if not result:
        raise HTTPException(404, f"Product '{product_id}' not found.")
    return result


@router.delete("/products/{product_id}", status_code=204)
def delete_product(product_id: str, _: TokenData = _admin) -> None:
    if not svc.delete_product(product_id):
        raise HTTPException(404, f"Product '{product_id}' not found.")


# ── Criteria ──────────────────────────────────────────────────────────────────

@router.get("/products/{product_id}/criteria")
def list_criteria(product_id: str, _: TokenData = _admin) -> List[Dict[str, Any]]:
    return svc.list_criteria(product_id)


@router.post("/products/{product_id}/criteria", status_code=201)
def create_criterion(product_id: str, body: CriterionCreate, _: TokenData = _admin) -> Dict[str, Any]:
    result = svc.create_criterion(product_id, body.model_dump())
    if not result:
        raise HTTPException(404, f"Product '{product_id}' not found.")
    return result


@router.put("/criteria/{criterion_id}")
def update_criterion(criterion_id: str, body: CriterionUpdate, _: TokenData = _admin) -> Dict[str, Any]:
    result = svc.update_criterion(criterion_id, body.model_dump(exclude_none=True))
    if not result:
        raise HTTPException(404, f"Criterion '{criterion_id}' not found.")
    return result


@router.delete("/criteria/{criterion_id}", status_code=204)
def delete_criterion(criterion_id: str, _: TokenData = _admin) -> None:
    if not svc.delete_criterion(criterion_id):
        raise HTTPException(404, f"Criterion '{criterion_id}' not found.")


# ── Choices ───────────────────────────────────────────────────────────────────

@router.get("/criteria/{criterion_id}/choices")
def list_choices(criterion_id: str, _: TokenData = _admin) -> List[Dict[str, Any]]:
    return svc.list_choices(criterion_id)


@router.post("/criteria/{criterion_id}/choices", status_code=201)
def create_choice(criterion_id: str, body: ChoiceCreate, _: TokenData = _admin) -> Dict[str, Any]:
    result = svc.create_choice(criterion_id, body.model_dump())
    if not result:
        raise HTTPException(404, f"Criterion '{criterion_id}' not found.")
    return result


@router.put("/choices/{choice_id}")
def update_choice(choice_id: str, body: ChoiceUpdate, _: TokenData = _admin) -> Dict[str, Any]:
    result = svc.update_choice(choice_id, body.model_dump(exclude_none=True))
    if not result:
        raise HTTPException(404, f"Choice '{choice_id}' not found.")
    return result


@router.delete("/choices/{choice_id}", status_code=204)
def delete_choice(choice_id: str, _: TokenData = _admin) -> None:
    if not svc.delete_choice(choice_id):
        raise HTTPException(404, f"Choice '{choice_id}' not found.")


# ── Campaigns ─────────────────────────────────────────────────────────────────

@router.get("/campaigns")
def list_campaigns(_: TokenData = _admin) -> List[Dict[str, Any]]:
    return svc.list_campaigns()


@router.post("/campaigns", status_code=201)
def create_campaign(body: CampaignCreate, _: TokenData = _admin) -> Dict[str, Any]:
    return svc.create_campaign(body.model_dump())


@router.put("/campaigns/{campaign_id}")
def update_campaign(campaign_id: str, body: CampaignUpdate, _: TokenData = _admin) -> Dict[str, Any]:
    result = svc.update_campaign(campaign_id, body.model_dump(exclude_none=True))
    if not result:
        raise HTTPException(404, f"Campaign '{campaign_id}' not found.")
    return result


@router.delete("/campaigns/{campaign_id}", status_code=204)
def delete_campaign(campaign_id: str, _: TokenData = _admin) -> None:
    if not svc.delete_campaign(campaign_id):
        raise HTTPException(404, f"Campaign '{campaign_id}' not found.")


@router.get("/campaigns/{campaign_id}/targets")
def get_campaign_targets(campaign_id: str, _: TokenData = _admin) -> Dict[str, Any]:
    return svc.get_campaign_targets(campaign_id)


# ── Data Sources ──────────────────────────────────────────────────────────────

@router.get("/sources")
def list_sources(client_id: Optional[str] = None, _: TokenData = _admin) -> List[Dict[str, Any]]:
    return svc.list_sources(client_id)


@router.post("/sources", status_code=201)
def create_source(body: DataSourceCreate, _: TokenData = _admin) -> Dict[str, Any]:
    return svc.create_source(body.model_dump())


@router.put("/sources/{source_id}")
def update_source(source_id: str, body: DataSourceUpdate, _: TokenData = _admin) -> Dict[str, Any]:
    result = svc.update_source(source_id, body.model_dump(exclude_none=True))
    if not result:
        raise HTTPException(404, f"Source '{source_id}' not found.")
    return result


@router.delete("/sources/{source_id}", status_code=204)
def delete_source(source_id: str, _: TokenData = _admin) -> None:
    if not svc.delete_source(source_id):
        raise HTTPException(404, f"Source '{source_id}' not found.")


# ── Document routing ──────────────────────────────────────────────────────────

@router.get("/document-routing")
def get_document_routing(_: TokenData = _admin) -> Dict[str, Any]:
    """Show the auto-classification cache: which document → which client."""
    from app.services.documents.document_router import classify_all_orphans
    mapping = classify_all_orphans()
    return {"routing": mapping, "total": len(mapping)}


@router.delete("/document-routing/cache", status_code=204)
def clear_routing_cache(_: TokenData = _admin) -> None:
    from app.services.documents.document_router import clear_cache
    clear_cache()


# ── Role management (Keycloak) ────────────────────────────────────────────────

@router.get("/users")
def list_users(_: TokenData = _admin) -> List[Dict[str, Any]]:
    """List all Keycloak users with their admin status."""
    try:
        return _kc.list_users()
    except Exception as exc:
        raise HTTPException(503, f"Keycloak unavailable: {exc}")


@router.post("/users/{user_id}/make-admin", status_code=204)
def make_admin(user_id: str, _: TokenData = _admin) -> None:
    """Assign the 'admin' role to a user."""
    try:
        _kc.assign_admin(user_id)
    except Exception as exc:
        raise HTTPException(503, f"Failed to assign role: {exc}")


@router.delete("/users/{user_id}/remove-admin", status_code=204)
def remove_admin(user_id: str, current: TokenData = _admin) -> None:
    """Remove the 'admin' role from a user (cannot remove your own admin)."""
    if current.sub == user_id:
        raise HTTPException(400, "You cannot remove your own admin role.")
    try:
        _kc.remove_admin(user_id)
    except Exception as exc:
        raise HTTPException(503, f"Failed to remove role: {exc}")
