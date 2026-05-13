"""Module registry — registers every module's router into the FastAPI application.

Adding a new module: create its routes file then add one include_router line here.
main.py never needs to know the internal route structure of any module.
"""
from __future__ import annotations

from fastapi import FastAPI


def register_modules(app: FastAPI) -> None:
    """Include every module router into the application at startup."""

    from app.modules.elasticsearch.routes.elasticsearch_routes import router as es_router
    app.include_router(es_router)

    from app.modules.admin.routes.admin_routes import router as admin_router
    app.include_router(admin_router)

    from app.modules.scoring.routes.scoring_routes import router as scoring_router
    app.include_router(scoring_router)

    from app.modules.documents.routes.document_routes import router as documents_router
    app.include_router(documents_router)

    from app.modules.reports.routes.report_routes import router as reports_router
    app.include_router(reports_router)

    from app.modules.campaigns.routes.campaign_routes import router as campaigns_router
    app.include_router(campaigns_router)

    from app.modules.scoring.routes.cache_routes import router as cache_router
    app.include_router(cache_router)

    from app.modules.elasticsearch.routes.recommendations_routes import router as reco_router
    app.include_router(reco_router)
