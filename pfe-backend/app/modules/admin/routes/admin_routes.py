"""Admin HTTP routes — receive requests, validate schemas, delegate to controller."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends

from app.core.auth import TokenData, require_admin
from app.core.references import AdminRoutePrefix
from app.modules.admin.controllers import admin_controller as ctrl
from app.modules.admin.types.admin_types import (
    CampaignCreate, CampaignUpdate,
    ChoiceCreate, ChoiceUpdate,
    CriterionCreate, CriterionUpdate,
    DataSourceCreate, DataSourceUpdate,
    ProductCreate, ProductUpdate,
)

router = APIRouter(prefix=AdminRoutePrefix.ROOT, tags=["admin"])

_admin = Depends(require_admin)

# ── Products ──────────────────────────────────────────────────────────────────

@router.get("/products")
def list_products(_: TokenData = _admin) -> List[Dict[str, Any]]:
    """Return all products."""
    return ctrl.get_products()


@router.post("/products", status_code=201)
def create_product(body: ProductCreate, _: TokenData = _admin) -> Dict[str, Any]:
    """Create a product."""
    return ctrl.post_product(body.name)


@router.put("/products/{product_id}")
def update_product(product_id: str, body: ProductUpdate, _: TokenData = _admin) -> Dict[str, Any]:
    """Update a product."""
    return ctrl.put_product(product_id, body.name)


@router.delete("/products/{product_id}", status_code=204)
def delete_product(product_id: str, _: TokenData = _admin) -> None:
    """Delete a product and its criteria."""
    ctrl.remove_product(product_id)


# ── Criteria ──────────────────────────────────────────────────────────────────

@router.get("/products/{product_id}/criteria")
def list_criteria(product_id: str, _: TokenData = _admin) -> List[Dict[str, Any]]:
    """Return criteria for a product."""
    return ctrl.get_criteria(product_id)


@router.post("/products/{product_id}/criteria", status_code=201)
def create_criterion(product_id: str, body: CriterionCreate, _: TokenData = _admin) -> Dict[str, Any]:
    """Create a criterion under a product."""
    return ctrl.post_criterion(product_id, body.model_dump())


@router.put("/criteria/{criterion_id}")
def update_criterion(criterion_id: str, body: CriterionUpdate, _: TokenData = _admin) -> Dict[str, Any]:
    """Update a criterion."""
    return ctrl.put_criterion(criterion_id, body.model_dump(exclude_none=True))


@router.delete("/criteria/{criterion_id}", status_code=204)
def delete_criterion(criterion_id: str, _: TokenData = _admin) -> None:
    """Delete a criterion and its choices."""
    ctrl.remove_criterion(criterion_id)


# ── Choices ───────────────────────────────────────────────────────────────────

@router.get("/criteria/{criterion_id}/choices")
def list_choices(criterion_id: str, _: TokenData = _admin) -> List[Dict[str, Any]]:
    """Return choices for a criterion."""
    return ctrl.get_choices(criterion_id)


@router.post("/criteria/{criterion_id}/choices", status_code=201)
def create_choice(criterion_id: str, body: ChoiceCreate, _: TokenData = _admin) -> Dict[str, Any]:
    """Create a choice under a criterion."""
    return ctrl.post_choice(criterion_id, body.model_dump())


@router.put("/choices/{choice_id}")
def update_choice(choice_id: str, body: ChoiceUpdate, _: TokenData = _admin) -> Dict[str, Any]:
    """Update a choice."""
    return ctrl.put_choice(choice_id, body.model_dump(exclude_none=True))


@router.delete("/choices/{choice_id}", status_code=204)
def delete_choice(choice_id: str, _: TokenData = _admin) -> None:
    """Delete a choice."""
    ctrl.remove_choice(choice_id)


# ── Campaigns ─────────────────────────────────────────────────────────────────

@router.get("/campaigns")
def list_campaigns(_: TokenData = _admin) -> List[Dict[str, Any]]:
    """Return all campaigns."""
    return ctrl.get_campaigns()


@router.post("/campaigns", status_code=201)
def create_campaign(body: CampaignCreate, _: TokenData = _admin) -> Dict[str, Any]:
    """Create a campaign."""
    return ctrl.post_campaign(body.model_dump())


@router.put("/campaigns/{campaign_id}")
def update_campaign(campaign_id: str, body: CampaignUpdate, _: TokenData = _admin) -> Dict[str, Any]:
    """Update a campaign."""
    return ctrl.put_campaign(campaign_id, body.model_dump(exclude_none=True))


@router.delete("/campaigns/{campaign_id}", status_code=204)
def delete_campaign(campaign_id: str, _: TokenData = _admin) -> None:
    """Delete a campaign."""
    ctrl.remove_campaign(campaign_id)


@router.get("/campaigns/{campaign_id}/targets")
def get_campaign_targets(campaign_id: str, _: TokenData = _admin) -> Dict[str, Any]:
    """Return targets for a campaign."""
    return ctrl.get_campaign_targets(campaign_id)


# ── Sources ───────────────────────────────────────────────────────────────────

@router.get("/sources")
def list_sources(client_id: Optional[str] = None, _: TokenData = _admin) -> List[Dict[str, Any]]:
    """Return data sources."""
    return ctrl.get_sources(client_id)


@router.post("/sources", status_code=201)
def create_source(body: DataSourceCreate, _: TokenData = _admin) -> Dict[str, Any]:
    """Create a data source."""
    return ctrl.post_source(body.model_dump())


@router.put("/sources/{source_id}")
def update_source(source_id: str, body: DataSourceUpdate, _: TokenData = _admin) -> Dict[str, Any]:
    """Update a data source."""
    return ctrl.put_source(source_id, body.model_dump(exclude_none=True))


@router.delete("/sources/{source_id}", status_code=204)
def delete_source(source_id: str, _: TokenData = _admin) -> None:
    """Delete a data source."""
    ctrl.remove_source(source_id)


# ── Document routing ──────────────────────────────────────────────────────────

@router.get("/document-routing")
def get_document_routing(_: TokenData = _admin) -> Dict[str, Any]:
    """Show the document auto-classification cache."""
    return ctrl.get_document_routing()


@router.delete("/document-routing/cache", status_code=204)
def clear_routing_cache(_: TokenData = _admin) -> None:
    """Clear the document routing cache to force re-classification."""
    ctrl.clear_document_routing_cache()


# ── Role management ───────────────────────────────────────────────────────────

@router.get("/users")
def list_users(_: TokenData = _admin) -> List[Dict[str, Any]]:
    """List all Keycloak users with their admin status."""
    return ctrl.get_users()


@router.post("/users/{user_id}/make-admin", status_code=204)
def make_admin(user_id: str, _: TokenData = _admin) -> None:
    """Grant the admin role to a user."""
    ctrl.assign_admin_role(user_id)


@router.delete("/users/{user_id}/remove-admin", status_code=204)
def remove_admin(user_id: str, current: TokenData = _admin) -> None:
    """Revoke the admin role from a user."""
    ctrl.revoke_admin_role(user_id, current.sub)
