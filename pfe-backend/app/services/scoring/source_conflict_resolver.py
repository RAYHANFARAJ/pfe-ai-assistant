from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Source credibility ranks — used to break ties when values conflict.
# These reflect data freshness and editorial control, not absolute trust.
# ---------------------------------------------------------------------------
_CREDIBILITY: Dict[str, float] = {
    "crm":             0.90,   # Structured CRM field — highest authority
    "website":         0.82,   # Official company website — usually up-to-date
    "linkedin":        0.72,   # LinkedIn company page — good for headcount
    "news":            0.62,   # Press / news articles — good recency, less precise
    "crm_description": 0.55,   # Free-text CRM description — lower reliability
}

# CRM numeric values that almost certainly represent "not filled in" or a
# placeholder rather than a real measurement.
_CRM_SUSPICIOUS_NUMERIC = {0.0, 1.0}

# If two numeric values diverge by more than this fraction, flag a conflict.
_CONFLICT_THRESHOLD = 0.20   # 20 %


class SourceConflictResolver:
    """
    Decides which source wins when multiple sources supply data for the same
    criterion.  Operates on a list of CandidateExtraction dicts.

    Each candidate dict must have:
        source_type: str          — one of the keys in _CREDIBILITY
        value:       Any          — the extracted value (numeric, label, text)
        confidence:  float 0–1    — the extractor's own confidence
        evidence:    str          — verbatim evidence sentence
        source_label: str         — human-readable source name
        source_url:  str | None

    Returns a ResolutionResult (plain dict) with:
        selected_candidate: dict  — the winning candidate
        conflict_detected:  bool
        all_candidates:     list[dict]   — all candidates for display
        reasoning:          str
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def resolve(
        self,
        candidates: List[Dict[str, Any]],
        criterion_label: str,
        answer_type: str = "numeric",
    ) -> Dict[str, Any]:
        """
        Select the best candidate from a list, applying conflict-detection
        and credibility-weighted scoring.
        """
        valid = [c for c in candidates if c.get("value") is not None]
        if not valid:
            return self._no_result(candidates, criterion_label)

        if len(valid) == 1:
            return self._single(valid[0], candidates)

        if answer_type == "numeric":
            return self._resolve_numeric(valid, candidates, criterion_label)
        else:
            return self._resolve_categorical(valid, candidates, criterion_label)

    # ------------------------------------------------------------------
    # Numeric resolution
    # ------------------------------------------------------------------

    def _resolve_numeric(
        self,
        valid: List[Dict[str, Any]],
        all_candidates: List[Dict[str, Any]],
        label: str,
    ) -> Dict[str, Any]:
        values = [float(c["value"]) for c in valid]
        min_v, max_v = min(values), max(values)

        conflict = (max_v > 0) and ((max_v - min_v) / max_v > _CONFLICT_THRESHOLD)

        # Check for suspicious CRM value
        crm = next((c for c in valid if c["source_type"] == "crm"), None)
        crm_suspicious = (
            crm is not None and float(crm["value"]) in _CRM_SUSPICIOUS_NUMERIC
        )

        if crm_suspicious:
            # Ignore the placeholder CRM value — prefer web sources
            non_crm = [c for c in valid if c["source_type"] != "crm"]
            if non_crm:
                best = self._top(non_crm)
                return {
                    "selected_candidate": best,
                    "conflict_detected":  True,
                    "all_candidates":     all_candidates,
                    "reasoning": (
                        f"CRM value ({int(crm['value'])}) is a known placeholder/default. "
                        f"Selected {best['source_type'].upper()} value "
                        f"({_fmt(best['value'])}) with {best['confidence']:.0%} confidence."
                    ),
                }

        # Check if web sources agree with each other but conflict with CRM
        # → CRM is likely stale (e.g., only French entity entered, not global group)
        if crm is not None and conflict:
            non_crm = [c for c in valid if c["source_type"] != "crm"]
            if len(non_crm) >= 2:
                non_crm_values = [float(c["value"]) for c in non_crm]
                web_min, web_max = min(non_crm_values), max(non_crm_values)
                web_agree = (web_max > 0) and ((web_max - web_min) / web_max <= _CONFLICT_THRESHOLD)
                crm_v = float(crm["value"])
                crm_vs_web_diverge = (web_max > 0) and abs(crm_v - web_max) / web_max > 0.50
                if web_agree and crm_vs_web_diverge:
                    best = self._top(non_crm)
                    pct = round(abs(crm_v - web_max) / web_max * 100)
                    return {
                        "selected_candidate": best,
                        "conflict_detected":  True,
                        "all_candidates":     all_candidates,
                        "reasoning": (
                            f"CRM value ({_fmt(crm_v)}) diverges from web sources by {pct}%, "
                            f"but website and LinkedIn agree ({_fmt(web_min)}–{_fmt(web_max)}). "
                            f"CRM likely stale or scoped to a sub-entity. "
                            f"Selected {best['source_type'].upper()} ({_fmt(best['value'])})."
                        ),
                    }

        if not conflict:
            best = self._top(valid)
            sources_str = ", ".join(
                f"{c['source_type']}={_fmt(c['value'])}" for c in valid if c != best
            )
            return {
                "selected_candidate": best,
                "conflict_detected":  False,
                "all_candidates":     all_candidates,
                "reasoning": (
                    f"Sources agree (values within {_CONFLICT_THRESHOLD*100:.0f}%). "
                    f"Selected {best['source_type'].upper()} ({_fmt(best['value'])})"
                    + (f"; corroborated by {sources_str}." if sources_str else ".")
                ),
            }

        # Real conflict — rank and explain
        ranked = sorted(valid, key=lambda c: _score(c), reverse=True)
        best = ranked[0]
        losers = ", ".join(
            f"{c['source_type']}={_fmt(c['value'])} (cred {_CREDIBILITY.get(c['source_type'],0.5):.2f})"
            for c in ranked[1:]
        )
        pct = round((max_v - min_v) / max_v * 100)
        return {
            "selected_candidate": best,
            "conflict_detected":  True,
            "all_candidates":     all_candidates,
            "reasoning": (
                f"CONFLICT — values diverge by {pct}% "
                f"({' vs '.join(_fmt(v) for v in values)}). "
                f"Selected {best['source_type'].upper()} "
                f"(credibility={_CREDIBILITY.get(best['source_type'],0.5):.2f} × "
                f"confidence={best['confidence']:.2f}) over {losers}."
            ),
        }

    # ------------------------------------------------------------------
    # Categorical / choice resolution
    # ------------------------------------------------------------------

    def _resolve_categorical(
        self,
        valid: List[Dict[str, Any]],
        all_candidates: List[Dict[str, Any]],
        label: str,
    ) -> Dict[str, Any]:
        # Majority vote weighted by credibility × confidence
        tally: Dict[str, float] = {}
        for c in valid:
            key = str(c["value"]).strip().lower()
            tally[key] = tally.get(key, 0.0) + _score(c)

        best_label = max(tally, key=lambda k: tally[k])
        # Find the highest-scoring candidate whose value matches the winner
        winner_candidates = [
            c for c in valid
            if str(c["value"]).strip().lower() == best_label
        ]
        best = self._top(winner_candidates)

        conflict = len(tally) > 1
        return {
            "selected_candidate": best,
            "conflict_detected":  conflict,
            "all_candidates":     all_candidates,
            "reasoning": (
                f"{'CONFLICT — ' if conflict else ''}"
                f"Selected '{best['value']}' from {best['source_type'].upper()} "
                f"(weighted score {tally[best_label]:.2f})."
                if conflict else
                f"All sources agree on '{best['value']}'. "
                f"Selected {best['source_type'].upper()} (highest credibility)."
            ),
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _top(candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        return max(candidates, key=lambda c: _score(c))

    @staticmethod
    def _single(candidate: Dict[str, Any], all_cands: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "selected_candidate": candidate,
            "conflict_detected":  False,
            "all_candidates":     all_cands,
            "reasoning": (
                f"Single source: {candidate['source_type'].upper()} "
                f"({_fmt(candidate['value'])}), confidence {candidate['confidence']:.0%}."
            ),
        }

    @staticmethod
    def _no_result(
        all_cands: List[Dict[str, Any]], label: str
    ) -> Dict[str, Any]:
        return {
            "selected_candidate": None,
            "conflict_detected":  False,
            "all_candidates":     all_cands,
            "reasoning": f"No valid value found for '{label}' from any source.",
        }


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def _score(c: Dict[str, Any]) -> float:
    cred = _CREDIBILITY.get(c.get("source_type", ""), 0.5)
    conf = float(c.get("confidence", 0.5))
    return cred * conf


def _fmt(value: Any) -> str:
    try:
        f = float(value)
        return str(int(f)) if f == int(f) else str(f)
    except (TypeError, ValueError):
        return str(value)
