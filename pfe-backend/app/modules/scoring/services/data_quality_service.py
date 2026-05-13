from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel

_TIER_HIGH = 0.75
_TIER_MEDIUM = 0.50
_TIER_LOW = 0.40


def quality_tier(confidence: float, found: bool) -> str:
    if not found or confidence < _TIER_LOW:
        return "UNKNOWN"
    if confidence >= _TIER_HIGH:
        return "HIGH"
    if confidence >= _TIER_MEDIUM:
        return "MEDIUM"
    return "LOW"


class ConsistencyIssue(BaseModel):
    rule: str
    detail: str
    severity: str  # "warning" | "error"


class DataQualityReport(BaseModel):
    reliability_score: float
    coverage_rate: float
    avg_confidence: float
    tier_counts: Dict[str, int]
    source_breakdown: Dict[str, int]
    consistency_issues: List[ConsistencyIssue]
    flags: List[str]


class DataQualityService:
    """
    Post-scoring quality audit.

    Runs after the scoring tree walk; requires no LLM call.
    Produces a DataQualityReport that surfaces:
      - How many criteria were answered vs. unknown
      - Average extraction confidence
      - Cross-criterion consistency violations (e.g. alternants > headcount)
      - Human-readable flags for the reviewer
    """

    def evaluate(self, criteria_results: List[Dict[str, Any]]) -> DataQualityReport:
        tier_counts: Dict[str, int] = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "UNKNOWN": 0}
        source_counts: Dict[str, int] = {}
        confidences: List[float] = []
        found_count = 0

        for item in criteria_results:
            conf = float(item.get("confidence") or 0.0)
            found = (item.get("predicted_answer") or "unknown") != "unknown"

            tier = quality_tier(conf, found)
            tier_counts[tier] += 1
            confidences.append(conf)

            if found:
                found_count += 1

            # Count each distinct source_type that contributed data
            for stype in (item.get("sources") or {}):
                source_counts[stype] = source_counts.get(stype, 0) + 1

        n = len(criteria_results) or 1
        coverage = round(found_count / n, 2)
        avg_conf = round(sum(confidences) / len(confidences), 2) if confidences else 0.0

        # Reliability = weighted average of coverage, confidence, high-tier rate
        reliability = round(
            0.50 * coverage
            + 0.30 * avg_conf
            + 0.20 * (tier_counts["HIGH"] / n),
            2,
        )

        consistency_issues = self._check_consistency(criteria_results)
        flags = self._build_flags(coverage, avg_conf, tier_counts, n, consistency_issues)

        return DataQualityReport(
            reliability_score=reliability,
            coverage_rate=coverage,
            avg_confidence=avg_conf,
            tier_counts=tier_counts,
            source_breakdown=source_counts,
            consistency_issues=consistency_issues,
            flags=flags,
        )

    # ── Cross-criterion consistency rules ────────────────────────────────────

    def _check_consistency(
        self, criteria_results: List[Dict[str, Any]]
    ) -> List[ConsistencyIssue]:
        issues: List[ConsistencyIssue] = []

        # Collect numeric values by lowercased criterion label
        values: Dict[str, float] = {}
        for item in criteria_results:
            label = (item.get("label") or "").lower()
            val = item.get("extracted_value")
            if val is None:
                continue
            try:
                values[label] = float(val)
            except (TypeError, ValueError):
                pass

        effectif = self._find(values, ["effectif", "salarié", "employé", "headcount", "staff"])
        alternants = self._find(values, ["alternant", "apprenti"])
        recrutement = self._find(values, ["recrut", "embauche", "hiring"])

        # Rule 1 — alternants cannot exceed total headcount
        if effectif is not None and alternants is not None and alternants > effectif:
            issues.append(ConsistencyIssue(
                rule="alternants_exceed_headcount",
                detail=(
                    f"Extracted alternants ({alternants:.0f}) > total headcount ({effectif:.0f}). "
                    "One of these values was likely misextracted."
                ),
                severity="error",
            ))

        # Rule 2 — annual recruitment > 50% of headcount is implausible
        if effectif is not None and recrutement is not None and recrutement > effectif * 0.5:
            issues.append(ConsistencyIssue(
                rule="recruitment_exceeds_half_headcount",
                detail=(
                    f"Annual recruitment ({recrutement:.0f}) > 50% of headcount ({effectif:.0f}). "
                    "Verify whether this is a cumulative or annual figure."
                ),
                severity="warning",
            ))

        # Rule 3 — percentage values must be in [0, 100]
        pct_markers = ["taux", "part", "ratio", "pourcent", "%"]
        for label, val in values.items():
            if any(p in label for p in pct_markers) and not (0.0 <= val <= 100.0):
                issues.append(ConsistencyIssue(
                    rule="percentage_out_of_range",
                    detail=f"Criterion «{label}»: value {val} is outside [0, 100].",
                    severity="error",
                ))

        # Rule 4 — headcount of 1 is suspicious for a company being assessed
        if effectif is not None and effectif <= 1:
            issues.append(ConsistencyIssue(
                rule="suspiciously_low_headcount",
                detail=(
                    f"Extracted headcount is {effectif:.0f}. "
                    "This may be a parsing artifact (e.g. '1 site', '1 an')."
                ),
                severity="warning",
            ))

        return issues

    @staticmethod
    def _find(values: Dict[str, float], keywords: List[str]) -> Optional[float]:
        for label, val in values.items():
            if any(kw in label for kw in keywords):
                return val
        return None

    # ── Human-readable flags ─────────────────────────────────────────────────

    @staticmethod
    def _build_flags(
        coverage: float,
        avg_conf: float,
        tier_counts: Dict[str, int],
        n: int,
        issues: List[ConsistencyIssue],
    ) -> List[str]:
        flags: List[str] = []

        if coverage < 0.50:
            flags.append(
                f"Low data coverage: only {coverage * 100:.0f}% of criteria have answers. "
                "Manual review is recommended."
            )
        if avg_conf < 0.50:
            flags.append(
                f"Low average extraction confidence ({avg_conf:.2f}). "
                "Extracted values should be verified against source documents."
            )
        unknown_rate = tier_counts["UNKNOWN"] / n
        if unknown_rate > 0.40:
            flags.append(
                f"{tier_counts['UNKNOWN']} of {n} criteria returned no answer. "
                "The company's public data may be insufficient for a complete assessment."
            )
        if tier_counts.get("HIGH", 0) == 0:
            flags.append(
                "No criterion reached HIGH confidence. "
                "All answers should be treated as indicative only."
            )

        for issue in issues:
            prefix = "Consistency error" if issue.severity == "error" else "Consistency warning"
            flags.append(f"{prefix}: {issue.detail}")

        return flags
