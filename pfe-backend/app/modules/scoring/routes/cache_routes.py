"""Cache & RAG diagnostics routes — read-only, authenticated."""
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends

from app.core.auth import TokenData, require_auth

router = APIRouter(prefix="/api/cache", tags=["cache"])


@router.get("/stats")
def cache_stats(user: TokenData = Depends(require_auth)) -> Dict[str, Any]:
    """Return stats for all cache layers and the RAG knowledge base."""
    from app.services.scoring.scoring_cache_service import scoring_cache
    from app.services.cache.embedding_cache import embedding_cache
    from app.services.cache.reference_cache import reference_cache
    from app.services.cache import llm_cache
    from app.services.rag import knowledge_base

    return {
        "scoring_cache":    scoring_cache.stats(),
        "embedding_cache":  embedding_cache.stats(),
        "reference_cache":  reference_cache.stats(),
        "llm_cache":        llm_cache.stats(),
        "rag_knowledge_base": knowledge_base.stats(),
    }


@router.delete("/reference")
def invalidate_reference_cache(user: TokenData = Depends(require_auth)) -> Dict[str, Any]:
    """Invalidate reference data cache (call after updating products/criteria)."""
    from app.services.cache.reference_cache import reference_cache
    reference_cache.invalidate()
    return {"status": "ok", "message": "Reference cache cleared"}
