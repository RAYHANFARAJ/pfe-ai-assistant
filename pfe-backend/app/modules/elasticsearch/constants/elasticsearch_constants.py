"""Elasticsearch module constants — index names and route prefixes."""
from __future__ import annotations

from app.core.config import settings
from app.core.references import ElasticsearchRoutePrefix


class IndexNames:
    """Resolved Elasticsearch index names from application settings."""

    XTRA_CAMPAIGN: str = settings.index_xtra_campaign
    XTRA_QUESTION: str = settings.index_xtra_question
    XTRA_CHOICE:   str = settings.index_xtra_choice
    ACCOUNT:       str = settings.index_account


ACCOUNTS_SEARCH_PATH    = ElasticsearchRoutePrefix.ACCOUNTS + "/search"
ACCOUNTS_BUILD_PATH     = ElasticsearchRoutePrefix.ACCOUNTS + "/build-reference"
PRODUCTS_PATH           = ElasticsearchRoutePrefix.PRODUCTS
DEBUG_HEALTH_PATH       = ElasticsearchRoutePrefix.DEBUG + "/health"
DEBUG_CLIENT_PATH       = ElasticsearchRoutePrefix.DEBUG + "/client/{client_id}"
