from __future__ import annotations

import json
import logging
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from app.core.config import settings
from app.core.types import ElasticsearchIndexes
from app.services.elasticsearch.base import AbstractElasticsearchService
from app.utils.text_utils import normalize_text, slugify, strip_html

logger = logging.getLogger(__name__)


class XtraReferenceService(AbstractElasticsearchService):
    def __init__(self) -> None:
        super().__init__()
        self.output_dir = Path("output")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def load_campaigns(self) -> List[Dict[str, Any]]:
        hits = self.search(
            index=ElasticsearchIndexes.XTRA_CAMPAIGN,
            query={"match_all": {}},
            size=settings.default_search_size,
        )
        campaigns = [hit.get("_source", {}) for hit in hits]
        logger.info("Campagnes chargées : %s", len(campaigns))
        return campaigns

    def load_questions(self) -> List[Dict[str, Any]]:
        hits = self.search(
            index=ElasticsearchIndexes.XTRA_QUESTION,
            query={"match_all": {}},
            size=settings.max_question_size,
        )
        questions = [hit.get("_source", {}) for hit in hits]
        logger.info("Questions chargées : %s", len(questions))
        return questions

    def load_choices(self) -> List[Dict[str, Any]]:
        hits = self.search(
            index=ElasticsearchIndexes.XTRA_CHOICE,
            query={"match_all": {}},
            size=settings.max_choice_size,
        )
        choices = [hit.get("_source", {}) for hit in hits]
        logger.info("Choix chargés : %s", len(choices))
        return choices

    def detect_product_name(self, title: str, sf_campaign_names: List[str]) -> str:
        title_upper = (title or "").upper()
        sf_blob = " | ".join(sf_campaign_names).upper()
        full_text = f"{title_upper} | {sf_blob}"

        rules = [
            ("CIR", "CIR"),
            ("CII", "CII"),
            ("CEE", "CEE"),
            ("DECARBONATION", "DECARBONATION"),
            ("SUBVENTION", "SUBVENTIONS"),
            ("FORMATION", "FORMATION"),
            ("BPO", "BPO RH"),
            ("HR", "RH"),
            ("NRJ", "ENERGIE"),
            ("ENERG", "ENERGIE"),
        ]

        for keyword, product_name in rules:
            if keyword in full_text:
                return product_name

        cleaned_title = normalize_text(title)
        return cleaned_title if cleaned_title else "UNKNOWN_PRODUCT"

    def normalize_answer_type(self, answer_type: Optional[str]) -> str:
        raw = (answer_type or "").strip().lower()

        mapping = {
            "bool": "yes_no",
            "boolean": "yes_no",
            "yes/no": "yes_no",
            "yes_no": "yes_no",
            "radio": "single_choice",
            "select": "single_choice",
            "single_choice": "single_choice",
            "checkbox": "multiple_choice",
            "multi_choice": "multiple_choice",
            "multiple_choice": "multiple_choice",
            "number": "numeric",
            "numeric": "numeric",
            "float": "numeric",
            "integer": "numeric",
            "int": "numeric",
            "text": "text",
            "string": "text",
            "free_text": "text",
            "date": "date",
        }

        return mapping.get(raw, raw if raw else "unknown")

    def build_agent_question_text(
        self,
        question_text: str,
        answer_type: Optional[str],
        unit: Optional[str],
    ) -> str:
        question = strip_html(question_text).rstrip(" ?.")
        normalized_type = self.normalize_answer_type(answer_type)

        parts = [f"Critère à évaluer : {question}."]

        if normalized_type == "yes_no":
            parts.append("Réponse attendue : yes or no.")
        elif normalized_type == "single_choice":
            parts.append("Réponse attendue : one value from a predefined list.")
        elif normalized_type == "multiple_choice":
            parts.append("Réponse attendue : one or more values from a predefined list.")
        elif normalized_type == "numeric":
            parts.append("Réponse attendue : a numeric value.")
        elif normalized_type == "date":
            parts.append("Réponse attendue : a date value.")
        elif normalized_type == "text":
            parts.append("Réponse attendue : a short text value.")
        else:
            parts.append(f"Réponse attendue : {normalized_type}.")

        if unit:
            parts.append(f"Unité attendue : {unit}.")

        return " ".join(parts)

    def build_products(
        self,
        campaigns: List[Dict[str, Any]],
    ) -> Tuple[Dict[str, Dict[str, str]], List[Dict[str, str]]]:
        campaign_to_product: Dict[str, Dict[str, str]] = {}
        name_to_product_id: Dict[str, str] = {}
        products: List[Dict[str, str]] = []
        counter = 1

        for campaign in campaigns:
            campaign_id = campaign.get("id")
            title = campaign.get("title", "")
            sf_campaigns = campaign.get("sf_campaigns", []) or []
            sf_campaign_names = [
                item.get("name", "") for item in sf_campaigns if isinstance(item, dict)
            ]

            product_name = self.detect_product_name(title, sf_campaign_names)

            if product_name not in name_to_product_id:
                product_id = f"P{counter:03d}"
                name_to_product_id[product_name] = product_id
                products.append({
                    "id": product_id,
                    "name": product_name,
                })
                counter += 1

            if campaign_id:
                campaign_to_product[campaign_id] = {
                    "id": name_to_product_id[product_name],
                    "name": product_name,
                }

        logger.info("Produits construits : %s", len(products))
        return campaign_to_product, products

    def clean_questions(
        self,
        questions: List[Dict[str, Any]],
        campaign_to_product: Dict[str, Dict[str, str]],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        valid_questions: List[Dict[str, Any]] = []
        orphan_questions: List[Dict[str, Any]] = []

        for question in questions:
            campaign_id = question.get("campaign_id")
            if campaign_id in campaign_to_product:
                valid_questions.append(question)
            else:
                orphan_questions.append(question)

        logger.info("Questions valides : %s", len(valid_questions))
        logger.warning("Questions orphelines : %s", len(orphan_questions))
        return valid_questions, orphan_questions

    def clean_choices(
        self,
        choices: List[Dict[str, Any]],
        valid_question_ids: Set[str],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        valid_choices: List[Dict[str, Any]] = []
        orphan_choices: List[Dict[str, Any]] = []

        for choice in choices:
            question_id = choice.get("question_id")
            if question_id in valid_question_ids:
                valid_choices.append(choice)
            else:
                orphan_choices.append(choice)

        logger.info("Choix valides : %s", len(valid_choices))
        logger.warning("Choix orphelins : %s", len(orphan_choices))
        return valid_choices, orphan_choices

    def transform_criteria(
        self,
        valid_questions: List[Dict[str, Any]],
        campaign_to_product: Dict[str, Dict[str, str]],
    ) -> List[Dict[str, Any]]:
        criteria: List[Dict[str, Any]] = []

        for question in valid_questions:
            campaign_id = question.get("campaign_id")
            product_info = campaign_to_product[campaign_id]

            criteria.append({
                "id": question.get("id"),
                "label": strip_html(question.get("text", "")),
                "label_normalized": slugify(strip_html(question.get("text", ""))),
                "agent_prompt": self.build_agent_question_text(
                question_text=question.get("text", ""),
                answer_type=question.get("answer_type"),
                unit=question.get("unit"),
),
                "expected_output": "",
                "product_id": product_info["id"],
                "campaign_id": campaign_id,
                "quiz_id": question.get("quiz_id"),
                "answer_type": self.normalize_answer_type(question.get("answer_type")),
                "can_pass": bool(question.get("can_pass", False)),
                "redirection_id": question.get("default_redirection"),
                "order": int(question.get("order", 0) or 0),
                "section_number": question.get("section_number"),
                "unit": question.get("unit", "") or "",
                "comment_enable": bool(question.get("comment_enable", False)),
                "default_score": int(question.get("default_score", 0) or 0),
                "is_main": bool(question.get("is_main", False)),
                "created_at": question.get("created_at"),
                "deleted_at": question.get("deleted_at"),
                "updated_at": question.get("updated_at"),
            })

        criteria.sort(key=lambda item: (item["product_id"], item["order"]))
        logger.info("Critères transformés : %s", len(criteria))
        return criteria

    def transform_choices(self, valid_choices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        output: List[Dict[str, Any]] = []

        for choice in valid_choices:
            raw_condition = choice.get("condition", {}) or {}

            output.append({
                "id": choice.get("id"),
                "criteria_id": choice.get("question_id"),
                "campaign_id": choice.get("campaign_id"),
                "quiz_id": choice.get("quiz_id"),
                "label": strip_html(choice.get("label", "")),
                "condition": {
                    "arg": raw_condition.get("args"),
                    "body": raw_condition.get("body"),
                },
                "score": int(choice.get("score", 0) or 0),
                "is_blocking": bool(choice.get("is_blocking", False)),
                "redirection_id": choice.get("redirection"),
                "created_at": choice.get("created_at"),
                "deleted_at": choice.get("deleted_at"),
                "updated_at": choice.get("updated_at"),
            })

        output.sort(key=lambda item: (item["criteria_id"] or "", item["label"] or ""))
        logger.info("Choix transformés : %s", len(output))
        return output

    def build_product_targets(
        self,
        campaigns: List[Dict[str, Any]],
        campaign_to_product: Dict[str, Dict[str, str]],
    ) -> List[Dict[str, Any]]:
        product_targets: List[Dict[str, Any]] = []
        seen = set()
        counter = 1

        for campaign in campaigns:
            xtra_campaign_id = campaign.get("id")
            product_info = campaign_to_product.get(xtra_campaign_id)
            if not product_info:
                continue

            sf_campaigns = campaign.get("sf_campaigns", []) or []
            for sf_campaign in sf_campaigns:
                if not isinstance(sf_campaign, dict):
                    continue

                sf_campaign_id = sf_campaign.get("id")
                if not sf_campaign_id:
                    continue

                key = (sf_campaign_id, product_info["id"])
                if key in seen:
                    continue

                seen.add(key)

                product_targets.append({
                    "id": f"PT{counter:03d}",
                    "sf_campaign_id": sf_campaign_id,
                    "product_id": product_info["id"],
                    "sf_campaign_name": sf_campaign.get("name"),
                    "xtra_campaign_id": xtra_campaign_id,
                })
                counter += 1

        logger.info("Product targets construits : %s", len(product_targets))
        return product_targets

    def build_product_structure(
        self,
        products: List[Dict[str, Any]],
        criteria: List[Dict[str, Any]],
        choices: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        choices_by_criteria: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for choice in choices:
            criteria_id = choice.get("criteria_id")
            if criteria_id:
                choices_by_criteria[criteria_id].append(choice)

        criteria_by_product: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for criterion in criteria:
            enriched = dict(criterion)
            enriched["choices"] = sorted(
                choices_by_criteria.get(criterion["id"], []),
                key=lambda item: item.get("label") or "",
            )
            criteria_by_product[criterion["product_id"]].append(enriched)

        result: List[Dict[str, Any]] = []
        for product in sorted(products, key=lambda item: item["id"]):
            result.append({
                "product_id": product["id"],
                "product_name": product["name"],
                "criteria": sorted(
                    criteria_by_product.get(product["id"], []),
                    key=lambda item: item["order"],
                ),
            })

        logger.info("Structure produit finale construite : %s produits", len(result))
        return result

    def save_json(self, filename: str, data: Any) -> Path:
        path = self.output_dir / filename
        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
        logger.info("Fichier sauvegardé : %s", path)
        return path

    def run(self) -> Dict[str, Any]:
        campaigns = self.load_campaigns()
        questions = self.load_questions()
        choices = self.load_choices()

        campaign_to_product, products = self.build_products(campaigns)

        valid_questions, orphan_questions = self.clean_questions(questions, campaign_to_product)
        valid_question_ids = {q.get("id") for q in valid_questions if q.get("id")}

        valid_choices, orphan_choices = self.clean_choices(choices, valid_question_ids)

        criteria = self.transform_criteria(valid_questions, campaign_to_product)
        choices_out = self.transform_choices(valid_choices)
        product_targets = self.build_product_targets(campaigns, campaign_to_product)
        product_structure = self.build_product_structure(products, criteria, choices_out)

        reference_bundle = {
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "products": len(products),
                "criteria": len(criteria),
                "choices": len(choices_out),
                "product_targets": len(product_targets),
                "orphan_questions": len(orphan_questions),
                "orphan_choices": len(orphan_choices),
            },
            "product": products,
            "criteria": criteria,
            "choice": choices_out,
            "product_target": product_targets,
            "product_structure": product_structure,
        }

        self.save_json("products.json", products)
        self.save_json("criteria.json", criteria)
        self.save_json("choice.json", choices_out)
        self.save_json("product_target.json", product_targets)
        self.save_json("product_structure.json", product_structure)
        self.save_json("orphan_questions.json", orphan_questions)
        self.save_json("orphan_choices.json", orphan_choices)
        self.save_json("reference_bundle.json", reference_bundle)

        return reference_bundle
