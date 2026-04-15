from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List

import requests
from requests import Session
from requests.auth import HTTPBasicAuth
from requests.exceptions import RequestException

from app.core.config import settings


class AbstractElasticsearchService(ABC):
    def __init__(self) -> None:
        self.base_url = settings.es_host
        self.timeout = settings.request_timeout
        self.session: Session = requests.Session()
        self.session.auth = HTTPBasicAuth(
            settings.es_username,
            settings.es_password,
        )
        self.session.headers.update({"Content-Type": "application/json"})

    def search(self, index: str, query: Dict[str, Any], size: int) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/{index}/_search"
        payload = {"size": size, "query": query}

        try:
            response = self.session.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            return data.get("hits", {}).get("hits", [])
        except RequestException as exc:
            raise RuntimeError(f"Elasticsearch request failed for index '{index}'") from exc

    @abstractmethod
    def run(self) -> Any:
        pass
