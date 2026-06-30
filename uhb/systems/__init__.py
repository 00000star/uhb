"""System-level benchmarking — evaluate entire AI coding systems as black boxes.

Compare Claude Code, Codex CLI, Aider, OpenHands, Cursor Agent, and your own agents
across 10 dimensions.
"""

from .base import AICodingSystem, SystemOutput, SystemState
from .metrics import SystemMetric, SystemProfile, SYSTEM_DIMENSIONS
from .compare import SystemComparator
from .runner import SystemBenchmarkRunner

__version__ = "0.1.0"
__all__ = [
    "AICodingSystem", "SystemOutput", "SystemState",
    "SystemMetric", "SystemProfile", "SYSTEM_DIMENSIONS",
    "SystemComparator", "SystemBenchmarkRunner",
]
