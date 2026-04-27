# Backward-compatibility shim.
# The canonical implementation lives in app.modules.elasticsearch.services.account_service.
from app.modules.elasticsearch.services.account_service import AccountReferenceService

__all__ = ["AccountReferenceService"]
