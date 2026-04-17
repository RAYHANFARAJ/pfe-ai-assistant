from __future__ import annotations

import contextlib

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from elastic_transport import ConnectionError as ESConnectionError

from app.mcp.server import mcp
from app.services.scoring.scoring_pipeline_service import ScoringPipelineService
from app.services.elasticsearch.account_reference_service import AccountReferenceService
from app.tools.es_client_tool import ESClientTool

app = FastAPI(title="PFE Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
            "detail": "Elasticsearch cluster is unreachable. Check host/network configuration.",
        },
    )


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": "internal_error", "detail": str(exc)},
    )


# ------------------------------------------------------------------
# Core routes
# ------------------------------------------------------------------

@app.get("/")
def root():
    return {"message": "FastAPI backend is running"}


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/scoring/agent-demo")
def run_agent_demo(payload: ScoringRequest):
    service = ScoringPipelineService()
    return service.run(client_id=payload.client_id, product_id=payload.product_id)


@app.post("/api/accounts/build-reference")
def build_account_reference():
    service = AccountReferenceService()
    return service.run()


# ------------------------------------------------------------------
# Debug routes  (use these to diagnose ES connectivity & data issues)
# ------------------------------------------------------------------

@app.get("/api/debug/es/health")
def debug_es_health():
    """Check Elasticsearch connectivity."""
    tool = ESClientTool()
    return tool.es_health()


@app.get("/api/debug/es/client/{client_id}")
def debug_es_client(client_id: str):
    """
    Run all lookup strategies for a client_id and return raw hit counts +
    field lists. Use this to understand why client data is not being retrieved.
    """
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
