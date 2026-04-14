from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import requests


# =========================
# Configuration
# =========================
ES_HOST = "http://localhost:9200"

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
LOG_DIR = BASE_DIR / "logs"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = LOG_DIR / f"load_reference_to_es_{TIMESTAMP}.log"

HEADERS = {"Content-Type": "application/json"}

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
# Helpers
# =========================
def load_json(filename: str) -> List[Dict[str, Any]]:
    path = OUTPUT_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"Le fichier {filename} doit contenir une liste JSON.")

    logger.info("Fichier chargé : %s (%s éléments)", path, len(data))
    return data


def es_put_document(index: str, doc_id: str, document: Dict[str, Any]) -> None:
    url = f"{ES_HOST}/{index}/_doc/{doc_id}"
    response = requests.put(url, headers=HEADERS, json=document, timeout=60)
    response.raise_for_status()


def es_delete_index_if_exists(index: str) -> None:
    url = f"{ES_HOST}/{index}"
    response = requests.delete(url, headers=HEADERS, timeout=60)
    if response.status_code in (200, 404):
        logger.info("Index supprimé ou absent : %s", index)
        return
    response.raise_for_status()


def es_create_index(index: str, mapping: Dict[str, Any]) -> None:
    url = f"{ES_HOST}/{index}"
    response = requests.put(url, headers=HEADERS, json=mapping, timeout=60)
    response.raise_for_status()
    logger.info("Index créé : %s", index)


def es_count(index: str) -> int:
    url = f"{ES_HOST}/{index}/_count"
    response = requests.get(url, headers=HEADERS, timeout=60)
    response.raise_for_status()
    return response.json().get("count", 0)


# =========================
# Mappings
# =========================
PRODUCT_MAPPING = {
    "mappings": {
        "properties": {
            "id": {"type": "keyword"},
            "name": {"type": "text"}
        }
    }
}

CRITERIA_MAPPING = {
    "mappings": {
        "properties": {
            "id": {"type": "keyword"},
            "label": {"type": "text"},
            "expected_output": {"type": "text"},
            "product_id": {"type": "keyword"},
            "can_pass": {"type": "boolean"},
            "redirection_id": {"type": "keyword"},
            "order": {"type": "integer"},
            "created_at": {"type": "date"},
            "deleted_at": {"type": "date"},
            "unit": {"type": "keyword"}
        }
    }
}

CHOICE_MAPPING = {
    "mappings": {
        "properties": {
            "id": {"type": "keyword"},
            "criteria_id": {"type": "keyword"},
            "condition": {
                "properties": {
                    "arg": {"type": "keyword"},
                    "body": {"type": "text"}
                }
            },
            "score": {"type": "integer"},
            "is_blocking": {"type": "boolean"},
            "redirection_id": {"type": "keyword"},
            "created_at": {"type": "date"},
            "deleted_at": {"type": "date"}
        }
    }
}

PRODUCT_TARGET_MAPPING = {
    "mappings": {
        "properties": {
            "id": {"type": "keyword"},
            "sf_campaign_id": {"type": "keyword"},
            "product_id": {"type": "keyword"}
        }
    }
}


# =========================
# Préparation documents
# =========================
def prepare_product_docs(products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    docs = []
    for p in products:
        docs.append({
            "id": p["id"],
            "name": p["name"],
        })
    return docs


def prepare_criteria_docs(criteria: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    docs = []
    for c in criteria:
        docs.append({
            "id": c["id"],
            "label": c["label"],
            "expected_output": c.get("expected_output", ""),
            "product_id": c["product_id"],
            "can_pass": c["can_pass"],
            "redirection_id": c["redirection_id"],
            "order": c["order"],
            "created_at": c["created_at"],
            "deleted_at": c["deleted_at"],
            "unit": c["unit"],
        })
    return docs


def prepare_choice_docs(choices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    docs = []
    for ch in choices:
        docs.append({
            "id": ch["id"],
            "criteria_id": ch["criteria_id"],
            "condition": {
                "arg": (ch.get("condition") or {}).get("arg"),
                "body": (ch.get("condition") or {}).get("body"),
            },
            "score": ch["score"],
            "is_blocking": ch["is_blocking"],
            "redirection_id": ch["redirection_id"],
            "created_at": ch["created_at"],
            "deleted_at": ch["deleted_at"],
        })
    return docs


def prepare_product_target_docs(product_targets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    docs = []
    for pt in product_targets:
        docs.append({
            "id": pt["id"],
            "sf_campaign_id": pt["sf_campaign_id"],
            "product_id": pt["product_id"],
        })
    return docs


# =========================
# Chargement
# =========================
def recreate_target_indexes() -> None:
    logger.info("Recréation des index cibles...")

    es_delete_index_if_exists("product")
    es_delete_index_if_exists("criteria")
    es_delete_index_if_exists("choice")
    es_delete_index_if_exists("product_target")

    es_create_index("product", PRODUCT_MAPPING)
    es_create_index("criteria", CRITERIA_MAPPING)
    es_create_index("choice", CHOICE_MAPPING)
    es_create_index("product_target", PRODUCT_TARGET_MAPPING)


def load_index(index: str, docs: List[Dict[str, Any]]) -> None:
    logger.info("Chargement index %s : %s documents", index, len(docs))
    for doc in docs:
        es_put_document(index, doc["id"], doc)
    logger.info("Index %s chargé avec succès", index)


def main() -> None:
    logger.info("=== Début chargement référentiel vers Elasticsearch ===")

    products = load_json("products.json")
    criteria = load_json("criteria.json")
    choices = load_json("choice.json")
    product_targets = load_json("product_target.json")

    product_docs = prepare_product_docs(products)
    criteria_docs = prepare_criteria_docs(criteria)
    choice_docs = prepare_choice_docs(choices)
    product_target_docs = prepare_product_target_docs(product_targets)

    recreate_target_indexes()

    load_index("product", product_docs)
    load_index("criteria", criteria_docs)
    load_index("choice", choice_docs)
    load_index("product_target", product_target_docs)

    logger.info("Résumé final :")
    logger.info("product        = %s", es_count("product"))
    logger.info("criteria       = %s", es_count("criteria"))
    logger.info("choice         = %s", es_count("choice"))
    logger.info("product_target = %s", es_count("product_target"))

    logger.info("=== Fin chargement ===")
    logger.info("Log d'exécution : %s", LOG_FILE)


if __name__ == "__main__":
    main()