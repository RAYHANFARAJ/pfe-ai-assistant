from __future__ import annotations

import contextlib
import logging

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from elastic_transport import ConnectionError as ESConnectionError

from app.core.auth import TokenData, require_auth
from app.mcp.server import mcp
from app.modules import register_modules

logger = logging.getLogger(__name__)

app = FastAPI(title="PFE Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------
# Register autonomous modules (each owns its own routes)
# ------------------------------------------------------------------

register_modules(app)

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
# Infrastructure routes (health + identity — not domain logic)
# ------------------------------------------------------------------

@app.get("/")
def root():
    return {"message": "FastAPI backend is running"}


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/me")
def me(user: TokenData = Depends(require_auth)):
    return {
        "sub":        user.sub,
        "name":       user.name,
        "email":      user.email,
        "username":   user.username,
        "given_name": user.given_name,
        "roles":      user.roles,
    }


# ------------------------------------------------------------------
# MCP
# ------------------------------------------------------------------

@contextlib.asynccontextmanager
async def lifespan(app_instance: FastAPI):
    async with mcp.session_manager.run():
        yield


app.router.lifespan_context = lifespan
app.mount("/mcp", mcp.streamable_http_app())
