from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from app.modules.elasticsearch.client import AbstractElasticsearchClient
from app.modules.elasticsearch.indexes import ElasticsearchIndexes

logger = logging.getLogger(__name__)


class AccountReferenceService(AbstractElasticsearchClient):
    """
    Reads accounts from the raw Salesforce pipeline index and normalises them.
    Used by the build-reference pipeline to populate the local account index.
    """

    SOURCE_INDEX = ElasticsearchIndexes.ACCOUNT

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_account_by_id(self, account_id: str) -> Optional[Dict[str, Any]]:
        hits = self._search(
            self.SOURCE_INDEX,
            {"term": {"_id": account_id}},
            size=1,
        )
        if not hits:
            logger.warning("No account found for id=%s", account_id)
            return None

        source = hits[0].get("_source", {})
        return self._normalise(source)

    def run(self) -> Dict[str, Any]:
        """Entry point called by the build-reference route."""
        return {"status": "not_implemented", "detail": "AccountReferenceService.run() not yet implemented."}

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _normalise(self, source: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "client_id":   source.get("Id"),
            "client_name": source.get("Name"),
            "sector":      source.get("Industry") or source.get("sect__c") or "Unknown",
            "website":     self._clean_url(
                               source.get("Website") or source.get("SalesLoft_Domain__c")
                           ),
            "linkedin":    source.get("LinkedIn_URL__c"),
            "employees":   source.get("NumberOfEmployees"),
        }

    @staticmethod
    def _clean_url(url: Optional[str]) -> Optional[str]:
        if not url:
            return None
        return url.split("?")[0]
