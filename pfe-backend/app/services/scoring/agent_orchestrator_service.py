from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from app.tools.es_client_tool import ESClientTool
from app.tools.es_reference_tool import ESReferenceTool
from app.tools.website_crawl_tool import WebsiteCrawlTool
from app.tools.social_media_tool import SocialMediaTool
from app.services.enrichment.social_extractor import SocialExtractor


class AgentOrchestratorService:
    def __init__(self) -> None:
        self.client_tool = ESClientTool()
        self.reference_tool = ESReferenceTool()
        self.website_tool = WebsiteCrawlTool()
        self.social_tool = SocialMediaTool()
        self.social_extractor = SocialExtractor()

    def run(self, client_id: str, product_id: str) -> Dict[str, Any]:
        trace: List[str] = []

        trace.append("Step 1: load product reference and criteria")
        product = self.reference_tool.get_product(product_id)
        criteria = self.reference_tool.get_criteria(product_id)

        trace.append("Step 2: load choices for all criteria (single file read)")
        all_choices = self.reference_tool.get_all_choices_grouped()
        choices_by_criterion: Dict[str, List[Dict[str, Any]]] = {
            c["id"]: all_choices.get(c["id"], []) for c in criteria
        }

        trace.append("Step 3: load client account data from Elasticsearch")
        client_data = self.client_tool.run(client_id)
        if client_data is None:
            trace.append(f"WARNING: client '{client_id}' not found or Elasticsearch unreachable — pipeline continues with empty client data")

        trace.append("Step 4: crawl website")
        website_data = self.website_tool.run(client_data.get("website") if client_data else None)

        trace.append("Step 5: retrieve social media signals")
        social_data = self.social_tool.run(client_data or {}, website_data)

        trace.append("Step 6: resolve LinkedIn from all sources (CRM → crawl → meta/JSON-LD → name inference)")
        resolved_linkedin = self._resolve_linkedin(
            client_data=client_data or {},
            social_data=social_data,
            trace=trace,
        )
        if client_data:
            client_data = {**client_data, "linkedin": resolved_linkedin}

        trace.append("Step 7: build evidence bundle")
        evidence_bundle = {
            "client_data": client_data or {},
            "website_data": website_data,
            "social_data": social_data,
        }

        trace.append("Step 8: evaluate each criterion according to its answer_type")
        criterion_results = [
            self._evaluate_criterion(
                criterion,
                evidence_bundle,
                choices_by_criterion.get(criterion["id"], []),
            )
            for criterion in criteria
        ]

        return {
            "trace": trace,
            "product": product,
            "criteria": criteria,
            "client_data": client_data,
            "website_data": website_data,
            "social_data": social_data,
            "criteria_results": criterion_results,
        }

    # ------------------------------------------------------------------
    # LinkedIn multi-layer resolution
    # ------------------------------------------------------------------

    def _resolve_linkedin(
        self,
        client_data: Dict[str, Any],
        social_data: Dict[str, Any],
        trace: List[str],
    ) -> Optional[str]:
        # Layer 1 — CRM field (highest confidence, already in client_data)
        linkedin = client_data.get("linkedin")
        if linkedin:
            trace.append("  LinkedIn resolved from CRM field.")
            return linkedin

        # Layer 2 — Website social links extracted by the crawler
        linkedin = social_data.get("links", {}).get("linkedin")
        if linkedin:
            trace.append("  LinkedIn resolved from website social link.")
            return linkedin

        # Layer 3 — Deep website scrape (meta tags, JSON-LD, raw source)
        website = client_data.get("website")
        if website:
            linkedin = self.social_extractor.extract_linkedin(website)
            if linkedin:
                trace.append(f"  LinkedIn resolved by deep website scrape: {linkedin}")
                return linkedin

        # Layer 4 — Company name slug inference (last resort)
        company_name = client_data.get("client_name")
        if company_name:
            linkedin = self.social_extractor.infer_linkedin_from_name(company_name)
            if linkedin:
                trace.append(
                    f"  LinkedIn inferred from company name (heuristic — unverified): {linkedin}"
                )
                return linkedin

        trace.append("  LinkedIn could not be resolved from any source.")
        return None

    # ------------------------------------------------------------------
    # Context helpers
    # ------------------------------------------------------------------

    def _build_criterion_context(
        self,
        criterion: Dict[str, Any],
        evidence_bundle: Dict[str, Any],
    ) -> Dict[str, Any]:
        client_data = evidence_bundle["client_data"]
        website_data = evidence_bundle["website_data"]
        social_data = evidence_bundle["social_data"]

        website_snippets = [
            f"{page.get('title', '')} {page.get('snippet', '')}"
            for page in website_data.get("pages", [])
        ]

        return {
            "criterion_id": criterion.get("id"),
            "criterion_label": criterion.get("label"),
            "answer_type": criterion.get("answer_type"),
            "unit": criterion.get("unit"),
            "client_name": client_data.get("client_name"),
            "client_description": client_data.get("description"),
            "sector": client_data.get("sector"),
            "website": client_data.get("website"),
            "linkedin": client_data.get("linkedin"),
            "website_snippets": website_snippets,
            "social_snippets": social_data.get("snippets", []),
            # CRM direct values — ground truth, priority over web extraction
            "crm_employee_count": client_data.get("crm_employee_count"),
        }

    def _build_evidence_blob(self, context: Dict[str, Any]) -> str:
        return " ".join([
            context.get("client_description") or "",
            context.get("client_name") or "",
            context.get("sector") or "",
            " ".join(context.get("website_snippets", [])),
            " ".join(context.get("social_snippets", [])),
        ]).lower()

    def _build_sources(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "website": context.get("website"),
            "linkedin": context.get("linkedin"),
        }

    # ------------------------------------------------------------------
    # Criterion dispatch
    # ------------------------------------------------------------------

    def _evaluate_criterion(
        self,
        criterion: Dict[str, Any],
        evidence_bundle: Dict[str, Any],
        choices: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        context = self._build_criterion_context(criterion, evidence_bundle)
        answer_type = criterion.get("answer_type")

        if answer_type == "numeric":
            result = self._evaluate_numeric(context, choices)
        elif answer_type == "single_choice":
            result = self._evaluate_single_choice(context, choices)
        elif answer_type == "multiple_choice":
            result = self._evaluate_multiple_choice(context, choices)
        elif answer_type == "text":
            result = self._evaluate_text(context)
        else:
            result = self._evaluate_generic(context, answer_type)

        return {
            "criterion_id": criterion.get("id"),
            "label": criterion.get("label"),
            "answer_type": answer_type,
            **result,
            "default_score": int(criterion.get("default_score", 0) or 0),
            "choices": choices,
        }

    # ------------------------------------------------------------------
    # Evaluators per answer_type
    # ------------------------------------------------------------------

    @staticmethod
    def _crm_direct_value(context: Dict[str, Any], label_lower: str) -> Optional[float]:
        """
        Return a numeric value directly from a CRM-structured field when the
        criterion label matches a known dimension.  CRM data is always preferred
        over anything extracted from website text.
        """
        # Percentage criteria must never be answered with a headcount value
        _percentage_kws = ["part", "ratio", "taux", "%", "pourcent", "proportion"]
        is_percentage = any(kw in label_lower for kw in _percentage_kws)

        # Employee / headcount dimension (only when question is NOT asking for a %)
        _employee_kws = ["effectif", "salarié", "employé", "collaborateur",
                         "employee", "staff", "headcount", "workforce", "personnel",
                         "nombre d'effectif", "nombre de collaborateur"]
        if not is_percentage and any(kw in label_lower for kw in _employee_kws):
            ec = context.get("crm_employee_count")
            if ec is not None:
                try:
                    return float(ec)
                except (TypeError, ValueError):
                    pass
        return None

    # Keyword groups → ordered list of regex patterns to try (French + English)
    _NUMERIC_PATTERNS: List[tuple] = [
        # --- Employee / headcount ---
        (
            ["effectif", "salarié", "employé", "collaborateur", "personnel",
             "employee", "staff", "headcount", "workforce"],
            [
                r"(\d[\d\s]*)\s*(?:salariés?|employés?|effectifs?|collaborateurs?|personnels?|employees?|staff)\b",
                r"(?:effectif|workforce|headcount)\s+(?:de\s+|d[e']\s+)?(\d[\d\s]*)",
                r"(\d[\d\s,]+)\s*[-–]\s*\d[\d\s,]*\s*(?:salariés?|employés?|employees?)",
            ],
        ),
        # --- Percentage / ratio ---
        (
            ["alternant", "apprenti", "part", "ratio", "taux", "pourcentage", "percent"],
            [
                r"(\d+(?:[.,]\d+)?)\s*%",
                r"(\d+(?:[.,]\d+)?)\s*(?:pourcent(?:age)?|percent)\b",
                r"taux\s+(?:de\s+)?(\d+(?:[.,]\d+)?)",
            ],
        ),
        # --- Hire / recruitment count ---
        (
            ["recrutement", "embauche", "recrut", "hire", "postes"],
            [
                r"(\d+)\s*(?:recrutements?|embauches?|recrues?|hires?)\b",
                r"(?:recrut\w*|embauch\w*)\s+(?:environ\s+|de\s+)?(\d+)",
                r"(\d+)\s*(?:postes?\s+(?:à\s+)?(?:pourvoir|ouverts?))",
            ],
        ),
    ]

    def _evaluate_numeric(
        self, context: Dict[str, Any], choices: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        label_lower = (context.get("criterion_label") or "").lower()
        unit = (context.get("unit") or "").lower()

        # ── Priority 1: CRM structured field (ground truth, highest confidence) ──
        crm_value = self._crm_direct_value(context, label_lower)
        if crm_value is not None:
            display = int(crm_value) if crm_value == int(crm_value) else crm_value
            return {
                "predicted_answer": str(display),
                "extracted_value": crm_value,
                "confidence": 0.95,
                "justification": (
                    f"Value {display} {unit} read directly from CRM (Salesforce) — ground truth."
                ),
                "sources": self._build_sources(context),
            }

        evidence_blob = self._build_evidence_blob(context)

        # Derive plausible upper bound from choice thresholds
        choice_thresholds: List[float] = []
        for ch in choices:
            body = (ch.get("condition") or {}).get("body", "")
            m = re.search(r"(\d+(?:\.\d+)?)", body)
            if m:
                choice_thresholds.append(float(m.group(1)))
        upper_bound = max(choice_thresholds) * 100 if choice_thresholds else 1_000_000

        # 1. Try context-aware keyword patterns first
        for domain_keywords, patterns in self._NUMERIC_PATTERNS:
            if any(kw in label_lower or kw in unit for kw in domain_keywords):
                for pattern in patterns:
                    match = re.search(pattern, evidence_blob)
                    if match:
                        raw = match.group(1)
                        val = self._parse_number(raw)
                        if val is not None and 0 < val <= upper_bound:
                            display = int(val) if val == int(val) else val
                            return {
                                "predicted_answer": str(display),
                                "extracted_value": val,
                                "confidence": 0.70,
                                "justification": (
                                    f"Extracted {display} {unit} using domain pattern "
                                    f"matched on evidence."
                                ),
                                "sources": self._build_sources(context),
                            }

        # 2. Generic fallback: any plausible number in evidence
        raw_all = re.findall(r"\b(\d[\d\s]*(?:[.,]\d+)?)\b", evidence_blob)
        candidates: List[float] = []
        for n in raw_all:
            val = self._parse_number(n)
            if val is not None and 0 < val <= upper_bound:
                candidates.append(val)

        if candidates:
            best = candidates[0]
            display = int(best) if best == int(best) else best
            return {
                "predicted_answer": str(display),
                "extracted_value": best,
                "confidence": 0.45,
                "justification": (
                    f"Numeric value {display} {unit} found in evidence (generic extraction)."
                ),
                "sources": self._build_sources(context),
            }

        return {
            "predicted_answer": "unknown",
            "extracted_value": None,
            "confidence": 0.20,
            "justification": "No numeric value found in available evidence.",
            "sources": self._build_sources(context),
        }

    @staticmethod
    def _parse_number(raw: str) -> Optional[float]:
        """Parse a raw string into a float, handling French/European formatting."""
        try:
            # Remove spaces (French thousands separator), normalise decimal separator
            cleaned = raw.replace(" ", "").replace(",", ".")
            return float(cleaned)
        except (ValueError, AttributeError):
            return None

    def _evaluate_single_choice(
        self, context: Dict[str, Any], choices: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        if not choices:
            return {
                "predicted_answer": "unknown",
                "extracted_value": None,
                "confidence": 0.25,
                "justification": "No choices defined for this criterion.",
                "sources": self._build_sources(context),
            }

        evidence_blob = self._build_evidence_blob(context)

        # Direct label match in evidence (highest confidence)
        for choice in sorted(choices, key=lambda c: c.get("score", 0), reverse=True):
            label = (choice.get("label") or "").lower().strip()
            if label and label in evidence_blob:
                return {
                    "predicted_answer": choice.get("label", "unknown"),
                    "extracted_value": choice.get("label"),
                    "confidence": 0.75,
                    "justification": f"Label '{choice.get('label')}' matched directly in evidence.",
                    "sources": self._build_sources(context),
                }

        # Fallback: oui/non positive-signal inference
        positive_keywords = ["yes", "oui", "true", "confirmed", "applicable"]
        negative_keywords = ["no", "non", "false", "none", "pas", "aucun"]

        positive_hits = sum(1 for kw in positive_keywords if kw in evidence_blob)
        negative_hits = sum(1 for kw in negative_keywords if kw in evidence_blob)

        oui_choice = next(
            (c for c in choices if (c.get("label") or "").lower() in ["oui", "yes", "true"]),
            None,
        )
        non_choice = next(
            (c for c in choices if (c.get("label") or "").lower() in ["non", "no", "false"]),
            None,
        )

        if positive_hits > negative_hits and oui_choice:
            best = oui_choice
            conf = 0.55
        elif negative_hits > positive_hits and non_choice:
            best = non_choice
            conf = 0.55
        else:
            # Default to the first non-blocking choice
            best = next((c for c in choices if not c.get("is_blocking", False)), choices[0])
            conf = 0.35

        return {
            "predicted_answer": best.get("label", "unknown"),
            "extracted_value": best.get("label"),
            "confidence": conf,
            "justification": (
                f"Classified as '{best.get('label')}' based on signal balance in evidence "
                f"(positive={positive_hits}, negative={negative_hits})."
            ),
            "sources": self._build_sources(context),
        }

    def _evaluate_multiple_choice(
        self, context: Dict[str, Any], choices: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        if not choices:
            return {
                "predicted_answer": "unknown",
                "extracted_value": None,
                "confidence": 0.25,
                "justification": "No choices defined for this criterion.",
                "sources": self._build_sources(context),
            }

        evidence_blob = self._build_evidence_blob(context)
        matched = [
            c.get("label") for c in choices
            if (c.get("label") or "").lower().strip() in evidence_blob
        ]

        if matched:
            return {
                "predicted_answer": ", ".join(matched),
                "extracted_value": matched,
                "confidence": 0.65,
                "justification": f"Matched {len(matched)} option(s) from evidence: {matched}.",
                "sources": self._build_sources(context),
            }

        return {
            "predicted_answer": "unknown",
            "extracted_value": None,
            "confidence": 0.25,
            "justification": "No choice labels matched in available evidence.",
            "sources": self._build_sources(context),
        }

    def _evaluate_text(self, context: Dict[str, Any]) -> Dict[str, Any]:
        snippets = context.get("website_snippets", [])
        description = context.get("client_description") or ""

        text = next((s for s in snippets if s.strip()), description or None)

        if text:
            return {
                "predicted_answer": text[:300].strip(),
                "extracted_value": text[:300].strip(),
                "confidence": 0.50,
                "justification": "Text extracted from website evidence.",
                "sources": self._build_sources(context),
            }

        return {
            "predicted_answer": "no_data",
            "extracted_value": None,
            "confidence": 0.20,
            "justification": "No text content available in evidence.",
            "sources": self._build_sources(context),
        }

    def _evaluate_generic(
        self, context: Dict[str, Any], answer_type: Optional[str]
    ) -> Dict[str, Any]:
        return {
            "predicted_answer": "not_evaluated",
            "extracted_value": None,
            "confidence": 0.10,
            "justification": (
                f"Criterion type '{answer_type}' is not supported by the evaluation engine."
            ),
            "sources": self._build_sources(context),
        }
