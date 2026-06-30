"""Normalized scoring across capability dimensions.

Maps raw task scores to the 10 capability dimensions and produces
a unified 0.0–1.0 score per dimension.
"""

from collections import defaultdict
from typing import Optional

from .tasks.base import TaskResult


# Mapping from task_id to primary capability dimension
DIMENSION_MAP = {
    "code_from_spec": "coding",
    "debug_broken": "self_repair",
    "refactor": "reasoning",
    "tool_use": "tool_usage",
    "search_docs": "exploration",
    "plan_feature": "planning",
    "review_pr": "reasoning",
    "long_context": "long_context",
    "self_repair": "self_repair",
}

# All dimensions the benchmark measures
ALL_DIMENSIONS = [
    "reasoning",
    "coding",
    "planning",
    "tool_usage",
    "long_context",
    "self_repair",
    "instruction_following",
    "exploration",
    "creativity",
    "speed",
]


def score_to_dimensions(results: list[TaskResult]) -> dict[str, dict]:
    """Aggregate task results into dimension scores.

    Args:
        results: List of task results from a benchmark run.

    Returns:
        Dict mapping dimension → {score, tasks, passes, fails}.
    """
    dim_scores = defaultdict(lambda: {"scores": [], "tasks": [], "passes": 0, "fails": 0})

    for r in results:
        dim = r.dimension
        dim_scores[dim]["scores"].append(r.score)
        dim_scores[dim]["tasks"].append(r.task_id)
        if r.passed:
            dim_scores[dim]["passes"] += 1
        else:
            dim_scores[dim]["fails"] += 1

    aggregated = {}
    for dim, data in dim_scores.items():
        scores = data["scores"]
        aggregated[dim] = {
            "score": round(sum(scores) / len(scores), 4) if scores else 0.0,
            "task_count": len(scores),
            "tasks_passed": data["passes"],
            "tasks_failed": data["fails"],
            "task_ids": data["tasks"],
        }

    # Fill in missing dimensions with null
    for dim in ALL_DIMENSIONS:
        if dim not in aggregated:
            aggregated[dim] = {
                "score": None,
                "task_count": 0,
                "task_ids": [],
            }

    return aggregated


def overall_score(aggregated: dict[str, dict]) -> float:
    """Compute a weighted overall score across all dimensions.

    Dimensions that weren't measured are excluded from the average.
    """
    measured = {d: v for d, v in aggregated.items() if v["score"] is not None}
    if not measured:
        return 0.0
    return round(sum(v["score"] for v in measured.values()) / len(measured), 4)


def compute_speed_score(latency_ms_values: list[float]) -> float:
    """Compute a speed score from latency data.

    Args:
        latency_ms_values: List of per-task latencies in milliseconds.

    Returns:
        Normalized speed score: 1.0 for <5s avg, scaling down to 0 at 60s+.
    """
    if not latency_ms_values:
        return 1.0  # no data, assume fast
    avg_ms = sum(latency_ms_values) / len(latency_ms_values)
    # Linear scale: 5000ms → 1.0, 60000ms → 0.0
    return max(0.0, min(1.0, 1.0 - (avg_ms - 5000) / 55000))
