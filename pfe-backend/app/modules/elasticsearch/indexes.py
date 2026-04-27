from __future__ import annotations

from app.core.config import settings


class ElasticsearchIndexes:
    """
    Central registry of Elasticsearch index names.
    Values are resolved from settings so they can be overridden per environment.
    """
    XTRA_CAMPAIGN: str = settings.index_xtra_campaign
    XTRA_QUESTION: str = settings.index_xtra_question
    XTRA_CHOICE:   str = settings.index_xtra_choice
    ACCOUNT:       str = settings.index_account
