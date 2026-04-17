from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from elasticsearch import Elasticsearch
from elastic_transport import ConnectionError as ESConnectionError
from app.core.config import settings

logger = logging.getLogger(__name__)


class ESClientTool:
    """
    Retrieves a single client account from Elasticsearch.

    Because the ES document _id may differ from the Salesforce Id field value
    (depending on the ingestion pipeline), we try three strategies in order
    and return the first hit.
    """

    def __init__(self) -> None:
        kwargs: dict = {
            "request_timeout": settings.request_timeout,
            "retry_on_timeout": False,
            "max_retries": 0,
        }
        # Only send credentials when both are set — avoids rejection on no-auth ES
        if settings.es_username and settings.es_password:
            kwargs["basic_auth"] = (settings.es_username, settings.es_password)

        self.es = Elasticsearch(settings.es_host, **kwargs)
        self.index = settings.index_account

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Return normalised client data or None when unavailable."""
        for strategy_name, query in self._lookup_queries(client_id):
            source = self._execute(query, strategy_name, client_id)
            if source is None:
                # ES is completely unreachable — stop immediately
                return None
            if source:
                # Hit found
                logger.info("Client '%s' resolved via strategy '%s'", client_id, strategy_name)
                return self._format_client(source)
            # Empty dict → no hit → try next strategy

        logger.warning(
            "Client '%s' not found in index '%s' after all lookup strategies.",
            client_id,
            self.index,
        )
        return None

    def debug_lookup(self, client_id: str) -> Dict[str, Any]:
        """Return per-strategy hit counts/field lists for diagnostics."""
        results: Dict[str, Any] = {}
        for name, query in self._lookup_queries(client_id):
            try:
                res = self.es.search(index=self.index, query=query, size=1)
                hits = res.get("hits", {}).get("hits", [])
                results[name] = {
                    "hits": len(hits),
                    "doc_id": hits[0].get("_id") if hits else None,
                    "source_keys": list(hits[0].get("_source", {}).keys()) if hits else [],
                }
            except ESConnectionError as exc:
                results[name] = {"error": "ES_UNREACHABLE", "detail": str(exc)}
            except Exception as exc:
                results[name] = {"error": type(exc).__name__, "detail": str(exc)}
        return {"client_id": client_id, "index": self.index, "strategies": results}

    def es_health(self) -> Dict[str, Any]:
        """Return a simple connectivity check."""
        try:
            info = self.es.info()
            return {
                "status": "connected",
                "host": settings.es_host,
                "cluster": info.get("cluster_name"),
                "version": info.get("version", {}).get("number"),
            }
        except ESConnectionError:
            return {"status": "unreachable", "host": settings.es_host}
        except Exception as exc:
            return {"status": "error", "detail": str(exc)}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _lookup_queries(client_id: str) -> List[tuple]:
        """
        Return (name, query) pairs in priority order.
        ES _id lookup is fastest; Id.keyword and Id field queries are fallbacks
        for pipelines that use a generated document ID instead of the SF Id.
        """
        return [
            ("by_doc_id",    {"ids": {"values": [client_id]}}),
            ("by_Id_keyword", {"term": {"Id.keyword": client_id}}),
            ("by_Id_field",  {"term": {"Id": client_id}}),
        ]

    def _execute(
        self, query: Dict[str, Any], strategy: str, client_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Execute one search query.
        Returns:
          None  → ES unreachable (caller must stop)
          {}    → query succeeded but no document found
          {...} → document source
        """
        try:
            res = self.es.search(index=self.index, query=query, size=1)
            hits = res.get("hits", {}).get("hits", [])
            if hits:
                return hits[0].get("_source", {})
            logger.debug("Strategy '%s': no hit for client '%s'", strategy, client_id)
            return {}
        except ESConnectionError:
            logger.warning(
                "Elasticsearch unreachable at %s (strategy '%s').", settings.es_host, strategy
            )
            return None
        except Exception as exc:
            logger.error("Strategy '%s' raised %s: %s", strategy, type(exc).__name__, exc)
            return {}

    # ------------------------------------------------------------------
    # Normalised output schema  — single definition, no duplicate keys
    # ------------------------------------------------------------------

    def _format_client(self, source: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "client_id":   source.get("Id"),
            "client_name": source.get("Name"),
            "sector":      source.get("Industry") or source.get("sect__c") or "Unknown",
            "website":     self._clean_url(
                               source.get("Website") or source.get("SalesLoft_Domain__c")
                           ),
            # Resolve linkedin from any CRM field variant — first non-null wins
            "linkedin": (
                source.get("LinkedIn_URL__c")
                or source.get("linkedin_url")
                or source.get("linkedin")
            ),
            "description": source.get("Description"),
            # --- CRM structured numeric fields (used directly in criteria evaluation) ---
            # These are the ground truth — always preferred over web-extracted estimates
            "crm_employee_count": self._to_int(source.get("NumberOfEmployees")),
            "crm_siren":          source.get("SIREN__c"),
            "crm_country":        (source.get("BillingAddress") or {}).get("country"),
        }

    @staticmethod
    def _to_int(value: Any) -> Optional[int]:
        """Safely cast a CRM numeric field to int."""
        try:
            return int(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _clean_url(url: Optional[str]) -> Optional[str]:
        """Normalise a URL or bare domain into a crawlable https:// URL."""
        if not url:
            return None
        url = url.strip().split("?")[0].rstrip("/")
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        return url
