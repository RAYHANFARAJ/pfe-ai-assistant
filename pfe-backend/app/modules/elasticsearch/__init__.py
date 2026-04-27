"""
Elasticsearch module — owns every piece of ES interaction.

Public surface:
    AbstractElasticsearchClient  — reusable generic base class
    ElasticsearchIndexes         — index name constants
    router                       — FastAPI router (registered by modules/__init__.py)
"""
from app.modules.elasticsearch.client  import AbstractElasticsearchClient
from app.modules.elasticsearch.indexes import ElasticsearchIndexes

__all__ = ["AbstractElasticsearchClient", "ElasticsearchIndexes"]
