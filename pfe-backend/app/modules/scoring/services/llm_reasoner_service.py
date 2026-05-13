from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from openai import OpenAI
from pydantic import BaseModel

from app.core.config import settings
from app.services.scoring.llm_extractor_service import (
    ExtractionResult,
    _parse_json,
    _safe_float,
)

logger = logging.getLogger(__name__)

REASONING_MODEL = None  # uses settings.ollama_model
MIN_CONFIDENCE = 0.40

_RECONCILE_SCHEMA = """{
  "selected_source_index": <integer index of the most reliable source, or null>,
  "final_value": <the best final answer value, or null>,
  "confidence": <float 0.0–1.0>,
  "is_valid": true or false,
  "reasoning": "<how the final answer was determined>"
}"""


class FinalAnswer(BaseModel):
    predicted_answer: str
    extracted_value: Optional[Any] = None
    confidence: float
    justification: Dict[str, Any]
    evidence: Optional[Dict[str, Any]] = None
    sources: Dict[str, Any] = {}


class LLMReasonerService:
    """
    Reconciles multiple ExtractionResults (one per evidence source) into a
    single FinalAnswer. Uses local Ollama when sources disagree.
    """

    def __init__(self) -> None:
        self._client = OpenAI(
            base_url=settings.ollama_base_url,
            api_key="ollama",
            timeout=300.0,
            max_retries=0,
        )
        self._model = settings.ollama_model

    # ── Public API ──────────────────────────────────────────────────────────

    def reconcile(
        self,
        criterion_label: str,
        answer_type: str,
        unit: str,
        extractions: List[ExtractionResult],
        sources_meta: Dict[str, Any],
    ) -> FinalAnswer:
        # Accept high-confidence results even when is_valid=false (small models miscalibrate it)
        valid = [
            e for e in extractions
            if e.found and e.confidence >= MIN_CONFIDENCE and (e.is_valid or e.confidence >= 0.70)
        ]

        if not valid:
            reasons = "; ".join(
                f"{e.source_label}: {e.reasoning[:100]}"
                for e in extractions
                if e.reasoning
            )
            return FinalAnswer(
                predicted_answer="unknown",
                extracted_value=None,
                confidence=0.10,
                justification={
                    "source": None,
                    "clickable_url": None,
                    "extracted_evidence": None,
                    "context_before": "",
                    "context_after": "",
                    "section": "",
                    "search_hint": "",
                    "reasoning": (
                        f"No source provided a semantically valid answer for «{criterion_label}». "
                        f"Checked {len(extractions)} source(s). "
                        + (f"Rejection details — {reasons}" if reasons else "")
                    ),
                },
                evidence=None,
                sources=sources_meta,
            )

        if len(valid) == 1:
            return self._build_final(valid[0], sources_meta, reasoning_override=None)

        # All sources agree → no extra LLM call needed
        if len({str(e.extracted_value) for e in valid}) == 1:
            best = max(valid, key=lambda e: e.confidence)
            return self._build_final(best, sources_meta, reasoning_override=None)

        # Multiple conflicting results → LLM reconciliation
        try:
            return self._llm_reconcile(criterion_label, answer_type, unit, valid, sources_meta)
        except Exception as exc:
            logger.error("Reconciliation LLM call failed: %s", exc)
            best = max(valid, key=lambda e: e.confidence)
            fa = self._build_final(best, sources_meta, reasoning_override=None)
            fa.justification["reasoning"] = (
                f"Multi-source reconciliation failed ({exc}). "
                f"Used highest-confidence source: {best.source_label} ({best.confidence:.2f})."
            )
            return fa

    # ── LLM reconciliation ──────────────────────────────────────────────────

    def _llm_reconcile(
        self,
        label: str,
        answer_type: str,
        unit: str,
        valid: List[ExtractionResult],
        sources_meta: Dict[str, Any],
    ) -> FinalAnswer:
        summary = "\n\n".join(
            f"Source {i} ({e.source_type} — {e.source_label}):\n"
            f"  Value      : {e.extracted_value}\n"
            f"  Evidence   : \"{e.evidence_sentence[:200]}\"\n"
            f"  Confidence : {e.confidence:.2f}\n"
            f"  Reasoning  : {e.reasoning[:200]}"
            for i, e in enumerate(valid)
        )
        prompt = (
            f"Reconcile these extractions for a company eligibility assessment.\n\n"
            f"CRITERION : {label}\n"
            f"TYPE      : {answer_type} | UNIT: {unit or 'not specified'}\n\n"
            f"EXTRACTIONS:\n{summary}\n\n"
            f"TASK: Choose the most reliable final answer.\n"
            f"- Prefer specific numbers over ranges\n"
            f"- Prefer website/LinkedIn data over CRM when CRM seems outdated\n"
            f"- Prefer higher-confidence sources\n"
            f"- Set is_valid=false if sources conflict irreconcilably\n\n"
            f"Respond with ONLY a valid JSON object matching this schema (no markdown, no extra text):\n"
            f"{_RECONCILE_SCHEMA}"
        )
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                max_tokens=256,
                temperature=0.0,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": "You are a data reconciliation assistant. Always respond with valid JSON only.",
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            raw = _parse_json(response.choices[0].message.content or "{}")
        except Exception as exc:
            logger.error("Reconciliation LLM error: %s", exc)
            raw = {}

        if not raw or not raw.get("is_valid"):
            best = max(valid, key=lambda e: e.confidence)
            return self._build_final(best, sources_meta, reasoning_override=None)

        idx = raw.get("selected_source_index")
        chosen = (
            valid[idx]
            if (idx is not None and isinstance(idx, int) and 0 <= idx < len(valid))
            else max(valid, key=lambda e: e.confidence)
        )
        fa = self._build_final(chosen, sources_meta, reasoning_override=raw.get("reasoning"))

        llm_value = raw.get("final_value")
        if llm_value is not None and str(llm_value) != str(chosen.extracted_value):
            fa.extracted_value = llm_value
            fa.predicted_answer = _display(llm_value)

        fa.confidence = _safe_float(raw.get("confidence", chosen.confidence))
        return fa

    # ── Builder ─────────────────────────────────────────────────────────────

    @staticmethod
    def _build_final(
        e: ExtractionResult,
        sources_meta: Dict[str, Any],
        reasoning_override: Optional[str],
    ) -> FinalAnswer:
        display = _display(e.extracted_value)
        highlighted = f"<<< {e.evidence_sentence} >>>" if e.evidence_sentence else ""
        search_hint = f"Search for: \"{e.evidence_sentence[:80]}\""
        if e.section:
            search_hint += f" under section \"{e.section}\""
        reasoning = reasoning_override or e.reasoning

        return FinalAnswer(
            predicted_answer=display,
            extracted_value=e.extracted_value,
            confidence=e.confidence,
            justification={
                "source": e.source_label,
                "clickable_url": e.clickable_url,
                "extracted_evidence": highlighted,
                "context_before": e.context_before,
                "context_after": e.context_after,
                "section": e.section,
                "search_hint": search_hint,
                "reasoning": reasoning,
            },
            evidence={
                "source_type": e.source_type,
                "source_url": e.source_url,
                "clickable_url": e.clickable_url,
                "source_label": e.source_label,
                "exact_quote": e.evidence_sentence,
                "highlighted_quote": highlighted,
                "context_before": e.context_before,
                "context_after": e.context_after,
                "section": e.section,
                "search_hint": search_hint,
            },
            sources=sources_meta,
        )


def _display(value: Any) -> str:
    if value is None:
        return "unknown"
    if isinstance(value, float) and value == int(value):
        return str(int(value))
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    return str(value)
