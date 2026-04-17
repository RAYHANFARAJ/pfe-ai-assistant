from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from elasticsearch import Elasticsearch
from app.core.config import settings

logger = logging.getLogger(__name__)


class AccountReferenceService:

    def __init__(self):
        # 🔥 connexion directe ES (évite ton AbstractElasticsearchService buggué)
        self.es = Elasticsearch(
            settings.es_host,
            basic_auth=(settings.es_username, settings.es_password)
        )

        self.source_index = "verse_sf_pipeline_account_raw_zone_v20251030"
        self.target_index = "account"

    # =========================
    # GET ACCOUNT BY ID (FIX FINAL)
    # =========================
    def get_account_by_id(self, account_id: str) -> Optional[Dict[str, Any]]:
        print("ACCOUNT RESULT:", source)  
        res = self.es.search(
            index=self.source_index,
            query={
                "term": {
                    "_id": account_id   # 🔥 CONFIRMÉ CHEZ TOI
                }
            },
            size=1
        )

        hits = res.get("hits", {}).get("hits", [])

        if not hits:
            logger.warning(f"No account found for id={account_id}")
            return None

        source = hits[0].get("_source", {})

        return {
            "client_id": source.get("Id"),
            "client_name": source.get("Name"),
            "sector": source.get("Industry") or source.get("sect__c") or "Unknown",
            "website": self.clean_url(
                source.get("Website") or source.get("SalesLoft_Domain__c")
            ),
            "linkedin": source.get("LinkedIn_URL__c"),
            "employees": source.get("NumberOfEmployees")
        }

    # =========================
    # CLEAN URL
    # =========================
    def clean_url(self, url: Optional[str]) -> Optional[str]:
        if not url:
            return None
        return url.split("?")[0]

    # =========================
    # OPTIONAL: DEBUG METHOD
    # =========================
    def debug_account(self, account_id: str):
        res = self.es.search(
            index=self.source_index,
            query={"match_all": {}},
            size=1
        )
        return res
