from __future__ import annotations

import contextlib
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from elastic_transport import ConnectionError as ESConnectionError

from app.core.auth import TokenData, require_auth
from app.mcp.server import mcp
from app.modules import register_modules
from app.services.scoring.scoring_pipeline_service import ScoringPipelineService
from app.services.scoring.batch_scoring_service import BatchScoringService
from app.services.documents.document_extractor import extract_and_store, get_sources
from fastapi import UploadFile, File
from typing import List as TList

from fastapi import Depends

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
# Scoring — will move to modules/scoring in the next refactor step
# ------------------------------------------------------------------

class ScoringRequest(BaseModel):
    client_id: str
    product_id: str


class DocumentPayload(BaseModel):
    label: str
    text: str


class BatchScoringRequest(BaseModel):
    client_id: str
    document_ids: TList[str] = []          # legacy — kept for compat
    documents: TList[DocumentPayload] = [] # preferred — inline text, no server state


@app.post("/api/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    user: TokenData = Depends(require_auth),
):
    """Upload a PDF or text document. Returns a doc_id to pass to /api/scoring/batch."""
    content = await file.read()
    try:
        from app.services.documents.document_extractor import _extract_text, _build_sections
        text = _extract_text(file.filename or "document", content)
        if not text.strip():
            return {"status": "error", "detail": "Could not extract text from file."}
        return {
            "status": "ok",
            "label":   file.filename,
            "text":    text,
            "chars":   len(text),
            "preview": text[:300].strip(),
        }
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@app.post("/api/scoring/batch")
def run_batch_scoring(
    payload: BatchScoringRequest,
    user: TokenData = Depends(require_auth),
):
    """
    Score all products for a client in one call.
    Crawls the client's sources once and evaluates every product in parallel.
    """
    logger.info(
        "Batch scoring request by %s (%s): client=%s",
        user.name, user.email, payload.client_id,
    )
    inline_docs = [{"label": d.label, "text": d.text} for d in payload.documents]
    return BatchScoringService().run_batch(
        client_id=payload.client_id,
        document_ids=payload.document_ids,
        inline_documents=inline_docs,
    )


@app.post("/api/scoring/agent-demo")
def run_agent_demo(
    payload: ScoringRequest,
    user: TokenData = Depends(require_auth),
):
    logger.info(
        "Scoring request by %s (%s): client=%s product=%s",
        user.name, user.email, payload.client_id, payload.product_id,
    )
    return ScoringPipelineService().run(
        client_id=payload.client_id,
        product_id=payload.product_id,
    )


# ------------------------------------------------------------------
# MCP
# ------------------------------------------------------------------

@contextlib.asynccontextmanager
async def lifespan(app_instance: FastAPI):
    async with mcp.session_manager.run():
        yield


app.router.lifespan_context = lifespan
app.mount("/mcp", mcp.streamable_http_app())
