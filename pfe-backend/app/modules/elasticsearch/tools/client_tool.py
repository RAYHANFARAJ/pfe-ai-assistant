from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from elastic_transport import ConnectionError as ESConnectionError

from app.core.config import settings
from app.modules.elasticsearch.client import AbstractElasticsearchClient
from app.modules.elasticsearch.indexes import ElasticsearchIndexes

logger = logging.getLogger(__name__)


class ESClientTool(AbstractElasticsearchClient):
    """
    Account lookup and search tool.
    Concrete subclass of AbstractElasticsearchClient bound to the ACCOUNT index.
    """

    INDEX = ElasticsearchIndexes.ACCOUNT

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Return normalised client data or None when unavailable."""
        for strategy_name, query in self._lookup_queries(client_id):
            try:
                hits = self._search(self.INDEX, query, size=1)
            except ESConnectionError:
                logger.warning("ES unreachable during strategy '%s'", strategy_name)
                return None

            if hits:
                logger.info("Client '%s' resolved via strategy '%s'", client_id, strategy_name)
                return self._format_client(hits[0].get("_source", {}))

        logger.warning("Client '%s' not found in index '%s'.", client_id, self.INDEX)
        return None

    def search(self, query: str, size: int = 10) -> List[Dict[str, Any]]:
        """Search clients by name or Salesforce ID."""
        q = query.strip()
        es_query: Dict[str, Any] = (
            {"match_all": {}}
            if not q
            else {
                "bool": {
                    "should": [
                        {"ids":     {"values": [q]}},
                        {"term":    {"Id": q}},
                        {"match":   {"Name": {"query": q, "fuzziness": "AUTO"}}},
                        {"wildcard": {"Name.keyword": {"value": f"*{q}*", "case_insensitive": True}}},
                    ],
                    "minimum_should_match": 1,
                }
            }
        )
        hits = self._search(
            self.INDEX,
            es_query,
            size=size,
            source_fields=["Id", "Name", "Industry", "Website", "NumberOfEmployees"],
        )
        return [
            {
                "client_id":   h["_source"].get("Id"),
                "client_name": h["_source"].get("Name"),
                "sector":      h["_source"].get("Industry") or "Unknown",
                "website":     h["_source"].get("Website"),
                "employees":   h["_source"].get("NumberOfEmployees"),
            }
            for h in hits
        ]

    def debug_lookup(self, client_id: str) -> Dict[str, Any]:
        """Return per-strategy diagnostics for a given client ID."""
        results: Dict[str, Any] = {}
        for name, query in self._lookup_queries(client_id):
            try:
                hits = self._search(self.INDEX, query, size=1)
                results[name] = {
                    "hits":        len(hits),
                    "doc_id":      hits[0].get("_id") if hits else None,
                    "source_keys": list(hits[0].get("_source", {}).keys()) if hits else [],
                }
            except ESConnectionError as exc:
                results[name] = {"error": "ES_UNREACHABLE", "detail": str(exc)}
            except Exception as exc:
                results[name] = {"error": type(exc).__name__, "detail": str(exc)}
        return {"client_id": client_id, "index": self.INDEX, "strategies": results}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _lookup_queries(client_id: str) -> List[tuple]:
        return [
            ("by_doc_id",     {"ids":  {"values": [client_id]}}),
            ("by_Id_keyword", {"term": {"Id.keyword": client_id}}),
            ("by_Id_field",   {"term": {"Id": client_id}}),
        ]

    def _format_client(self, source: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "client_id":         source.get("Id"),
            "client_name":       source.get("Name"),
            "sector":            source.get("Industry") or source.get("sect__c") or "Unknown",
            "website":           _clean_url(
                                     source.get("Website") or source.get("SalesLoft_Domain__c")
                                 ),
            "linkedin": (
                source.get("LinkedIn_URL__c")
                or source.get("linkedin_url")
                or source.get("linkedin")
            ),
            "description":       source.get("Description"),
            "crm_employee_count": _to_int(source.get("NumberOfEmployees")),
            "crm_siren":          source.get("SIREN__c"),
            "crm_country":       (source.get("BillingAddress") or {}).get("country"),
        }


# ------------------------------------------------------------------
# Module-level helpers (pure functions, no state)
# ------------------------------------------------------------------

def _to_int(value: Any) -> Optional[int]:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _clean_url(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    url = url.strip().split("?")[0].rstrip("/")
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url
