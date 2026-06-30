"""UHB Benchmark — the universal benchmark suite for AI coding models."""

from .tasks.base import TaskBase, TaskSpec, TaskContext, TaskResult
from .tasks.registry import TaskRegistry, get_registry, discover_tasks
from .runner import BenchmarkRunner
from .scorer import score_to_dimensions, overall_score, ALL_DIMENSIONS
from .report import generate_profile, save_profile, load_profile, compare_profiles

__version__ = "0.1.0"
__all__ = [
    "TaskBase", "TaskSpec", "TaskContext", "TaskResult",
    "TaskRegistry", "get_registry", "discover_tasks",
    "BenchmarkRunner",
    "score_to_dimensions", "overall_score", "ALL_DIMENSIONS",
    "generate_profile", "save_profile", "load_profile", "compare_profiles",
]
