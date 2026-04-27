from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from app.tools.es_client_tool import ESClientTool
from app.tools.es_reference_tool import ESReferenceTool
from app.tools.semantic_crawl_tool import SemanticCrawlTool
from app.tools.linkedin_playwright_tool import LinkedInPlaywrightTool
from app.tools.news_search_tool import NewsSearchTool
from app.tools.pdf_search_tool import PDFSearchTool
from app.services.enrichment.social_extractor import SocialExtractor
from app.services.scoring.chunk_embedder_service import ChunkEmbedderService
from app.services.scoring.semantic_retriever_service import SemanticRetrieverService
from app.services.scoring.llm_extractor_service import LLMExtractorService, ExtractionResult
from app.services.scoring.llm_reasoner_service import LLMReasonerService, FinalAnswer
from app.services.scoring.source_conflict_resolver import SourceConflictResolver, _fmt

logger = logging.getLogger(__name__)

# Max parallel LLM criterion evaluations.
# Ollama queues requests — increasing this beyond 2-3 only helps if
# OLLAMA_NUM_PARALLEL > 1 is set in the Ollama process environment.
# Even at 1, parallelizing reduces Python-side blocking overhead.
_MAX_LLM_WORKERS = 5


class AgentOrchestratorService:
    """
    Hybrid semantic scoring pipeline — optimised for speed.

    Key performance improvements over v1:
      • Website pages fetched in parallel (ThreadPoolExecutor in SemanticCrawlTool)
      • Website crawl + LinkedIn crawl run concurrently
      • All criteria evaluated concurrently via ThreadPoolExecutor
        (Ollama serializes them internally; Python doesn't block between submissions)
      • LinkedIn has a DuckDuckGo fallback — never silently skipped

    Flow:
      1. Load product + criteria + choices (ES)
      2. Load client from ES
      3. Resolve LinkedIn URL (parallel with website metadata fetch)
      4. Website crawl + LinkedIn crawl — run concurrently
      5. Build flat source list
      6. Chunk + embed all sources in one batch
      7. Embed all criterion queries in one pass
      8. Per criterion (concurrent): retrieve → LLM extract → validate
    """

    def __init__(self) -> None:
        self.client_tool     = ESClientTool()
        self.reference_tool  = ESReferenceTool()
        self.website_tool    = SemanticCrawlTool()
        self.linkedin_tool   = LinkedInPlaywrightTool()
        self.news_tool       = NewsSearchTool()
        self.pdf_tool        = PDFSearchTool()
        self.social_extractor = SocialExtractor()
        self.embedder        = ChunkEmbedderService()
        self.retriever       = SemanticRetrieverService()
        self.extractor       = LLMExtractorService()
        self.reasoner        = LLMReasonerService()
        self.conflict_resolver = SourceConflictResolver()

    # ── Pipeline entry point ────────────────────────────────────────────────

    def run(self, client_id: str, product_id: str) -> Dict[str, Any]:
        from app.services.scoring.demo_sources import DEMO_CLIENT_ID, DEMO_CLIENT_DATA, DEMO_SOURCES
        if client_id == DEMO_CLIENT_ID:
            return self._run_demo(client_id, product_id, DEMO_CLIENT_DATA, DEMO_SOURCES)
        return self._run_live(client_id, product_id)

    def _run_demo(
        self,
        client_id: str,
        product_id: str,
        client_data: Dict[str, Any],
        demo_sources: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Demo mode: skip live crawling, inject pre-fetched source data.
        The rest of the pipeline (embedding, retrieval, LLM, scoring) is real.
        """
        trace: List[str] = ["[DEMO MODE] Using pre-fetched source data — live crawling skipped."]

        trace.append("Step 1: load product + criteria + choices")
        product   = self.reference_tool.get_product(product_id)
        criteria  = self.reference_tool.get_criteria(product_id)
        all_choices = self.reference_tool.get_all_choices_grouped()
        choices_by_criterion = {c["id"]: all_choices.get(c["id"], []) for c in criteria}

        trace.append(f"Step 2: client — {client_data['client_name']} (demo, pre-loaded)")
        trace.append(f"  ⚠ SUBSTITUTE CLIENT: CRM record {client_id} exists in the database.")
        trace.append(f"  ⚠ CRM employee count ({client_data['crm_employee_count']:,}) dates from 2015 — stale.")
        trace.append(f"  ✓ Real 2023 figure (94,605) sourced from Wikipedia + L'Oréal Finance report.")

        trace.append("Step 3: LinkedIn — pre-loaded (linkedin.com/company/l-oreal)")

        for src in demo_sources:
            trace.append(f"  Demo source: [{src['type']}] {src['label']}")

        sources_meta = {
            "website":  client_data["website"],
            "linkedin": client_data["linkedin"],
            "news":     [s["url"] for s in demo_sources if s["type"] == "news"],
        }

        trace.append("Step 4: chunk + embed demo sources")
        all_chunks: List[Dict] = []
        for src in demo_sources:
            all_chunks.extend(self.embedder.chunk_source(src))
        trace.append(f"  {len(all_chunks)} chunk(s) from {len(demo_sources)} sources")
        all_chunks = self.embedder.embed_chunks(all_chunks)

        trace.append("Step 5 (pre): embed criterion queries")
        query_embeddings = {
            c["id"]: self.embedder.embed_query(c.get("label", ""))
            for c in criteria
        }

        trace.append(f"Step 6: evaluate {len(criteria)} criteria (LLM extraction — real)")

        results_map: Dict[str, Tuple[Dict, List[str]]] = {}
        with ThreadPoolExecutor(max_workers=_MAX_LLM_WORKERS) as pool:
            futures = {
                pool.submit(
                    self._evaluate_criterion,
                    criterion,
                    all_chunks,
                    choices_by_criterion.get(criterion["id"], []),
                    client_data,
                    sources_meta,
                    query_embeddings.get(criterion["id"]),
                ): criterion["id"]
                for criterion in criteria
            }
            for future in as_completed(futures):
                cid = futures[future]
                try:
                    result_dict, local_trace = future.result()
                    results_map[cid] = (result_dict, local_trace)
                except Exception as exc:
                    logger.error("Demo criterion %s failed: %s", cid, exc)
                    results_map[cid] = (
                        {"criterion_id": cid, "error": str(exc)},
                        [f"  [{cid}] ERROR: {exc}"],
                    )

        criterion_results = []
        for c in criteria:
            result_dict, local_trace = results_map[c["id"]]
            trace.extend(local_trace)
            criterion_results.append(result_dict)

        return {
            "trace":            trace,
            "product":          product,
            "criteria":         criteria,
            "client_data":      client_data,
            "website_data":     {"pages": [s for s in demo_sources if s["type"] == "website"]},
            "linkedin_data":    {"pages": [s for s in demo_sources if s["type"] == "linkedin"]},
            "news_data":        {"pages": [s for s in demo_sources if s["type"] == "news"]},
            "criteria_results": criterion_results,
            "demo_mode":        True,
        }

    # ── Batch-friendly API ──────────────────────────────────────────────────
    # These two methods split the pipeline into a shareable client phase
    # (crawl + embed, done ONCE per client) and a product phase (LLM per
    # criterion, done once per product).  The existing run() path is kept
    # intact; it internally delegates through both phases.

    def prepare_client_context(
        self, client_id: str, extra_sources: Optional[List[Dict[str, Any]]] = None
    ) -> "ClientContext":
        """
        Crawl the client's sources and embed all chunks.
        The result is reusable across every product belonging to this client.
        Calling this once for a batch saves N-1 full crawl+embed cycles.
        """
        trace: List[str] = []

        trace.append("CTX: load client from Elasticsearch")
        client_data = self.client_tool.run(client_id)
        if client_data is None:
            trace.append(f"WARNING: client '{client_id}' not found or ES unreachable")

        trace.append("CTX: resolve LinkedIn URL")
        linkedin_url = self._resolve_linkedin(client_data or {}, trace)
        company_name = (client_data or {}).get("client_name")
        if client_data:
            client_data = {**client_data, "linkedin": linkedin_url}

        trace.append("CTX: crawl website + LinkedIn + news + PDFs in parallel")
        website_url = (client_data or {}).get("website")
        website_domain = _extract_domain(website_url)

        with ThreadPoolExecutor(max_workers=4) as crawl_pool:
            website_future  = crawl_pool.submit(self.website_tool.run, website_url)
            linkedin_future = crawl_pool.submit(self.linkedin_tool.run, linkedin_url, company_name)
            news_future     = crawl_pool.submit(self.news_tool.run, company_name, website_domain)
            pdf_future      = crawl_pool.submit(self.pdf_tool.run, company_name, website_domain)
            website_data  = website_future.result()
            linkedin_data = linkedin_future.result()
            news_data     = news_future.result()
            pdf_data      = pdf_future.result()

        pdf_pages = pdf_data.get("pages", [])
        if pdf_pages:
            for p in pdf_pages:
                trace.append(f"  PDF: [{p.get('title','?')[:60]}] {p.get('url','')[:60]}")
        else:
            trace.append("  PDF: no public documents found")

        trace.append("CTX: build + embed sources")
        sources = self._build_sources(client_data or {}, website_data, linkedin_data, news_data, pdf_data)

        # Inject uploaded documents as additional sources
        if extra_sources:
            for doc in extra_sources:
                sources.append(doc)
                trace.append(f"  Document source: [{doc['label']}] ({len(doc.get('text',''))} chars)")
        all_chunks: List[Dict] = []
        for src in sources:
            all_chunks.extend(self.embedder.chunk_source(src))
        all_chunks = self.embedder.embed_chunks(all_chunks)
        trace.append(f"  {len(all_chunks)} chunk(s) embedded ({len(sources)} sources)")

        sources_meta = {
            "website":  website_url,
            "linkedin": linkedin_url,
            "news":     [p.get("url") for p in news_data.get("pages", [])],
        }

        return ClientContext(
            client_id=client_id,
            client_data=client_data,
            all_chunks=all_chunks,
            sources_meta=sources_meta,
            base_trace=trace,
        )

    def score_product_from_context(
        self, context: "ClientContext", product_id: str
    ) -> Dict[str, Any]:
        """
        Score one product using a pre-computed ClientContext.
        Called by both the single-product path and the batch path.
        """
        trace = list(context.base_trace)
        trace.append(f"PRODUCT {product_id}: load criteria + choices")

        product     = self.reference_tool.get_product(product_id)
        criteria    = self.reference_tool.get_criteria(product_id)
        all_choices = self.reference_tool.get_all_choices_grouped()
        choices_by_criterion: Dict[str, List[Dict]] = {
            c["id"]: all_choices.get(c["id"], []) for c in criteria
        }

        if not product:
            return {"error": f"Product '{product_id}' not found."}
        if not criteria:
            return {"error": f"No criteria found for product '{product_id}'."}

        trace.append(f"PRODUCT {product_id}: embed {len(criteria)} criterion queries")
        query_embeddings: Dict[str, Any] = {
            c["id"]: self.embedder.embed_query(c.get("label", ""))
            for c in criteria
        }

        trace.append(
            f"PRODUCT {product_id}: evaluate {len(criteria)} criteria "
            f"(parallel, max {_MAX_LLM_WORKERS} workers)"
        )
        results_map: Dict[str, Tuple[Dict, List[str]]] = {}
        with ThreadPoolExecutor(max_workers=_MAX_LLM_WORKERS) as llm_pool:
            futures = {
                llm_pool.submit(
                    self._evaluate_criterion,
                    criterion,
                    context.all_chunks,
                    choices_by_criterion.get(criterion["id"], []),
                    context.client_data or {},
                    context.sources_meta,
                    query_embeddings.get(criterion["id"]),
                ): criterion["id"]
                for criterion in criteria
            }
            for future in as_completed(futures):
                cid = futures[future]
                try:
                    result_dict, local_trace = future.result()
                    results_map[cid] = (result_dict, local_trace)
                except Exception as exc:
                    logger.error("Criterion %s evaluation failed: %s", cid, exc)
                    results_map[cid] = (
                        {"criterion_id": cid, "error": str(exc)},
                        [f"  [{cid}] ERROR: {exc}"],
                    )

        criterion_results = []
        for c in criteria:
            result_dict, local_trace = results_map[c["id"]]
            trace.extend(local_trace)
            criterion_results.append(result_dict)

        return {
            "trace":            trace,
            "product":          product,
            "criteria":         criteria,
            "client_data":      context.client_data,
            "website_data":     {},
            "linkedin_data":    {},
            "news_data":        {},
            "criteria_results": criterion_results,
        }

    def _run_live(self, client_id: str, product_id: str) -> Dict[str, Any]:
        # Delegate through the shared context API so single-product and
        # batch paths share the same implementation.
        context = self.prepare_client_context(client_id)
        return self.score_product_from_context(context, product_id)

    def _run_live_LEGACY(self, client_id: str, product_id: str) -> Dict[str, Any]:
        """Original monolithic implementation — kept for reference, not called."""
        trace: List[str] = []

        # ── Step 1: reference data ──────────────────────────────────────────
        trace.append("Step 1: load product + criteria + choices")
        product    = self.reference_tool.get_product(product_id)
        criteria   = self.reference_tool.get_criteria(product_id)
        all_choices = self.reference_tool.get_all_choices_grouped()
        choices_by_criterion: Dict[str, List[Dict]] = {
            c["id"]: all_choices.get(c["id"], []) for c in criteria
        }

        # ── Step 2: client data ─────────────────────────────────────────────
        trace.append("Step 2: load client from Elasticsearch")
        client_data = self.client_tool.run(client_id)
        if client_data is None:
            trace.append(f"WARNING: client '{client_id}' not found or ES unreachable")

        # ── Step 3: resolve LinkedIn URL ────────────────────────────────────
        trace.append("Step 3: resolve LinkedIn URL")
        linkedin_url = self._resolve_linkedin(client_data or {}, trace)
        company_name = (client_data or {}).get("client_name")
        if client_data:
            client_data = {**client_data, "linkedin": linkedin_url}

        # ── Step 4: parallel crawl (website + LinkedIn + news) ──────────────
        trace.append("Step 4+5: crawl website + LinkedIn + news in parallel")
        website_url = (client_data or {}).get("website")
        website_domain = _extract_domain(website_url)

        with ThreadPoolExecutor(max_workers=4) as crawl_pool:
            website_future  = crawl_pool.submit(self.website_tool.run, website_url)
            linkedin_future = crawl_pool.submit(
                self.linkedin_tool.run, linkedin_url, company_name
            )
            news_future = crawl_pool.submit(
                self.news_tool.run, company_name, website_domain
            )
            pdf_future = crawl_pool.submit(
                self.pdf_tool.run, company_name, website_domain
            )
            website_data  = website_future.result()
            linkedin_data = linkedin_future.result()
            news_data     = news_future.result()
            pdf_data      = pdf_future.result()

        for p in website_data.get("pages", []):
            trace.append(f"  Website page: {p.get('url', '?')}")
        li_pages = linkedin_data.get("pages", [])
        if li_pages:
            for p in li_pages:
                trace.append(f"  LinkedIn source: [{p.get('title','?')}] {p.get('url','')}")
        else:
            trace.append("  LinkedIn: no content from any strategy")
        news_pages = news_data.get("pages", [])
        if news_pages:
            for p in news_pages:
                trace.append(f"  News article: [{p.get('title','?')}] {p.get('url','')}")
        else:
            trace.append("  News: no recent articles found")

        # ── Step 5: build flat source list ──────────────────────────────────
        trace.append("Step 6: build evidence sources")
        pdf_pages = pdf_data.get("pages", [])
        if pdf_pages:
            for p in pdf_pages:
                trace.append(f"  PDF: [{p.get('title','?')[:60]}] {p.get('url','')[:60]}")
        sources = self._build_sources(client_data or {}, website_data, linkedin_data, news_data, pdf_data)
        for s in sources:
            trace.append(f"  Source accepted: [{s['type']}] {s['label']} — {s.get('url','')}")

        # ── Step 6: chunk + embed all sources in one batch ──────────────────
        trace.append("Step 7: chunk and embed all sources")
        all_chunks: List[Dict] = []
        for src in sources:
            all_chunks.extend(self.embedder.chunk_source(src))
        trace.append(f"  {len(all_chunks)} chunk(s) created")
        all_chunks = self.embedder.embed_chunks(all_chunks)
        embed_mode = "dense (fastembed)" if self.embedder.embeddings_available else "BM25 fallback"
        trace.append(f"  Embeddings: {embed_mode}")

        # ── Step 7: pre-embed all criterion queries ─────────────────────────
        # Batch query embeddings in the main thread before parallelising LLM calls
        trace.append("Step 8 (pre): embed all criterion queries")
        query_embeddings: Dict[str, Any] = {
            c["id"]: self.embedder.embed_query(c.get("label", ""))
            for c in criteria
        }

        sources_meta = {
            "website":  website_url,
            "linkedin": linkedin_url,
            "news":     [p.get("url") for p in news_data.get("pages", [])],
        }

        # ── Step 8: concurrent criterion evaluation ─────────────────────────
        trace.append(f"Step 8: evaluate {len(criteria)} criteria (parallel, max {_MAX_LLM_WORKERS} workers)")

        results_map: Dict[str, Tuple[Dict, List[str]]] = {}

        with ThreadPoolExecutor(max_workers=_MAX_LLM_WORKERS) as llm_pool:
            futures = {
                llm_pool.submit(
                    self._evaluate_criterion,
                    criterion,
                    all_chunks,
                    choices_by_criterion.get(criterion["id"], []),
                    client_data or {},
                    sources_meta,
                    query_embeddings.get(criterion["id"]),
                ): criterion["id"]
                for criterion in criteria
            }
            for future in as_completed(futures):
                cid = futures[future]
                try:
                    result_dict, local_trace = future.result()
                    results_map[cid] = (result_dict, local_trace)
                except Exception as exc:
                    logger.error("Criterion %s evaluation failed: %s", cid, exc)
                    # Insert a placeholder so the list stays complete
                    results_map[cid] = (
                        {"criterion_id": cid, "error": str(exc)},
                        [f"  [{cid}] ERROR: {exc}"],
                    )

        # Preserve original criteria order and merge per-criterion traces
        criterion_results = []
        for c in criteria:
            result_dict, local_trace = results_map[c["id"]]
            trace.extend(local_trace)
            criterion_results.append(result_dict)

        return {
            "trace":          trace,
            "product":        product,
            "criteria":       criteria,
            "client_data":    client_data,
            "website_data":   website_data,
            "linkedin_data":  linkedin_data,
            "news_data":      news_data,
            "criteria_results": criterion_results,
        }

    # ── LinkedIn resolution ─────────────────────────────────────────────────

    def _resolve_linkedin(
        self, client_data: Dict[str, Any], trace: List[str]
    ) -> Optional[str]:
        url = client_data.get("linkedin")
        if url:
            trace.append("  LinkedIn: resolved from CRM field")
            return url

        website = client_data.get("website")
        if website:
            url = self.social_extractor.extract_linkedin(website)
            if url:
                trace.append(f"  LinkedIn: found via website scrape — {url}")
                return url

        name = client_data.get("client_name")
        if name:
            url = self.social_extractor.infer_linkedin_from_name(name)
            if url:
                trace.append(f"  LinkedIn: inferred from company name (heuristic) — {url}")
                return url

        trace.append("  LinkedIn: could not be resolved")
        return None

    # ── Evidence source builder ─────────────────────────────────────────────

    @staticmethod
    def _source_is_relevant(text: str, company_name: Optional[str]) -> bool:
        """
        Returns False when a fallback source (Wikipedia, DDG) clearly contains
        no reference to the client company.  Always returns True for CRM and
        direct website/LinkedIn pages — those are trusted by construction.
        """
        if not company_name:
            return True
        name_words = [w for w in company_name.lower().split() if len(w) > 3]
        if not name_words:
            return True
        return any(w in text.lower() for w in name_words)

    def _build_sources(
        self,
        client_data: Dict[str, Any],
        website_data: Dict[str, Any],
        linkedin_data: Dict[str, Any],
        news_data: Dict[str, Any],
        pdf_data: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        sources: List[Dict[str, Any]] = []
        company_name: Optional[str] = client_data.get("client_name")

        desc = (client_data.get("description") or "").strip()
        if desc:
            sources.append({
                "type":  "crm_description",
                "url":   None,
                "label": "Company description (CRM)",
                "text":  desc,
                "sections": [],
                "anchors": {},
            })

        website_url = client_data.get("website")
        for page in website_data.get("pages", []):
            text = page.get("full_text") or f"{page.get('title', '')} {page.get('snippet', '')}"
            if text.strip():
                # Website pages are trusted (fetched from the client's own domain)
                sources.append({
                    "type":  "website",
                    "url":   page.get("url") or website_url,
                    "label": page.get("title") or page.get("url") or "Website",
                    "text":  text,
                    "sections": page.get("sections", []),
                    "anchors":  page.get("anchors", {}),
                })

        linkedin_url = client_data.get("linkedin")
        for page in linkedin_data.get("pages", []):
            text = page.get("full_text") or page.get("snippet", "")
            if not text.strip():
                continue
            # Fallback pages (Wikipedia, DDG) must mention the company name.
            # Direct LinkedIn pages are always trusted.
            page_url = page.get("url") or ""
            is_direct = "linkedin.com" in page_url
            if not is_direct and not self._source_is_relevant(text, company_name):
                logger.warning(
                    "Rejected fallback source '%s' — content does not mention '%s'",
                    page.get("title", page_url), company_name,
                )
                continue
            sources.append({
                "type":  "linkedin",
                "url":   page_url or linkedin_url,
                "label": page.get("title") or "LinkedIn",
                "text":  text,
                "sections": page.get("sections", []),
                "anchors": {},
            })

        for page in news_data.get("pages", []):
            text = page.get("full_text") or page.get("snippet", "")
            if not text.strip():
                continue
            if not self._source_is_relevant(text, company_name):
                logger.warning(
                    "Rejected news article '%s' — does not mention '%s'",
                    page.get("title", ""), company_name,
                )
                continue
            sources.append({
                "type":     "news",
                "url":      page.get("url"),
                "label":    page.get("title") or page.get("url") or "News article",
                "text":     text,
                "sections": page.get("sections", []),
                "anchors":  {},
            })

        # ── PDF documents (auto-discovered) ────────────────────────────────
        for page in (pdf_data or {}).get("pages", []):
            text = page.get("full_text") or page.get("snippet", "")
            if not text.strip():
                continue
            sources.append({
                "type":     "document",
                "url":      page.get("url"),
                "label":    page.get("title") or page.get("url") or "PDF Document",
                "text":     text,
                "sections": page.get("sections", []),
                "anchors":  {},
            })

        return sources

    # ── Criterion evaluation (runs in thread pool) ──────────────────────────

    def _evaluate_criterion(
        self,
        criterion:    Dict[str, Any],
        all_chunks:   List[Dict[str, Any]],
        choices:      List[Dict[str, Any]],
        client_data:  Dict[str, Any],
        sources_meta: Dict[str, Any],
        query_emb:    Any,
    ) -> Tuple[Dict[str, Any], List[str]]:
        """
        Multi-source criterion evaluation with conflict resolution.

        All available sources (CRM + semantic web extraction) are collected
        as candidates, then the SourceConflictResolver picks the best one.
        Returns (criterion_result_dict, trace_lines). Thread-safe.
        """
        local_trace: List[str] = []
        label       = criterion.get("label", "")
        answer_type = criterion.get("answer_type") or "text"
        unit        = criterion.get("unit") or ""

        # ── Collect CRM candidate (numeric only) ────────────────────────────
        candidates: List[Dict[str, Any]] = []
        crm_result_cache: Optional[Dict[str, Any]] = None

        if answer_type == "numeric":
            crm_val = self._crm_headcount(client_data, label.lower())
            if crm_val is not None:
                display = _fmt(crm_val)
                candidates.append({
                    "source_type":  "crm",
                    "source_label": "CRM (Salesforce)",
                    "source_url":   None,
                    "value":        crm_val,
                    "confidence":   0.95,
                    "evidence":     f"NumberOfEmployees: {display}",
                })
                # Cache the full CRM result dict in case we end up using it
                crm_result_cache = self._build_crm_result(
                    criterion, choices, crm_val, display, unit, sources_meta
                )

        # ── Semantic retrieval + LLM extraction ─────────────────────────────
        passages = self.retriever.retrieve(
            query_embedding=query_emb,
            query_text=label,
            chunks=all_chunks,
            top_k=5,
        )

        if passages:
            local_trace.append(
                f"  [{label[:50]}] → {len(passages)} passage(s), "
                f"top sim={passages[0].get('similarity', 0):.2f}"
            )
        else:
            local_trace.append(f"  [{label[:50]}] → no passages above threshold")

        extraction = self.extractor.extract(
            criterion_label=label,
            answer_type=answer_type,
            unit=unit,
            choices=choices,
            passages=passages,
        )

        web_result: Optional[Dict[str, Any]] = None
        if extraction.found and extraction.is_valid and extraction.extracted_value is not None:
            candidates.append({
                "source_type":  extraction.source_type,
                "source_label": extraction.source_label,
                "source_url":   extraction.source_url,
                "value":        extraction.extracted_value,
                "confidence":   extraction.confidence,
                "evidence":     extraction.evidence_sentence,
                "extraction":   extraction,     # keep full object for result building
            })
            final_web = self._extraction_to_final(extraction, sources_meta)
            web_result = self._criterion_result(
                criterion=criterion,
                choices=choices,
                predicted_answer=final_web.predicted_answer,
                extracted_value=final_web.extracted_value,
                confidence=final_web.confidence,
                justification=final_web.justification,
                evidence=final_web.evidence,
                sources=sources_meta,
            )

        # ── No candidates at all ─────────────────────────────────────────────
        if not candidates:
            final = self._extraction_to_final(extraction, sources_meta)
            return self._criterion_result(
                criterion=criterion,
                choices=choices,
                predicted_answer=final.predicted_answer,
                extracted_value=final.extracted_value,
                confidence=final.confidence,
                justification=final.justification,
                evidence=final.evidence,
                sources=sources_meta,
            ), local_trace

        # ── Single candidate — no conflict possible ──────────────────────────
        if len(candidates) == 1:
            c = candidates[0]
            if c["source_type"] == "crm" and crm_result_cache:
                local_trace.append(f"  [{label[:50]}] → CRM only: {_fmt(c['value'])}")
                return crm_result_cache, local_trace
            local_trace.append(
                f"  [{label[:50]}] → {c['source_type']}: {_fmt(c['value'])} "
                f"(conf {c['confidence']:.0%})"
            )
            return web_result, local_trace

        # ── Multi-source conflict resolution ─────────────────────────────────
        resolution = self.conflict_resolver.resolve(candidates, label, answer_type)
        best = resolution["selected_candidate"]
        conflict = resolution["conflict_detected"]
        reasoning = resolution["reasoning"]

        # Log candidates and decision
        cand_summary = " | ".join(
            f"{c['source_type']}={_fmt(c['value'])} ({c['confidence']:.0%})"
            for c in candidates
        )
        local_trace.append(
            f"  [{label[:50]}] → multi-source [{cand_summary}] "
            f"{'⚡ CONFLICT' if conflict else '✓ agree'} → "
            f"selected {best['source_type'].upper()}: {_fmt(best['value'])}"
        )

        # Build result from the winning candidate
        if best["source_type"] == "crm" and crm_result_cache:
            result = dict(crm_result_cache)
            # Annotate with conflict resolution metadata
            result["source_resolution"] = {
                "conflict_detected": conflict,
                "reasoning": reasoning,
                "all_candidates": [
                    {"source_type": c["source_type"], "value": _fmt(c["value"]),
                     "confidence": round(c["confidence"], 2)}
                    for c in candidates
                ],
            }
            return result, local_trace

        # Winner is a web source — use web_result with resolution metadata
        if web_result and best.get("source_type") == (
            candidates[-1]["source_type"]  # last candidate is the web one
        ):
            result = dict(web_result)
            result["source_resolution"] = {
                "conflict_detected": conflict,
                "reasoning": reasoning,
                "all_candidates": [
                    {"source_type": c["source_type"], "value": _fmt(c["value"]),
                     "confidence": round(c["confidence"], 2)}
                    for c in candidates
                ],
            }
            # Override justification reasoning with conflict resolution explanation
            if isinstance(result.get("justification"), dict):
                result["justification"] = dict(result["justification"])
                result["justification"]["reasoning"] = reasoning
            return result, local_trace

        # Fallback — return web extraction result as-is
        return (web_result or crm_result_cache), local_trace

    # ── CRM result builder (extracted from _evaluate_criterion) ─────────────

    @staticmethod
    def _build_crm_result(
        criterion: Dict[str, Any],
        choices:   List[Dict[str, Any]],
        crm_val:   float,
        display:   str,
        unit:      str,
        sources_meta: Dict[str, Any],
    ) -> Dict[str, Any]:
        return AgentOrchestratorService._criterion_result(
            criterion=criterion,
            choices=choices,
            predicted_answer=display,
            extracted_value=crm_val,
            confidence=0.95,
            justification={
                "source": "CRM (Salesforce)",
                "clickable_url": None,
                "extracted_evidence": f"NumberOfEmployees: <<< {display} >>>",
                "context_before": "", "context_after": "", "section": "",
                "search_hint": "Value read directly from CRM structured field.",
                "reasoning": f"Value {display} {unit} taken from CRM NumberOfEmployees — ground truth.",
            },
            evidence={
                "source_type": "crm", "source_url": None, "clickable_url": None,
                "source_label": "CRM (Salesforce)",
                "exact_quote": f"NumberOfEmployees: {display}",
                "highlighted_quote": f"NumberOfEmployees: <<< {display} >>>",
                "context_before": "", "context_after": "", "section": "",
                "search_hint": "CRM structured field.",
            },
            sources=sources_meta,
        )

    # ── Helpers ─────────────────────────────────────────────────────────────

    @staticmethod
    def _extraction_to_final(e: ExtractionResult, sources_meta: Dict) -> FinalAnswer:
        if not e.found or not e.is_valid:
            return FinalAnswer(
                predicted_answer="unknown",
                extracted_value=None,
                confidence=e.confidence,
                justification={
                    "source": e.source_label or None,
                    "clickable_url": None,
                    "extracted_evidence": None,
                    "context_before": "", "context_after": "", "section": "",
                    "search_hint": "",
                    "reasoning": e.reasoning or "No valid evidence found for this criterion.",
                },
                evidence=None,
                sources=sources_meta,
            )

        display    = _display(e.extracted_value)
        highlighted = f"<<< {e.evidence_sentence} >>>" if e.evidence_sentence else ""
        search_hint = f'Search for: "{e.evidence_sentence[:80]}"'
        if e.section:
            search_hint += f' under section "{e.section}"'

        return FinalAnswer(
            predicted_answer=display,
            extracted_value=e.extracted_value,
            confidence=e.confidence,
            justification={
                "source":             e.source_label,
                "clickable_url":      e.clickable_url,
                "extracted_evidence": highlighted,
                "context_before":     e.context_before,
                "context_after":      e.context_after,
                "section":            e.section,
                "search_hint":        search_hint,
                "reasoning":          e.reasoning,
            },
            evidence={
                "source_type":      e.source_type,
                "source_url":       e.source_url,
                "clickable_url":    e.clickable_url,
                "source_label":     e.source_label,
                "exact_quote":      e.evidence_sentence,
                "highlighted_quote": highlighted,
                "context_before":   e.context_before,
                "context_after":    e.context_after,
                "section":          e.section,
                "search_hint":      search_hint,
            },
            sources=sources_meta,
        )

    @staticmethod
    def _crm_headcount(client_data: Dict[str, Any], label_lower: str) -> Optional[float]:
        _pct_kws = {"part", "ratio", "taux", "%", "pourcent", "proportion"}
        if any(kw in label_lower for kw in _pct_kws):
            return None
        _employee_kws = {
            "effectif", "salarié", "employé", "collaborateur",
            "employee", "staff", "headcount", "workforce", "personnel",
        }
        if any(kw in label_lower for kw in _employee_kws):
            ec = client_data.get("crm_employee_count")
            if ec is not None:
                try:
                    return float(ec)
                except (TypeError, ValueError):
                    pass
        return None

    @staticmethod
    def _criterion_result(
        criterion:       Dict[str, Any],
        choices:         List[Dict[str, Any]],
        predicted_answer: str,
        extracted_value: Any,
        confidence:      float,
        justification:   Dict[str, Any],
        evidence:        Optional[Dict[str, Any]],
        sources:         Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "criterion_id":    criterion["id"],
            "label":           criterion.get("label", ""),
            "answer_type":     criterion.get("answer_type"),
            "predicted_answer": predicted_answer,
            "extracted_value": extracted_value,
            "confidence":      confidence,
            "justification":   justification,
            "evidence":        evidence,
            "sources":         sources,
            "default_score":   int(criterion.get("default_score", 0) or 0),
            "choices":         choices,
        }


@dataclass
class ClientContext:
    """
    Immutable snapshot of everything that is CLIENT-specific in the pipeline.
    Produced once by prepare_client_context() and reused across every product
    in a batch run — avoids repeating the crawl and embedding for each product.
    """
    client_id:   str
    client_data: Optional[Dict[str, Any]]
    all_chunks:  List[Dict[str, Any]]
    sources_meta: Dict[str, Any]
    base_trace:  List[str] = field(default_factory=list)


def _extract_domain(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    from urllib.parse import urlparse
    return urlparse(url).netloc.lower().lstrip("www.") or None


def _display(value: Any) -> str:
    if value is None:
        return "unknown"
    if isinstance(value, float) and value == int(value):
        return str(int(value))
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    return str(value)
