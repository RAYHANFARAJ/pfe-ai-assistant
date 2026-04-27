# Backward-compatibility shim.
# The canonical definition lives in app.modules.elasticsearch.indexes.
from app.modules.elasticsearch.indexes import ElasticsearchIndexes

__all__ = ["ElasticsearchIndexes"]
