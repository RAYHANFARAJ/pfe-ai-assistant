from __future__ import annotations

import json
import logging
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
from requests.auth import HTTPBasicAuth


# =========================
# Configuration
# =========================
ES_HOST = "http://10.0.4.125:9200"
ES_USERNAME = "data_guest"
ES_PASSWORD = "data_guest"

INDEX_XTRA_CAMPAIGN = "xtra_campaign"
INDEX_XTRA_QUESTION = "xtra_question"
INDEX_XTRA_CHOICE = "xtra_choice"

AUTH = HTTPBasicAuth(ES_USERNAME, ES_PASSWORD)
HEADERS = {"Content-Type": "application/json"}

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
LOG_DIR = BASE_DIR / "logs"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = LOG_DIR / f"build_reference_{TIMESTAMP}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# =========================
# Helpers Elasticsearch
# =========================
def es_search(index: str, query: Dict[str, Any], size: int = 1000) -> List[Dict[str, Any]]:
    url = f"{ES_HOST}/{index}/_search"
    payload = {"size": size, "query": query}
    response = requests.post(url, auth=AUTH, headers=HEADERS, json=payload, timeout=60)
    response.raise_for_status()
    data = response.json()
    return data.get("hits", {}).get("hits", [])


# =========================
# Helpers texte / normalisation
# =========================
def normalize_text(value: Optional[str]) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def strip_html(value: Optional[str]) -> str:
    text = value or ""
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    return normalize_text(text)


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "unknown"


def detect_product_name(title: str, sf_campaign_names: List[str]) -> str:
    """
    Déduit le nom produit à partir du title Xtra et/ou des campagnes SF associées.
    Adapte les règles si besoin.
    """
    title_u = (title or "").upper()
    sf_blob = " | ".join(sf_campaign_names).upper()
    text = f"{title_u} | {sf_blob}"

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
        if keyword in text:
            return product_name

    cleaned = normalize_text(title)
    return cleaned if cleaned else "UNKNOWN_PRODUCT"


def build_agent_question_text(
    question_text: str,
    answer_type: Optional[str],
    unit: Optional[str],
    can_pass: bool
) -> str:
    """
    Reformule la question dans un format plus exploitable par un agent.
    """
    q = strip_html(question_text)
    q = q.rstrip(" ?.")

    parts = [f"Critère à évaluer : {q}."]
    if answer_type:
        parts.append(f"Type de réponse attendu : {answer_type}.")
    if unit:
        parts.append(f"Unité attendue : {unit}.")
    parts.append("Question passable." if can_pass else "Question non passable.")

    return " ".join(parts)


# =========================
# Chargement brut
# =========================
def load_campaigns() -> List[Dict[str, Any]]:
    hits = es_search(INDEX_XTRA_CAMPAIGN, {"match_all": {}}, size=1000)
    campaigns = [h.get("_source", {}) for h in hits]
    logger.info("Campagnes chargées : %s", len(campaigns))
    return campaigns


def load_questions() -> List[Dict[str, Any]]:
    hits = es_search(INDEX_XTRA_QUESTION, {"match_all": {}}, size=5000)
    questions = [h.get("_source", {}) for h in hits]
    logger.info("Questions chargées : %s", len(questions))
    return questions


def load_choices() -> List[Dict[str, Any]]:
    hits = es_search(INDEX_XTRA_CHOICE, {"match_all": {}}, size=5000)
    choices = [h.get("_source", {}) for h in hits]
    logger.info("Choices chargés : %s", len(choices))
    return choices


