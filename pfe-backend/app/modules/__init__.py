from __future__ import annotations

from fastapi import FastAPI


def register_modules(app: FastAPI) -> None:
    """
    Register all autonomous modules into the FastAPI application.
    Each module exposes a router that is included here.
    main.py calls this once — it never needs to know what routes exist inside.
    """
    from app.modules.elasticsearch.router import router as es_router
    app.include_router(es_router)
