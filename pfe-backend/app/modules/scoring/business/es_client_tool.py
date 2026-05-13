# Backward-compatibility shim.
# The canonical implementation lives in app.modules.elasticsearch.tools.client_tool.
from app.modules.elasticsearch.tools.client_tool import ESClientTool

__all__ = ["ESClientTool"]
