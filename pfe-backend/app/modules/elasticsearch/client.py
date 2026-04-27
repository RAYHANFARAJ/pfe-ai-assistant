from __future__ import annotations

import logging
from typing import Any, Dict, Generic, List, Optional, TypeVar

from elasticsearch import Elasticsearch
from elastic_transport import ConnectionError as ESConnectionError

from app.core.config import settings

logger = logging.getLogger(__name__)

# Generic type for the normalised document returned by a concrete subclass.
TDocument = TypeVar("TDocument")


class AbstractElasticsearchClient(Generic[TDocument]):
    """
    Reusable, typed Elasticsearch client built on the official SDK.

    Responsibilities
    ────────────────
    • Owns the single Elasticsearch connection (SDK-based, not raw HTTP).
    • Exposes low-level primitives: search, get_by_id, index_document,
      bulk_index, health.
    • Never contains business logic — that belongs in subclasses.

    How to extend
    ─────────────
    class AccountClient(AbstractElasticsearchClient[AccountDocument]):
        INDEX = ElasticsearchIndexes.ACCOUNT

        def find_by_id(self, account_id: str) -> Optional[AccountDocument]:
            hits = self._search(self.INDEX, {"ids": {"values": [account_id]}}, size=1)
            return self._map(hits[0]["_source"]) if hits else None

        def _map(self, source: Dict[str, Any]) -> AccountDocument:
            ...
    """

    def __init__(self) -> None:
        kwargs: Dict[str, Any] = {
            "request_timeout": settings.request_timeout,
            "retry_on_timeout": False,
            "max_retries": 0,
        }
        if settings.es_username and settings.es_password:
            kwargs["basic_auth"] = (settings.es_username, settings.es_password)

        self._es = Elasticsearch(settings.es_host, **kwargs)

    # ------------------------------------------------------------------
    # Low-level primitives — for use by subclasses only
    # ------------------------------------------------------------------

    def search(
        self,
        index: str,
        query: Dict[str, Any],
        size: int = 10,
        source_fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Public alias for _search — preserves backward compatibility with subclasses that call self.search()."""
        return self._search(index, query, size, source_fields)

    def _search(
        self,
        index: str,
        query: Dict[str, Any],
        size: int = 10,
        source_fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Execute a search query. Returns raw ES hits. Never raises."""
        kwargs: Dict[str, Any] = {"index": index, "query": query, "size": size}
        if source_fields:
            kwargs["source"] = source_fields
        try:
            res = self._es.search(**kwargs)
            return res.get("hits", {}).get("hits", [])
        except ESConnectionError:
            logger.warning("Elasticsearch unreachable at %s", settings.es_host)
            return []
        except Exception as exc:
            logger.error("ES search error on index '%s': %s", index, exc)
            return []

    def _get_by_id(
        self, index: str, doc_id: str
    ) -> Optional[Dict[str, Any]]:
        """Fetch a single document by its ES _id. Returns _source or None."""
        hits = self._search(index, {"ids": {"values": [doc_id]}}, size=1)
        return hits[0].get("_source") if hits else None

    def _index_document(
        self,
        index: str,
        document: Dict[str, Any],
        doc_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        if doc_id:
            return self._es.index(index=index, id=doc_id, document=document).body
        return self._es.index(index=index, document=document).body

    def _bulk_index(
        self,
        index: str,
        documents: List[Dict[str, Any]],
        id_field: Optional[str] = None,
    ) -> Dict[str, Any]:
        success, errors = 0, []
        for doc in documents:
            try:
                self._index_document(index, doc, doc.get(id_field) if id_field else None)
                success += 1
            except Exception as exc:
                errors.append({"id": doc.get(id_field), "error": str(exc)})
        return {"success": success, "errors_count": len(errors), "errors": errors[:20]}

    # ------------------------------------------------------------------
    # Health check — usable directly, no subclassing needed
    # ------------------------------------------------------------------

    def health(self) -> Dict[str, Any]:
        try:
            info = self._es.info()
            return {
                "status":  "connected",
                "host":    settings.es_host,
                "cluster": info.get("cluster_name"),
                "version": info.get("version", {}).get("number"),
            }
        except ESConnectionError:
            return {"status": "unreachable", "host": settings.es_host}
        except Exception as exc:
            return {"status": "error", "detail": str(exc)}
