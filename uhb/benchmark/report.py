"""Capability profile report generator — produces JSON and visualizable output."""

import json
from datetime import datetime, timezone
from typing import Optional

from .tasks.base import TaskResult
from .scorer import score_to_dimensions, overall_score, compute_speed_score


def generate_profile(model_key: str, results: list[TaskResult],
                     harness_id: str = "default",
                     environment: str = "terminal",
                     cost_summary: Optional[dict] = None) -> dict:
    """Generate a full capability profile from benchmark results.

    Args:
        model_key: Model identifier (e.g., "anthropic/claude-sonnet-4-6").
        results: List of task results.
        harness_id: Identifier for the harness used.
        environment: Environment the benchmark ran in.
        cost_summary: Optional cost breakdown.

    Returns:
        Capability profile as a dictionary ready for JSON export.
    """
    aggregated = score_to_dimensions(results)

    # Extract latency for speed score
    latencies = [
        r.details.get("latency_ms", 0)
        for r in results
        if "latency_ms" in r.details
    ]
    if latencies:
        aggregated["speed"]["score"] = round(compute_speed_score(latencies), 4)

    profile = {
        "model_id": model_key,
        "harness": harness_id,
        "environment": environment,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "overall_score": overall_score(aggregated),
        "dimensions": {
            dim: aggregated[dim]["score"]
            for dim in sorted(aggregated.keys())
        },
        "dimension_details": aggregated,
        "task_count": len(results),
        "tasks_passed": sum(1 for r in results if r.passed),
        "total_latency_ms": round(sum(latencies), 1),
        "cost": cost_summary or {},
        "per_task": [
            {
                "task_id": r.task_id,
                "task_name": r.task_name,
                "dimension": r.dimension,
                "score": r.score,
                "passed": r.passed,
                "latency_ms": r.details.get("latency_ms", 0),
                "error": r.error,
            }
            for r in results
        ],
    }

    return profile


def save_profile(profile: dict, path: str) -> None:
    """Save a capability profile to a JSON file."""
    from pathlib import Path
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(profile, indent=2))


def load_profile(path: str) -> dict:
    """Load a capability profile from a JSON file."""
    return json.loads(__import__('pathlib').Path(path).read_text())


def compare_profiles(profiles: list[dict]) -> dict:
    """Generate a comparison of multiple capability profiles.

    Args:
        profiles: List of profile dicts (from generate_profile).

    Returns:
        Comparison dict with side-by-side dimension scores.
    """
    dimensions = set()
    for p in profiles:
        dimensions.update(p["dimensions"].keys())
    dimensions = sorted(dimensions)

    models = [p["model_id"] for p in profiles]

    comparison = {
        "models": models,
        "dimensions": {},
        "overall": {p["model_id"]: p.get("overall_score", 0) for p in profiles},
    }

    for dim in dimensions:
        comparison["dimensions"][dim] = {}
        for p in profiles:
            comparison["dimensions"][dim][p["model_id"]] = p["dimensions"].get(dim)

    # Find winner per dimension
    comparison["winners"] = {}
    for dim in dimensions:
        best_model = None
        best_score = -1
        for p in profiles:
            score = p["dimensions"].get(dim)
            if score is not None and score > best_score:
                best_score = score
                best_model = p["model_id"]
        comparison["winners"][dim] = best_model

    return comparison