# =========================
# Construction products
# =========================
def build_products(campaigns: List[Dict[str, Any]]) -> Tuple[Dict[str, Dict[str, str]], List[Dict[str, str]]]:
    """
    Retourne :
    - campaign_id -> {"id": product_id, "name": product_name}
    - liste de produits uniques
    """
    name_to_product_id: Dict[str, str] = {}
    campaign_to_product: Dict[str, Dict[str, str]] = {}
    products: List[Dict[str, str]] = []
    counter = 1

    for src in campaigns:
        campaign_id = src.get("id")
        title = src.get("title", "")
        sf_campaigns = src.get("sf_campaigns", []) or []
        sf_campaign_names = [c.get("name", "") for c in sf_campaigns if isinstance(c, dict)]

        product_name = detect_product_name(title, sf_campaign_names)

        if product_name not in name_to_product_id:
            product_id = f"P{counter:03d}"
            name_to_product_id[product_name] = product_id
            products.append({
                "id": product_id,
                "name": product_name
            })
            counter += 1

        if campaign_id:
            campaign_to_product[campaign_id] = {
                "id": name_to_product_id[product_name],
                "name": product_name
            }

    logger.info("Produits construits : %s", len(products))
    return campaign_to_product, products


# =========================
# Nettoyage et transformation
# =========================
def clean_questions(
    questions: List[Dict[str, Any]],
    campaign_to_product: Dict[str, Dict[str, str]]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Garde uniquement les questions reliées à une campagne connue.
    Retourne :
    - valid_questions
    - orphan_questions
    """
    valid_questions: List[Dict[str, Any]] = []
    orphan_questions: List[Dict[str, Any]] = []

    for q in questions:
        campaign_id = q.get("campaign_id")
        if campaign_id in campaign_to_product:
            valid_questions.append(q)
        else:
            orphan_questions.append(q)

    logger.info("Questions valides : %s", len(valid_questions))
    logger.warning("Questions orphelines : %s", len(orphan_questions))
    return valid_questions, orphan_questions


def clean_choices(
    choices: List[Dict[str, Any]],
    valid_question_ids: set[str]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Garde uniquement les choices reliés à une question valide.
    Retourne :
    - valid_choices
    - orphan_choices
    """
    valid_choices: List[Dict[str, Any]] = []
    orphan_choices: List[Dict[str, Any]] = []

    for ch in choices:
        question_id = ch.get("question_id")
        if question_id in valid_question_ids:
            valid_choices.append(ch)
        else:
            orphan_choices.append(ch)

    logger.info("Choices valides : %s", len(valid_choices))
    logger.warning("Choices orphelins : %s", len(orphan_choices))
    return valid_choices, orphan_choices


def transform_criteria(
    valid_questions: List[Dict[str, Any]],
    campaign_to_product: Dict[str, Dict[str, str]]
) -> List[Dict[str, Any]]:
    criteria: List[Dict[str, Any]] = []

    for q in valid_questions:
        campaign_id = q.get("campaign_id")
        product_info = campaign_to_product[campaign_id]
        product_id = product_info["id"]

        criteria.append({
            "id": q.get("id"),
            "label": strip_html(q.get("text", "")),
            "label_normalized": slugify(strip_html(q.get("text", ""))),
            "agent_prompt": build_agent_question_text(
                question_text=q.get("text", ""),
                answer_type=q.get("answer_type"),
                unit=q.get("unit"),
                can_pass=bool(q.get("can_pass", False)),
            ),
            "expected_output": "",
            "product_id": product_id,
            "campaign_id": campaign_id,
            "quiz_id": q.get("quiz_id"),
            "answer_type": q.get("answer_type"),
            "can_pass": bool(q.get("can_pass", False)),
            "redirection_id": q.get("default_redirection"),
            "order": int(q.get("order", 0) or 0),
            "section_number": q.get("section_number"),
            "unit": q.get("unit", "") or "",
            "comment_enable": bool(q.get("comment_enable", False)),
            "default_score": int(q.get("default_score", 0) or 0),
            "is_main": bool(q.get("is_main", False)),
            "created_at": q.get("created_at"),
            "deleted_at": q.get("deleted_at"),
            "updated_at": q.get("updated_at"),
        })

    criteria.sort(key=lambda x: (x["product_id"], x["order"]))
    logger.info("Criteria transformés : %s", len(criteria))
    return criteria


def transform_choices(valid_choices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    choices_out: List[Dict[str, Any]] = []

    for ch in valid_choices:
        raw_condition = ch.get("condition", {}) or {}

        choices_out.append({
            "id": ch.get("id"),
            "criteria_id": ch.get("question_id"),
            "campaign_id": ch.get("campaign_id"),
            "quiz_id": ch.get("quiz_id"),
            "label": strip_html(ch.get("label", "")),
            "condition": {
                "arg": raw_condition.get("args"),
                "body": raw_condition.get("body"),
            },
            "score": int(ch.get("score", 0) or 0),
            "is_blocking": bool(ch.get("is_blocking", False)),
            "redirection_id": ch.get("redirection"),
            "created_at": ch.get("created_at"),
            "deleted_at": ch.get("deleted_at"),
            "updated_at": ch.get("updated_at"),
        })

    choices_out.sort(key=lambda x: (x["criteria_id"] or "", x["label"] or ""))
    logger.info("Choices transformés : %s", len(choices_out))
    return choices_out


def build_product_targets(
    campaigns: List[Dict[str, Any]],
    campaign_to_product: Dict[str, Dict[str, str]]
) -> List[Dict[str, Any]]:
    product_targets: List[Dict[str, Any]] = []
    seen = set()
    counter = 1

    for src in campaigns:
        xtra_campaign_id = src.get("id")
        product_info = campaign_to_product.get(xtra_campaign_id)
        if not product_info:
            continue

        sf_campaigns = src.get("sf_campaigns", []) or []
        for sf in sf_campaigns:
            if not isinstance(sf, dict):
                continue

            sf_campaign_id = sf.get("id")
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
                "sf_campaign_name": sf.get("name"),
                "xtra_campaign_id": xtra_campaign_id,
            })
            counter += 1

    logger.info("Product targets construits : %s", len(product_targets))
    return product_targets


