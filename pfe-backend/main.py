from __future__ import annotations

import contextlib
import logging
from typing import Optional

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from elastic_transport import ConnectionError as ESConnectionError

from app.mcp.server import mcp
from app.services.scoring.scoring_pipeline_service import ScoringPipelineService
from app.services.elasticsearch.account_reference_service import AccountReferenceService
from app.tools.es_client_tool import ESClientTool
from app.core.auth import TokenData, optional_auth, require_auth

logger = logging.getLogger(__name__)

app = FastAPI(title="PFE Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ScoringRequest(BaseModel):
    client_id: str
    product_id: str


# ------------------------------------------------------------------
# Global exception handlers
# ------------------------------------------------------------------

@app.exception_handler(ESConnectionError)
async def es_connection_error_handler(request: Request, exc: ESConnectionError):
    return JSONResponse(
        status_code=503,
        content={
            "error": "elasticsearch_unavailable",
            "detail": "Elasticsearch cluster is unreachable.",
        },
    )


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": "internal_error", "detail": str(exc)},
    )


# ------------------------------------------------------------------
# Public routes (no auth required)
# ------------------------------------------------------------------

@app.get("/")
def root():
    return {"message": "FastAPI backend is running"}


@app.get("/api/health")
def health():
    return {"status": "ok"}


# ------------------------------------------------------------------
# Authenticated routes
# ------------------------------------------------------------------

@app.get("/api/me")
def me(user: TokenData = Depends(require_auth)):
    """Returns the identity of the currently authenticated user."""
    return {
        "sub":        user.sub,
        "name":       user.name,
        "email":      user.email,
        "username":   user.username,
        "given_name": user.given_name,
        "roles":      user.roles,
    }


@app.post("/api/scoring/agent-demo")
def run_agent_demo(
    payload: ScoringRequest,
    user: TokenData = Depends(require_auth),
):
    logger.info("Scoring request by %s (%s): client=%s product=%s",
                user.name, user.email, payload.client_id, payload.product_id)
    service = ScoringPipelineService()
    return service.run(client_id=payload.client_id, product_id=payload.product_id)


@app.post("/api/accounts/build-reference")
def build_account_reference(user: TokenData = Depends(require_auth)):
    service = AccountReferenceService()
    return service.run()


# ------------------------------------------------------------------
# Debug routes (auth optional — works with or without token)
# ------------------------------------------------------------------

@app.get("/api/products")
def list_products(user: TokenData = Depends(require_auth)):
    """Return all available products with criteria count."""
    from app.tools.es_reference_tool import ESReferenceTool
    ref = ESReferenceTool()
    products = ref._load_json(ref.products_path)
    all_criteria = ref._load_json(ref.criteria_path)
    counts = {}
    for c in all_criteria:
        counts[c["product_id"]] = counts.get(c["product_id"], 0) + 1
    return [{"id": p["id"], "name": p["name"], "criteria_count": counts.get(p["id"], 0)} for p in products]


@app.get("/api/accounts/search")
def search_accounts(
    q: str = "",
    user: TokenData = Depends(require_auth),
):
    """Search clients by name or ID — returns up to 10 matches."""
    tool = ESClientTool()
    return tool.search(q)


@app.get("/api/debug/es/health")
def debug_es_health(user: Optional[TokenData] = Depends(optional_auth)):
    tool = ESClientTool()
    return tool.es_health()


@app.get("/api/debug/es/client/{client_id}")
def debug_es_client(client_id: str, user: Optional[TokenData] = Depends(optional_auth)):
    tool = ESClientTool()
    return tool.debug_lookup(client_id)


# ------------------------------------------------------------------
# MCP
# ------------------------------------------------------------------

@contextlib.asynccontextmanager
async def lifespan(app_instance: FastAPI):
    async with mcp.session_manager.run():
        yield


app.router.lifespan_context = lifespan
app.mount("/mcp", mcp.streamable_http_app())
