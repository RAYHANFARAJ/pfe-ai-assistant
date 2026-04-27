from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple


class ScoreMapperService:

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def map_criterion_score(
        self,
        criterion: Dict[str, Any],
        predicted_answer: str,
        extracted_value: Any = None,
        choices: Optional[List[Dict[str, Any]]] = None,
    ) -> int:
        score, _ = self.map_criterion_score_with_choice(
            predicted_answer=predicted_answer,
            extracted_value=extracted_value,
            choices=choices or [],
        )
        return score

    def map_criterion_score_with_choice(
        self,
        predicted_answer: str,
        extracted_value: Any = None,
        choices: Optional[List[Dict[str, Any]]] = None,
    ) -> Tuple[int, Optional[Dict[str, Any]]]:
        """Return (score, matched_choice). matched_choice carries redirection_id and is_blocking."""
        choices = choices or []
        if not choices:
            return 0, None

        value_to_test = extracted_value if extracted_value is not None else predicted_answer

        # Evaluate highest-scoring non-blocking choices first so that
        # overlapping conditions (e.g. "> 25" and "> 50") always award
        # the maximum deserved score rather than the first match.
        ranked = sorted(choices, key=lambda c: c.get("score", 0), reverse=True)
        for choice in ranked:
            condition = choice.get("condition") or {}
            if self._evaluate_condition(value_to_test, condition):
                return choice.get("score", 0), choice

        return 0, None

    def get_max_score(self, choices: List[Dict[str, Any]]) -> int:
        """Highest score reachable by a non-blocking choice."""
        if not choices:
            return 0
        return max(
            (c.get("score", 0) for c in choices if not c.get("is_blocking", False)),
            default=0,
        )

    def aggregate(
        self,
        criteria_results: List[Dict[str, Any]],
        blocking_triggered: bool = False,
    ) -> Dict[str, Any]:
        # If any blocking choice was hit, the entire scoring resets to zero
        if blocking_triggered:
            return {
                "total_score": 0,
                "max_score": sum(item.get("max_score", 0) for item in criteria_results),
                "normalized_score": 0.0,
                "eligibility_status": "not_eligible",
                "blocking_triggered": True,
            }

        total_score = sum(item.get("score", 0) for item in criteria_results)
        max_score = sum(item.get("max_score", 0) for item in criteria_results)
        normalized_score = round(total_score / max_score, 2) if max_score else 0.0

        if normalized_score >= 0.75:
            status = "eligible"
        elif normalized_score >= 0.40:
            status = "to_review"
        else:
            status = "not_eligible"

        return {
            "total_score": total_score,
            "max_score": max_score,
            "normalized_score": normalized_score,
            "eligibility_status": status,
            "blocking_triggered": False,
        }

    # ------------------------------------------------------------------
    # Condition evaluator
    # ------------------------------------------------------------------

    def _evaluate_condition(self, value: Any, condition: Dict[str, Any]) -> bool:
        body = (condition.get("body") or "").strip()
        if not body:
            return False

        # Numeric comparison: "return a <op> <number>"
        m = re.match(
            r"return\s+a\s*([<>]=?|==|!=)\s*(\d+(?:\.\d+)?)",
            body,
        )
        if m:
            op, operand = m.group(1), float(m.group(2))
            try:
                val = float(str(value).replace(",", ".").replace(" ", ""))
            except (TypeError, ValueError):
                return False
            return {
                "<":  val < operand,
                ">":  val > operand,
                "<=": val <= operand,
                ">=": val >= operand,
                "==": val == operand,
                "!=": val != operand,
            }.get(op, False)

        # String equality: "return a == 'OUI'" — case-insensitive
        m = re.match(r'return\s+a\s*==\s*[\'"](.+?)[\'"]', body)
        if m:
            operand = m.group(1).strip().lower()
            return str(value).strip().lower() == operand

        return False
