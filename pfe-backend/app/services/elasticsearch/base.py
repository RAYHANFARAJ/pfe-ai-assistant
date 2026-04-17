from __future__ import annotations

import requests
from requests.auth import HTTPBasicAuth
from typing import Any, Dict, List

from app.core.config import settings


class AbstractElasticsearchService:
    def __init__(self) -> None:
        self.base_url = settings.es_host
        self.auth = HTTPBasicAuth(settings.es_username, settings.es_password)
        self.timeout = settings.request_timeout

        self.session = requests.Session()
        self.session.auth = self.auth
        self.session.headers.update({"Content-Type": "application/json"})

    def search(self, index: str, query: Dict[str, Any], size: int = 1000) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/{index}/_search"

        payload = {
            "size": size,
            "query": query,
        }

        try:
            response = self.session.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            return data.get("hits", {}).get("hits", [])
        except Exception:
            # IMPORTANT: fallback pour éviter crash si ES down
            return []
    def index_document(
        self,
        index: str,
        document: Dict[str, Any],
        document_id: str | None = None,
    ) -> Dict[str, Any]:
        if document_id:
            url = f"{self.base_url}/{index}/_doc/{document_id}"
            response = self.session.put(url, json=document, timeout=self.timeout)
        else:
            url = f"{self.base_url}/{index}/_doc"
            response = self.session.post(url, json=document, timeout=self.timeout)

        response.raise_for_status()
        return response.json()

    def bulk_index(
        self,
        index: str,
        documents: List[Dict[str, Any]],
        id_field: str | None = None,
    ) -> Dict[str, Any]:
        success = 0
        errors: List[Dict[str, Any]] = []

        for document in documents:
            try:
                document_id = document.get(id_field) if id_field else None
                self.index_document(
                    index=index,
                    document=document,
                    document_id=document_id,
                )
                success += 1
            except Exception as exc:
                errors.append({
                    "document_id": document.get(id_field) if id_field else None,
                    "error": str(exc),
                })

        return {
            "success": success,
            "errors_count": len(errors),
            "errors": errors[:20],
        }
