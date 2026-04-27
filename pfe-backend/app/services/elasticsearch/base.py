# Backward-compatibility shim.
# The canonical implementation lives in app.modules.elasticsearch.client.
# Remove this file once all direct imports have been updated.
from app.modules.elasticsearch.client import AbstractElasticsearchClient as AbstractElasticsearchService

__all__ = ["AbstractElasticsearchService"]
