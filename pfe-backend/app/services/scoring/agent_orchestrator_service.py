from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Tuple

from app.tools.es_client_tool import ESClientTool
from app.tools.es_reference_tool import ESReferenceTool
from app.tools.semantic_crawl_tool import SemanticCrawlTool
from app.tools.linkedin_crawl_tool import LinkedInCrawlTool
from app.services.enrichment.social_extractor import SocialExtractor
from app.services.scoring.chunk_embedder_service import ChunkEmbedderService
from app.services.scoring.semantic_retriever_service import SemanticRetrieverService
from app.services.scoring.llm_extractor_service import LLMExtractorService, ExtractionResult
from app.services.scoring.llm_reasoner_service import LLMReasonerService, FinalAnswer

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
        self.linkedin_tool   = LinkedInCrawlTool()
        self.social_extractor = SocialExtractor()
        self.embedder        = ChunkEmbedderService()
        self.retriever       = SemanticRetrieverService()
        self.extractor       = LLMExtractorService()
        self.reasoner        = LLMReasonerService()

    # ── Pipeline entry point ────────────────────────────────────────────────

    def run(self, client_id: str, product_id: str) -> Dict[str, Any]:
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

        # ── Step 4: parallel crawl (website + LinkedIn) ─────────────────────
        trace.append("Step 4+5: crawl website + LinkedIn in parallel")
        website_url = (client_data or {}).get("website")

        with ThreadPoolExecutor(max_workers=2) as crawl_pool:
            website_future  = crawl_pool.submit(self.website_tool.run, website_url)
            linkedin_future = crawl_pool.submit(
                self.linkedin_tool.run, linkedin_url, company_name
            )
            website_data  = website_future.result()
            linkedin_data = linkedin_future.result()

        for p in website_data.get("pages", []):
            trace.append(f"  Website page: {p.get('url', '?')}")
        li_pages = linkedin_data.get("pages", [])
        if li_pages:
            for p in li_pages:
                trace.append(f"  LinkedIn source: [{p.get('title','?')}] {p.get('url','')}")
        else:
            trace.append("  LinkedIn: no content from any strategy")

        # ── Step 5: build flat source list ──────────────────────────────────
        trace.append("Step 6: build evidence sources")
        sources = self._build_sources(client_data or {}, website_data, linkedin_data)
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

        return sources

    # ── Criterion evaluation (runs in thread pool) ──────────────────────────

    def _evaluate_criterion(
        self,
        criterion:    Dict[str, Any],
        all_chunks:   List[Dict[str, Any]],
        choices:      List[Dict[str, Any]],
        client_data:  Dict[str, Any],
        sources_meta: Dict[str, Any],
        query_emb:    Any,                 # pre-computed in main thread
    ) -> Tuple[Dict[str, Any], List[str]]:
        """
        Returns (criterion_result_dict, trace_lines).
        Thread-safe: writes only to local variables.
        """
        local_trace: List[str] = []
        label       = criterion.get("label", "")
        answer_type = criterion.get("answer_type") or "text"
        unit        = criterion.get("unit") or ""

        # ── Priority 1: CRM headcount direct (no LLM needed) ───────────────
        if answer_type == "numeric":
            crm_val = self._crm_headcount(client_data, label.lower())
            if crm_val is not None:
                display = str(int(crm_val)) if crm_val == int(crm_val) else str(crm_val)
                local_trace.append(f"  [{label[:50]}] → CRM direct: {display}")
                return self._criterion_result(
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
                ), local_trace

        # ── Priority 2: semantic retrieval + LLM extraction ─────────────────
        passages = self.retriever.retrieve(
            query_embedding=query_emb,
            query_text=label,
            chunks=all_chunks,
            top_k=3,           # reduced from 5 — tighter, faster context
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


def _display(value: Any) -> str:
    if value is None:
        return "unknown"
    if isinstance(value, float) and value == int(value):
        return str(int(value))
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    return str(value)
