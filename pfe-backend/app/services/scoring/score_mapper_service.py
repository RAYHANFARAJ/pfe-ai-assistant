from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


class ScoreMapperService:
    """
    Maps a criterion's extracted value to a score by evaluating it against
    the criterion's choices, which carry condition bodies and score weights.
    """

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
        choices = choices or []
        if not choices:
            return 0

        # Use the richer extracted_value when available; fall back to predicted_answer
        value_to_test = extracted_value if extracted_value is not None else predicted_answer

        for choice in choices:
            condition = choice.get("condition") or {}
            if self._evaluate_condition(value_to_test, condition):
                return choice.get("score", 0)

        return 0

    def get_max_score(self, choices: List[Dict[str, Any]]) -> int:
        """Highest score reachable by a non-blocking choice."""
        if not choices:
            return 0
        return max(
            (c.get("score", 0) for c in choices if not c.get("is_blocking", False)),
            default=0,
        )

    def aggregate(self, criteria_results: List[Dict[str, Any]]) -> Dict[str, Any]:
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
        }

    # ------------------------------------------------------------------
    # Condition evaluator
    # Handles the JS-style condition bodies stored in choice.condition.body:
    #   "return a < 500"   "return a >= 500"   "return a == 'oui'"
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
                val = float(
                    str(value).replace(",", ".").replace(" ", "")
                )
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

        # String equality: "return a == 'oui'"  /  "return a == \"oui\""
        m = re.match(r'return\s+a\s*==\s*[\'"](.+?)[\'"]', body)
        if m:
            operand = m.group(1).strip().lower()
            return str(value).strip().lower() == operand

        return False