def build_product_structure(
    products: List[Dict[str, Any]],
    criteria: List[Dict[str, Any]],
    choices: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    choices_by_criteria: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for ch in choices:
        criteria_id = ch.get("criteria_id")
        if criteria_id:
            choices_by_criteria[criteria_id].append(ch)

    criteria_by_product: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for c in criteria:
        enriched = dict(c)
        enriched["choices"] = sorted(
            choices_by_criteria.get(c["id"], []),
            key=lambda x: (x.get("label") or "")
        )
        criteria_by_product[c["product_id"]].append(enriched)

    result: List[Dict[str, Any]] = []
    for p in sorted(products, key=lambda x: x["id"]):
        result.append({
            "product_id": p["id"],
            "product_name": p["name"],
            "criteria": sorted(criteria_by_product.get(p["id"], []), key=lambda x: x["order"])
        })

    logger.info("Structure produit finale construite : %s produits", len(result))
    return result


# =========================
# Sauvegarde
# =========================
def save_json(filename: str, data: Any) -> Path:
    path = OUTPUT_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info("Fichier sauvegardé : %s", path)
    return path


# =========================
# Main
# =========================
def main() -> None:
    logger.info("=== Début du script de construction du référentiel ===")

    campaigns = load_campaigns()
    questions = load_questions()
    choices = load_choices()

    campaign_to_product, products = build_products(campaigns)

    valid_questions, orphan_questions = clean_questions(questions, campaign_to_product)
    valid_question_ids = {q.get("id") for q in valid_questions if q.get("id")}

    valid_choices, orphan_choices = clean_choices(choices, valid_question_ids)

    criteria = transform_criteria(valid_questions, campaign_to_product)
    choices_out = transform_choices(valid_choices)
    product_targets = build_product_targets(campaigns, campaign_to_product)

    product_structure = build_product_structure(products, criteria, choices_out)

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

    # Sauvegardes principales
    save_json("products.json", products)
    save_json("criteria.json", criteria)
    save_json("choice.json", choices_out)
    save_json("product_target.json", product_targets)
    save_json("product_structure.json", product_structure)
    save_json("orphan_questions.json", orphan_questions)
    save_json("orphan_choices.json", orphan_choices)
    save_json("reference_bundle.json", reference_bundle)

    # Aperçu console
    print(json.dumps(reference_bundle["summary"], ensure_ascii=False, indent=2))

    logger.info("=== Fin du script ===")
    logger.info("Log d'exécution disponible ici : %s", LOG_FILE)


if __name__ == "__main__":
    main()