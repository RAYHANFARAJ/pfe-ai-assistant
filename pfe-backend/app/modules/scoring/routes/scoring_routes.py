"""Scoring HTTP routes — receive requests and delegate to the controller."""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.core.auth import TokenData, require_auth
from app.modules.scoring.controllers.scoring_controller import run_single_scoring, run_batch_scoring
from app.modules.scoring.types.scoring_types import BatchScoringRequest, ScoringRequest

router = APIRouter(prefix="/api/scoring", tags=["scoring"])


@router.post("/agent-demo")
def score_single(body: ScoringRequest, user: TokenData = Depends(require_auth)):
    """Score a single product for a client."""
    return run_single_scoring(body.client_id, body.product_id, user.name, user.email)


@router.post("/batch")
def score_batch(body: BatchScoringRequest, user: TokenData = Depends(require_auth)):
    """Score all products for a client in one call (blocking)."""
    inline = [{"label": d.label, "text": d.text} for d in body.documents]
    return run_batch_scoring(body.client_id, body.document_ids, inline, user.name, user.email)


@router.post("/batch/stream")
async def score_batch_stream(body: BatchScoringRequest, user: TokenData = Depends(require_auth)):
    """Score all products with SSE streaming — results appear as each product is scored."""
    from app.services.scoring.batch_scoring_service import BatchScoringService

    inline = [{"label": d.label, "text": d.text} for d in body.documents]
    service = BatchScoringService()

    selected_ids = body.product_ids if body.product_ids else None

    async def event_stream():
        async for event in service.stream_batch(
            body.client_id,
            inline_documents=inline or None,
            product_ids=selected_ids,
        ):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":    "no-cache",
            "X-Accel-Buffering": "no",
            "Connection":       "keep-alive",
        },
    )
