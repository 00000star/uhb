"""Personality metrics — quantifiable behavioral traits of a model.

Measures operational characteristics:
- Question rate: how often the model asks clarifying questions
- Verbosity: tokens per substantive action
- Tool overuse: unnecessary tool calls
- Tool underuse: avoiding tools when appropriate
- Stability: score variance across repeated runs
- Confidence: does it express uncertainty appropriately?
- Initiative: does it verify assumptions or just proceed?
- Context degradation: score drop with conversation length
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PersonalityMetrics:
    """Quantified behavioral metrics for a model."""

    model_id: str

    # Core metrics (0.0–1.0, normalized)
    question_rate: float = 0.0         # % of interactions where model asks clarifying Q
    verbosity_ratio: float = 0.0       # tokens_output / tokens_input (normalized)
    tool_overuse_rate: float = 0.0     # unnecessary tool calls / total tool calls
    tool_underuse_rate: float = 0.0    # missed tool opportunities / total opportunities
    stability_score: float = 0.0       # 1.0 - coefficient_of_variation across runs
    confidence_calibration: float = 0.0 # how often expressed confidence matches accuracy
    initiative_score: float = 0.0      # verifies assumptions vs blindly proceeds
    context_degradation: float = 0.0   # score drop per 10k context tokens
    repair_attempt_rate: float = 0.0   # how often it tries to fix its own mistakes
    instruction_adherence: float = 0.0 # strictness of following instructions exactly

    # Raw measurements (for reference)
    avg_tokens_per_response: int = 0
    avg_tool_calls_per_task: float = 0.0
    avg_time_to_first_token_ms: float = 0.0
    runs_analyzed: int = 0

    def to_dict(self) -> dict:
        """Export as dictionary for JSON serialization."""
        return {
            "model_id": self.model_id,
            "traits": {
                "question_rate": self.question_rate,
                "verbosity_ratio": self.verbosity_ratio,
                "tool_overuse_rate": self.tool_overuse_rate,
                "tool_underuse_rate": self.tool_underuse_rate,
                "stability_score": self.stability_score,
                "confidence_calibration": self.confidence_calibration,
                "initiative_score": self.initiative_score,
                "context_degradation": self.context_degradation,
                "repair_attempt_rate": self.repair_attempt_rate,
                "instruction_adherence": self.instruction_adherence,
            },
            "raw": {
                "avg_tokens_per_response": self.avg_tokens_per_response,
                "avg_tool_calls_per_task": self.avg_tool_calls_per_task,
                "avg_time_to_first_token_ms": self.avg_time_to_first_token_ms,
                "runs_analyzed": self.runs_analyzed,
            },
        }

    def summary(self) -> str:
        """Human-readable summary of personality traits."""
        lines = [f"Personality Profile: {self.model_id}", "=" * 50]
        traits = self.to_dict()["traits"]
        for name, value in traits.items():
            bar = "█" * int(value * 20)
            lines.append(f"  {name:<28} {value:.2f} {bar}")
        return "\n".join(lines)
