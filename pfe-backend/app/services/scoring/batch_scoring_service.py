from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List

from app.services.scoring.agent_orchestrator_service import AgentOrchestratorService
from app.services.scoring.scoring_pipeline_service import ScoringPipelineService
from app.services.scoring.score_mapper_service import ScoreMapperService
from app.services.scoring.data_quality_service import DataQualityService
from app.modules.elasticsearch.tools.reference_tool import ESReferenceTool

logger = logging.getLogger(__name__)

# Max products evaluated in parallel.
# Each product itself parallelises criterion evaluation internally (up to
# _MAX_LLM_WORKERS threads), so the total thread count is
# BATCH_PRODUCT_WORKERS × _MAX_LLM_WORKERS at peak.
# Keep this low to avoid overwhelming the LLM provider rate limits.
_BATCH_PRODUCT_WORKERS = 5


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

        # For the demo client (L'ORÉAL): inject pre-fetched sources + local client docs.
        # Other clients: ClientDocumentTool handles local files inside prepare_client_context.
        # We load local docs manually here only for the demo path because that path
        # builds ClientContext directly and never calls prepare_client_context.
        if client_id == DEMO_CLIENT_ID:
            from app.services.documents.local_document_loader import load_documents_for_client
            client_docs = load_documents_for_client(client_id)
            extra_sources = list(DEMO_SOURCES) + client_docs
            logger.info(
                "Batch[%s]: demo mode — pre-fetched sources + %d client doc(s) injected",
                client_id, len(client_docs),
            )

        # Inline documents are handled by ClientDocumentTool inside prepare_client_context.
        # Do NOT convert them to extra_sources here — that would duplicate them.
        if inline_documents:
            logger.info("Batch[%s]: %d inline document(s) will be passed to ClientDocumentTool", client_id, len(inline_documents))

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
                context = self.orchestrator.prepare_client_context(
                    client_id,
                    extra_sources=extra_sources,
                    inline_documents=inline_documents,
                )
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
    # Streaming API — yields events as each product is scored
    # ------------------------------------------------------------------

    async def stream_batch(
        self,
        client_id: str,
        inline_documents: List[Dict[str, Any]] | None = None,
        product_ids: List[str] | None = None,
    ):
        """
        Async generator that yields SSE-ready dicts.
        Events: context_ready | product_result | done | error
        """
        import asyncio, time as _time

        loop  = asyncio.get_event_loop()
        start = _time.monotonic()

        # ── Phase 1: build client context in a thread ────────────────────────
        try:
            context = await loop.run_in_executor(
                None,
                lambda: self.orchestrator.prepare_client_context(
                    client_id, inline_documents=inline_documents
                ),
            )
        except Exception as exc:
            yield {"type": "error", "detail": str(exc)}
            return

        if context.client_data is None:
            yield {"type": "error", "detail": f"Client '{client_id}' not found in Elasticsearch."}
            return

        client_data = context.client_data or {}
        yield {
            "type":   "context_ready",
            "client": {
                "client_id":   client_data.get("client_id"),
                "client_name": client_data.get("client_name"),
                "sector":      client_data.get("sector"),
                "website":     client_data.get("website"),
            },
        }

        # ── Phase 2: check scoring cache first, only run pipeline for misses ──
        from app.services.scoring.scoring_cache_service import scoring_cache

        all_products = self.reference_tool._load_json(self.reference_tool._products_path)
        if not all_products:
            yield {"type": "error", "detail": "No products found."}
            return

        # Filter to requested products if a selection was provided
        if product_ids:
            products = [p for p in all_products if p["id"] in product_ids]
            if not products:
                yield {"type": "error", "detail": "None of the requested product IDs were found."}
                return
        else:
            products = all_products

        # Split products into cache hits (instant) and misses (need scoring)
        cached_results  = []
        products_to_run = []
        has_inline_docs = bool(inline_documents)

        for p in products:
            if not has_inline_docs:           # skip cache when new docs are provided
                hit = scoring_cache.get(client_id, p["id"])
                if hit:
                    cached_results.append(hit)
                    continue
            products_to_run.append(p)

        # Stream cached results immediately (no wait)
        succeeded = len(cached_results)
        for result in cached_results:
            yield {"type": "product_result", "result": {**result, "cache_hit": True}}

        if cached_results and not products_to_run:
            # Everything was cached — skip context build, return instantly
            duration = round(_time.monotonic() - start, 1)
            yield {
                "type": "done",
                "summary": {
                    "total":            len(products),
                    "succeeded":        succeeded,
                    "failed":           0,
                    "duration_seconds": duration,
                    "from_cache":       len(cached_results),
                },
            }
            return

        # Some products need live scoring — proceed with context
        queue: asyncio.Queue = asyncio.Queue()

        def _producer():
            with ThreadPoolExecutor(max_workers=_BATCH_PRODUCT_WORKERS) as pool:
                futures = {
                    pool.submit(self._score_one_product, context, p["id"], p["name"]): p
                    for p in products_to_run
                }
                for fut in as_completed(futures):
                    try:
                        result = fut.result()
                    except Exception as exc:
                        product_meta = futures[fut]
                        result = {
                            "product_id":   product_meta["id"],
                            "product_name": product_meta["name"],
                            "status":       "failed",
                            "error":        str(exc),
                        }
                    loop.call_soon_threadsafe(queue.put_nowait, result)
            loop.call_soon_threadsafe(queue.put_nowait, None)   # sentinel

        loop.run_in_executor(None, _producer)

        while True:
            result = await queue.get()
            if result is None:
                break
            if result.get("status") == "success":
                succeeded += 1
                try:
                    scoring_cache.set(client_id, result["product_id"], result)
                except Exception:
                    pass
            yield {"type": "product_result", "result": result}

        duration = round(_time.monotonic() - start, 1)
        yield {
            "type": "done",
            "summary": {
                "total":            len(products),
                "succeeded":        succeeded,
                "failed":           len(products) - succeeded,
                "duration_seconds": duration,
                "from_cache":       len(cached_results),
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

            result = {
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
            # Save to cache so campaign scoring can reuse this result
            try:
                from app.services.scoring.scoring_cache_service import scoring_cache
                scoring_cache.set(context.client_id, product_id, result)
            except Exception:
                pass  # cache failure must never break scoring
            return result

        except Exception as exc:
            logger.error("Batch product %s failed: %s", product_id, exc)
            return {
                "product_id":   product_id,
                "product_name": product_name,
                "status":       "failed",
                "error":        str(exc),
            }
