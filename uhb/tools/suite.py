"""Tool ecology benchmark suite — test model × tool combinations."""

import itertools
from dataclasses import dataclass, field
from typing import Optional, Callable

from .tools_list import KNOWN_TOOLS, BASELINE_TOOLS, MINIMAL_TOOLS, STANDARD_TOOLS


@dataclass
class ToolResult:
    """Result for a single tool combination test."""
    model_id: str
    tool_names: list[str]
    task_id: str
    score: float = 0.0
    tokens_used: int = 0
    tool_calls_made: int = 0
    time_seconds: float = 0.0
    error: Optional[str] = None


@dataclass
class ToolCombo:
    """A combination of tools to test."""
    name: str
    tools: list[str]
    description: str


# Predefined tool combinations to test
PRESET_COMBOS = [
    ToolCombo("baseline", BASELINE_TOOLS, "No tools — model alone"),
    ToolCombo("minimal", MINIMAL_TOOLS, "Ripgrep + Git only"),
    ToolCombo("standard", STANDARD_TOOLS, "ripgrep, git, pytest, ruff, gh"),
    ToolCombo("search_focused", ["ripgrep", "ast-grep", "tree-sitter", "jq"],
              "Heavy search and analysis tools"),
    ToolCombo("test_focused", ["pytest", "coverage", "docker"],
              "Test execution and coverage focused"),
    ToolCombo("full_dev", ["ripgrep", "ast-grep", "tree-sitter", "pytest", "coverage",
                           "ruff", "mypy", "git", "gh", "docker"],
              "Complete development toolchain"),
]


class ToolEcologySuite:
    """Benchmarks how tool combinations affect model performance.

    The key question: can weaker models + better tools outperform stronger models?
    """

    def __init__(self, models: list[str], task_runner: Callable):
        """Initialize the suite.

        Args:
            models: List of model IDs to test.
            task_runner: Callable(model_id, tool_names, task_id) → ToolResult.
        """
        self.models = models
        self.runner = task_runner
        self.results: list[ToolResult] = []

    def run(self, task_ids: list[str],
            combos: Optional[list[ToolCombo]] = None) -> dict:
        """Run benchmarks across model × tool_combo × task.

        Returns:
            Dict with results matrix suitable for heatmap visualization.
        """
        if combos is None:
            combos = PRESET_COMBOS

        self.results = []
        for model, combo, task in itertools.product(self.models, combos, task_ids):
            result = self.runner(model, combo.tools, task)
            self.results.append(result)

        return self.to_matrix()

    def to_matrix(self) -> dict:
        """Build model × combo average score matrix."""
        matrix = {}
        for model in self.models:
            matrix[model] = {}
            model_results = [r for r in self.results if r.model_id == model]
            combos_seen = set(tuple(r.tool_names) for r in model_results)
            for combo_tools in combos_seen:
                combo_results = [r for r in model_results if tuple(r.tool_names) == combo_tools]
                avg_score = sum(r.score for r in combo_results) / len(combo_results) if combo_results else 0.0
                combo_name = self._combo_name(tuple(combo_tools))
                matrix[model][combo_name] = {
                    "avg_score": round(avg_score, 4),
                    "avg_tokens": sum(r.tokens_used for r in combo_results) // max(1, len(combo_results)),
                    "avg_tool_calls": sum(r.tool_calls_made for r in combo_results) / max(1, len(combo_results)),
                }

        return matrix

    def best_combo_for(self, model_id: str) -> tuple[str, float]:
        """Find the best tool combination for a specific model."""
        matrix = self.to_matrix()
        if model_id not in matrix:
            return ("unknown", 0.0)
        best = max(matrix[model_id].items(), key=lambda x: x[1]["avg_score"])
        return best[0], best[1]["avg_score"]

    def synergy_score(self, tool_a: str, tool_b: str) -> float:
        """Estimate synergy between two tools.

        Positive = using both together is better than either alone.
        """
        a_alone = [r for r in self.results if set(r.tool_names) == {tool_a}]
        b_alone = [r for r in self.results if set(r.tool_names) == {tool_b}]
        together = [r for r in self.results if {tool_a, tool_b}.issubset(set(r.tool_names))]

        if not together:
            return 0.0

        a_avg = sum(r.score for r in a_alone) / len(a_alone) if a_alone else 0.0
        b_avg = sum(r.score for r in b_alone) / len(b_alone) if b_alone else 0.0
        together_avg = sum(r.score for r in together) / len(together)

        # Expected if independent: max(a, b)
        expected = max(a_avg, b_avg)
        if expected == 0:
            return 0.0
        return together_avg - expected

    def _combo_name(self, tools: tuple) -> str:
        """Find a friendly name for a tool combination."""
        for preset in PRESET_COMBOS:
            if set(preset.tools) == set(tools):
                return preset.name
        return "+".join(sorted(tools)[:4])  # Truncate long names
