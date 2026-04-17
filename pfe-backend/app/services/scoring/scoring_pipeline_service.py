from __future__ import annotations

from typing import Any, Dict, List

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

        # Surface ES connectivity failure as an explicit error rather than silent nulls
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

        scored_criteria: List[Dict[str, Any]] = []
        for item in orchestration_result["criteria_results"]:
            choices = item.get("choices", [])

            score = self.score_mapper.map_criterion_score(
                criterion={"answer_type": item["answer_type"]},
                predicted_answer=item["predicted_answer"],
                extracted_value=item.get("extracted_value"),
                choices=choices,
            )
            max_score = self.score_mapper.get_max_score(choices)

            scored_criteria.append({
                "criterion_id": item["criterion_id"],
                "label": item["label"],
                "answer_type": item["answer_type"],
                "predicted_answer": item["predicted_answer"],
                "extracted_value": item.get("extracted_value"),
                "confidence": item["confidence"],
                "justification": item["justification"],
                "sources": item["sources"],
                "score": score,
                "max_score": max_score,
            })

        summary = self.score_mapper.aggregate(scored_criteria)
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
