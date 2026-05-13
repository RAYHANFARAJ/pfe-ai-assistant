# Backward-compatibility shim.
# The canonical implementation lives in app.modules.elasticsearch.tools.reference_tool.
from app.modules.elasticsearch.tools.reference_tool import ESReferenceTool

__all__ = ["ESReferenceTool"]
