from app.core.config import settings


class ElasticsearchIndexes:
    XTRA_CAMPAIGN = settings.index_xtra_campaign
    XTRA_QUESTION = settings.index_xtra_question
    XTRA_CHOICE = settings.index_xtra_choice
    ACCOUNT = "account"
