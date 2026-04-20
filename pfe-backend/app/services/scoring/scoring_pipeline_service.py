from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.services.scoring.agent_orchestrator_service import AgentOrchestratorService
from app.services.scoring.score_mapper_service import ScoreMapperService


class ScoringPipelineService:
    def __init__(self) -> None:
        self.agent = AgentOrchestratorService()
        self.score_mapper = ScoreMapperService()

    def run(self, client_id: str, product_id: str) -> Dict[str, Any]:
        orchestration_result = self.agent.run(client_id=client_id, product_id=product_id)

        product = orchestration_result["product"]
        if not product:
            return {"error": f"Product '{product_id}' not found."}

        if orchestration_result["client_data"] is None:
            return {
                "error": "client_data_unavailable",
                "detail": (
                    f"Client '{client_id}' could not be retrieved from Elasticsearch. "
                    "Elasticsearch may be unreachable or the client_id does not exist. "
                    "Check /api/debug/es/health and /api/debug/es/client/{client_id}."
                ),
                "trace": orchestration_result["trace"],
            }

        # Build a lookup of raw criterion results by id
        raw_by_id: Dict[str, Dict[str, Any]] = {
            item["criterion_id"]: item
            for item in orchestration_result["criteria_results"]
        }
        # Build criterion order from original list (already deduplicated in data)
        criteria_order: List[str] = [
            item["criterion_id"] for item in orchestration_result["criteria_results"]
        ]

        scored_criteria, blocking_triggered = self._walk_tree(
            criteria_order, raw_by_id
        )

        summary = self.score_mapper.aggregate(scored_criteria, blocking_triggered)
        client_data = orchestration_result["client_data"] or {}

        return {
            "trace": orchestration_result["trace"],
            "client": {
                "client_id": client_data.get("client_id"),
                "client_name": client_data.get("client_name"),
                "sector": client_data.get("sector"),
                "website": client_data.get("website"),
                "linkedin": client_data.get("linkedin"),
            },
            "product": {
                "product_id": product.get("id"),
                "product_name": product.get("name"),
            },
            "summary": {
                "criteria_count": len(scored_criteria),
                **summary,
            },
            "criteria_results": scored_criteria,
        }

    # ------------------------------------------------------------------
    # Tree walker
    # Follows redirection_id links between criteria.
    # Stops immediately when a blocking choice is selected.
    # ------------------------------------------------------------------

    def _walk_tree(
        self,
        criteria_order: List[str],
        raw_by_id: Dict[str, Dict[str, Any]],
    ):
        visited: set = set()
        scored_criteria: List[Dict[str, Any]] = []
        blocking_triggered = False

        # Start from the first criterion and follow redirections
        current_id: Optional[str] = criteria_order[0] if criteria_order else None

        while current_id and current_id not in visited:
            visited.add(current_id)
            item = raw_by_id.get(current_id)
            if item is None:
                break

            choices: List[Dict[str, Any]] = item.get("choices", [])
            score, selected_choice = self.score_mapper.map_criterion_score_with_choice(
                predicted_answer=item["predicted_answer"],
                extracted_value=item.get("extracted_value"),
                choices=choices,
            )
            max_score = self.score_mapper.get_max_score(choices)

            is_blocking_hit = (
                selected_choice is not None
                and selected_choice.get("is_blocking", False)
            )

            scored_criteria.append({
                "criterion_id": item["criterion_id"],
                "label": item["label"],
                "answer_type": item["answer_type"],
                "predicted_answer": item["predicted_answer"],
                "extracted_value": item.get("extracted_value"),
                "confidence": item["confidence"],
                "justification": item["justification"],
                "evidence": item.get("evidence"),
                "sources": item["sources"],
                "score": score,
                "max_score": max_score,
                "is_blocking": is_blocking_hit,
            })

            if is_blocking_hit:
                blocking_triggered = True
                break

            # Follow redirection from selected choice, or advance sequentially
            next_id: Optional[str] = None
            if selected_choice:
                next_id = selected_choice.get("redirection_id")

            if not next_id:
                # No redirection — advance to next criterion in the original order
                try:
                    idx = list(raw_by_id.keys()).index(current_id)
                    remaining = [k for k in raw_by_id if k not in visited]
                    next_id = remaining[0] if remaining else None
                except (ValueError, IndexError):
                    next_id = None

            current_id = next_id

        return scored_criteria, blocking_triggered
