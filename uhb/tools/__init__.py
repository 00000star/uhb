"""Tool ecology benchmark — measure how model + tool combinations perform.

Key insight: sometimes a modest model with excellent tooling outperforms
a stronger model with weak tooling.
"""

from .suite import ToolEcologySuite, ToolResult, ToolCombo
from .tools_list import KNOWN_TOOLS, TOOL_CATEGORIES

__version__ = "0.1.0"
__all__ = [
    "ToolEcologySuite", "ToolResult", "ToolCombo",
    "KNOWN_TOOLS", "TOOL_CATEGORIES",
]
