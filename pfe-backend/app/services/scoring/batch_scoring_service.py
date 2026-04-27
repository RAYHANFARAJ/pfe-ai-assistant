from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List

from app.services.scoring.agent_orchestrator_service import AgentOrchestratorService
from app.services.scoring.scoring_pipeline_service import ScoringPipelineService
from app.services.scoring.score_mapper_service import ScoreMapperService
from app.services.scoring.data_quality_service import DataQualityService, quality_tier
from app.modules.elasticsearch.tools.reference_tool import ESReferenceTool

logger = logging.getLogger(__name__)

# Max products evaluated in parallel.
# Each product itself parallelises criterion evaluation internally (up to
# _MAX_LLM_WORKERS threads), so the total thread count is
# BATCH_PRODUCT_WORKERS × _MAX_LLM_WORKERS at peak.
# Keep this low to avoid overwhelming the LLM provider rate limits.
_BATCH_PRODUCT_WORKERS = 3


class BatchScoringService:
    """
    Scores all products for a given client in a single batch.

    Key optimisation: the client's sources (website, LinkedIn, news) are
    crawled and embedded exactly ONCE, then reused for every product.
    Without this, N products would trigger N identical crawl+embed cycles.

    Partial failure isolation: if one product's scoring fails, the other
    products continue — the error is recorded in the per-product result.
    """

    def __init__(self) -> None:
        self.orchestrator    = AgentOrchestratorService()
        self.score_mapper    = ScoreMapperService()
        self.quality_checker = DataQualityService()
        self.reference_tool  = ESReferenceTool()
        # Reuse ScoringPipelineService only for its _walk_tree + aggregate logic
        self._pipeline       = ScoringPipelineService()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_batch(
        self,
        client_id: str,
        document_ids: List[str] | None = None,
        inline_documents: List[Dict[str, Any]] | None = None,
    ) -> Dict[str, Any]:
        """
        Score all products for client_id.
        Returns a BatchScoringResult dict.
        """
        started_at = time.monotonic()

        # ── Phase 1: prepare shared client context (crawl + embed ONCE) ────
        from app.services.scoring.demo_sources import DEMO_CLIENT_ID, DEMO_CLIENT_DATA, DEMO_SOURCES

        extra_sources: List[Dict[str, Any]] = []

        # Always load manually placed documents from client_documents/
        from app.services.documents.local_document_loader import load_local_documents
        local_docs = load_local_documents()
        if local_docs:
            extra_sources.extend(local_docs)
            logger.info("Batch[%s]: %d local document(s) loaded from client_documents/", client_id, len(local_docs))

        # For the demo client, inject pre-fetched sources instead of live crawl
        if client_id == DEMO_CLIENT_ID:
            extra_sources = list(DEMO_SOURCES) + [s for s in extra_sources if s.get("type") == "document"]
            logger.info("Batch[%s]: demo mode — pre-fetched sources injected", client_id)

        # Append inline documents (sent directly in the request — no server state required)
        if inline_documents:
            for doc in inline_documents:
                from app.services.scoring.agent_orchestrator_service import _extract_domain
                from app.services.documents.document_extractor import _build_sections
                src = {
                    "type":     "document",
                    "url":      None,
                    "label":    doc.get("label", "Document"),
                    "text":     doc.get("text", ""),
                    "sections": _build_sections(doc.get("text", "")),
                    "anchors":  {},
                }
                extra_sources.append(src)
            logger.info("Batch[%s]: %d inline document(s) attached", client_id, len(inline_documents))

        # Legacy: look up documents by ID from server-side store
        if document_ids:
            from app.services.documents.document_extractor import get_sources
            doc_sources = get_sources(document_ids)
            extra_sources.extend(doc_sources)
            logger.info("Batch[%s]: %d stored document(s) attached", client_id, len(doc_sources))

        logger.info("Batch[%s]: preparing client context", client_id)
        try:
            # For demo client, pass demo client_data directly to skip ES lookup
            if client_id == DEMO_CLIENT_ID:
                from app.services.scoring.agent_orchestrator_service import ClientContext
                all_chunks: List[Dict[str, Any]] = []
                for src in extra_sources:
                    all_chunks.extend(self.orchestrator.embedder.chunk_source(src))
                all_chunks = self.orchestrator.embedder.embed_chunks(all_chunks)
                context = ClientContext(
                    client_id=client_id,
                    client_data=DEMO_CLIENT_DATA,
                    all_chunks=all_chunks,
                    sources_meta={
                        "website":  DEMO_CLIENT_DATA["website"],
                        "linkedin": DEMO_CLIENT_DATA["linkedin"],
                        "news":     [],
                    },
                    base_trace=[f"[DEMO+BATCH] {len(extra_sources)} sources, {len(all_chunks)} chunks"],
                )
            else:
                context = self.orchestrator.prepare_client_context(client_id, extra_sources=extra_sources)
        except Exception as exc:
            logger.error("Batch[%s]: context preparation failed: %s", client_id, exc)
            return {
                "status": "failed",
                "error": f"Could not prepare client context: {exc}",
                "client_id": client_id,
            }
        # close the if/else opened above


        if context.client_data is None:
            return {
                "status": "failed",
                "error": "client_data_unavailable",
                "detail": f"Client '{client_id}' not found in Elasticsearch.",
                "client_id": client_id,
            }

        # ── Phase 2: score all products in parallel ──────────────────────────
        products = self.reference_tool._load_json(self.reference_tool._products_path)
        if not products:
            return {
                "status": "failed",
                "error": "no_products",
                "detail": "No products found in the reference file.",
                "client_id": client_id,
            }

        logger.info(
            "Batch[%s]: scoring %d products (max %d parallel)",
            client_id, len(products), _BATCH_PRODUCT_WORKERS,
        )

        product_results: List[Dict[str, Any]] = []

        with ThreadPoolExecutor(max_workers=_BATCH_PRODUCT_WORKERS) as pool:
            futures = {
                pool.submit(self._score_one_product, context, p["id"], p["name"]): p
                for p in products
            }
            for future in as_completed(futures):
                product_meta = futures[future]
                try:
                    product_results.append(future.result())
                except Exception as exc:
                    logger.error(
                        "Batch[%s]: product %s raised unexpected error: %s",
                        client_id, product_meta["id"], exc,
                    )
                    product_results.append({
                        "product_id":   product_meta["id"],
                        "product_name": product_meta["name"],
                        "status":       "failed",
                        "error":        str(exc),
                    })

        # Sort back to stable product order
        product_order = {p["id"]: i for i, p in enumerate(products)}
        product_results.sort(key=lambda r: product_order.get(r["product_id"], 999))

        duration = round(time.monotonic() - started_at, 1)
        succeeded = sum(1 for r in product_results if r["status"] == "success")

        client_data = context.client_data or {}
        return {
            "client": {
                "client_id":   client_data.get("client_id"),
                "client_name": client_data.get("client_name"),
                "sector":      client_data.get("sector"),
                "website":     client_data.get("website"),
                "linkedin":    client_data.get("linkedin"),
            },
            "results": product_results,
            "batch_summary": {
                "total":            len(products),
                "succeeded":        succeeded,
                "failed":           len(products) - succeeded,
                "duration_seconds": duration,
            },
        }

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _score_one_product(
        self,
        context: Any,           # ClientContext — avoids circular import at top level
        product_id: str,
        product_name: str,
    ) -> Dict[str, Any]:
        """
        Score a single product using the shared client context.
        Returns a product result dict regardless of success or failure.
        """
        try:
            orchestration = self.orchestrator.score_product_from_context(context, product_id)

            if "error" in orchestration:
                return {
                    "product_id":   product_id,
                    "product_name": product_name,
                    "status":       "failed",
                    "error":        orchestration["error"],
                }

            # Reuse ScoringPipelineService tree walker + aggregate
            raw_by_id = {
                item["criterion_id"]: item
                for item in orchestration["criteria_results"]
            }
            criteria_order = [
                item["criterion_id"] for item in orchestration["criteria_results"]
            ]

            scored_criteria, blocking_triggered = self._pipeline._walk_tree(
                criteria_order, raw_by_id
            )
            summary = self.score_mapper.aggregate(scored_criteria, blocking_triggered)
            quality_report = self.quality_checker.evaluate(scored_criteria)

            return {
                "product_id":       product_id,
                "product_name":     product_name,
                "status":           "success",
                "summary": {
                    "criteria_count": len(scored_criteria),
                    **summary,
                },
                "data_quality":     quality_report.model_dump(),
                "criteria_results": scored_criteria,
            }

        except Exception as exc:
            logger.error("Batch product %s failed: %s", product_id, exc)
            return {
                "product_id":   product_id,
                "product_name": product_name,
                "status":       "failed",
                "error":        str(exc),
            }
