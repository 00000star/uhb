"""Personality fingerprint — exportable behavioral profile generated from runs."""

import hashlib
from datetime import datetime, timezone
from typing import Optional, Any
from dataclasses import dataclass, field

from .metrics import PersonalityMetrics


@dataclass
class PersonalityFingerprint:
    """Complete personality fingerprint for a model."""

    model_id: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metrics: PersonalityMetrics = field(default_factory=lambda: PersonalityMetrics(model_id="unknown"))

    # Categorical descriptors
    behavioral_class: str = "unknown"  # "planner", "executor", "explorer", "hesitant", "reckless"
    recommended_interaction: str = ""  # e.g., "Give explicit instructions, request plans first"
    weaknesses: list[str] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "model_id": self.model_id,
            "timestamp": self.timestamp,
            "metrics": self.metrics.to_dict(),
            "behavioral_class": self.behavioral_class,
            "recommended_interaction": self.recommended_interaction,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
        }

    def classify(self) -> str:
        """Classify the model's behavioral type based on metrics."""
        m = self.metrics

        if m.planning_orientation > 0.7 and m.question_rate > 0.3:
            self.behavioral_class = "planner"
            self.recommended_interaction = "Let it plan first. Provide high-level goals, let it decompose."
        elif m.initiative_score > 0.7 and m.instruction_adherence > 0.8:
            self.behavioral_class = "executor"
            self.recommended_interaction = "Give clear step-by-step instructions. It executes well."
        elif m.question_rate > 0.5 and m.exploration_preference > 0.6:
            self.behavioral_class = "explorer"
            self.recommended_interaction = "Give open-ended problems. It finds novel solutions."
        elif m.question_rate < 0.1 and m.tool_overuse_rate > 0.4:
            self.behavioral_class = "reckless"
            self.recommended_interaction = "Add guardrails. Request plans before coding. Verify outputs."
        elif m.confidence_calibration < 0.3:
            self.behavioral_class = "hesitant"
            self.recommended_interaction = "Provide more context. Be explicit about constraints."
        else:
            self.behavioral_class = "versatile"
            self.recommended_interaction = "Standard interaction works well. Adapt to task complexity."

        return self.behavioral_class

    def hash(self) -> str:
        """Stable hash of the fingerprint for comparison."""
        raw = f"{self.model_id}|{self.behavioral_class}|{sorted(self.strengths)}|{sorted(self.weaknesses)}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]


def generate_fingerprint(model_id: str,
                         benchmark_results: list[Any] = None,
                         conversation_logs: list[Any] = None,
                         repeated_scores: list[float] = None) -> PersonalityFingerprint:
    """Generate a personality fingerprint from observed behavior.

    This is a heuristic generator. In production, these metrics would come
    from dedicated interaction experiments and analysis of benchmark conversation logs.

    Args:
        model_id: The model identifier.
        benchmark_results: Raw task results from a benchmark run.
        conversation_logs: Full conversation histories.
        repeated_scores: Scores from repeated runs of the same task.

    Returns:
        A PersonalityFingerprint with estimated metrics.
    """
    metrics = PersonalityMetrics(model_id=model_id)

    if benchmark_results:
        # Estimate from benchmark results
        metrics.runs_analyzed = len(benchmark_results)

        # Stability: inverse of score variance
        if repeated_scores and len(repeated_scores) > 1:
            mean = sum(repeated_scores) / len(repeated_scores)
            variance = sum((s - mean) ** 2 for s in repeated_scores) / len(repeated_scores)
            cv = (variance ** 0.5) / mean if mean > 0 else 1.0
            metrics.stability_score = max(0.0, 1.0 - cv)

        # Verbosity from result details
        total_tokens = sum(
            r.details.get("tokens_output", 0) + r.details.get("tokens_input", 0)
            for r in benchmark_results if hasattr(r, 'details')
        )
        if metrics.runs_analyzed > 0:
            metrics.avg_tokens_per_response = total_tokens // metrics.runs_analyzed

    # If no data, use defaults (metrics stay at 0.0)
    if metrics.runs_analyzed == 0:
        metrics.runs_analyzed = 0

    finger = PersonalityFingerprint(
        model_id=model_id,
        metrics=metrics,
    )
    finger.classify()

    return finger
