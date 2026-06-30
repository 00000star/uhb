"""System benchmarking metrics — 10 dimensions for evaluating AI coding systems."""

from dataclasses import dataclass, field
from enum import Enum


class SystemMetric(Enum):
    """The 10 dimensions for system-level benchmarking."""
    REPO_UNDERSTANDING = "repo_understanding"    # Can it navigate and explain the codebase?
    ARCHITECTURE = "architecture"                # Can it reason about system design?
    REFACTORING = "refactoring"                  # Can it improve code without breaking?
    DEBUGGING = "debugging"                      # Can it find and fix bugs?
    TESTING = "testing"                          # Can it write good tests?
    PLANNING = "planning"                        # Can it decompose complex tasks?
    DOCUMENTATION = "documentation"              # Can it generate useful docs?
    AUTONOMY = "autonomy"                        # How much can it do without human input?
    RECOVERY = "recovery"                        # Can it fix its own mistakes?
    COST_EFFICIENCY = "cost"                     # Total $ to complete tasks vs quality


SYSTEM_DIMENSIONS = [m.value for m in SystemMetric]


@dataclass
class SystemProfile:
    """A complete profile for an AI coding system."""
    system_name: str
    system_version: str
    dimensions: dict[str, float] = field(default_factory=dict)  # dimension → score
    task_results: list[dict] = field(default_factory=list)
    total_cost_usd: float = 0.0
    total_time_seconds: float = 0.0
    total_human_interventions: int = 0
    repo_used: str = ""

    def overall_score(self) -> float:
        scores = [v for v in self.dimensions.values() if v is not None]
        return sum(scores) / len(scores) if scores else 0.0

    def to_dict(self) -> dict:
        return {
            "system": f"{self.system_name} v{self.system_version}",
            "overall": round(self.overall_score(), 4),
            "dimensions": self.dimensions,
            "total_cost_usd": round(self.total_cost_usd, 4),
            "total_time_seconds": round(self.total_time_seconds, 1),
            "total_human_interventions": self.total_human_interventions,
            "repo": self.repo_used,
        }

    def summary(self) -> str:
        lines = [f"System Profile: {self.system_name} v{self.system_version}",
                 "=" * 60,
                 f"Overall: {self.overall_score():.3f}",
                 f"Cost: ${self.total_cost_usd:.2f}",
                 f"Time: {self.total_time_seconds:.0f}s",
                 f"Human Interventions: {self.total_human_interventions}",
                 ""]
        for dim in SystemMetric:
            score = self.dimensions.get(dim.value)
            bar = "█" * int((score or 0) * 20) if score is not None else "N/A"
            lines.append(f"  {dim.value:<26} {score or 'N/A'} {bar}")
        return "\n".join(lines)
