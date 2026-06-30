"""Rule engine — knowledge base of harness generation rules.

Rules map capability profile dimensions → harness configuration decisions.
Grows over time as more benchmark data is collected.
"""

from dataclasses import dataclass, field
from typing import Optional, Callable


@dataclass
class Rule:
    """A single harness generation rule."""
    name: str
    description: str
    condition: Callable[[dict], bool]  # profile → True if rule applies
    apply: Callable[[dict, dict], None]  # (harness_config, profile) → modifies config in place
    priority: int = 0                  # higher = applied first
    source: str = "heuristic"          # "heuristic", "learned", "manual"


class RuleEngine:
    """Evaluates and applies rules to generate harness configurations."""

    def __init__(self):
        self.rules: list[Rule] = []
        self._register_default_rules()

    def _register_default_rules(self) -> None:
        """Register the default heuristic rule set."""

        # Planning rules
        self.add(Rule(
            name="force_plan_for_low_planners",
            description="If reasoning is strong but planning is weak, force a plan step first",
            condition=lambda p: (
                (p.get("reasoning") or 0) > 0.85
                and (p.get("planning") or 0) < 0.60
            ),
            apply=lambda h, p: self._insert_gene(h, "plan", 0),
            priority=10,
        ))

        self.add(Rule(
            name="add_research_for_strong_planners",
            description="If planning is strong, add a research step before planning",
            condition=lambda p: (p.get("planning") or 0) > 0.80,
            apply=lambda h, p: self._insert_gene_before(h, "research", "plan"),
            priority=5,
        ))

        # Context rules
        self.add(Rule(
            name="sliding_window_for_low_long_context",
            description="If long-context retention is poor, use sliding window",
            condition=lambda p: (p.get("long_context") or 1.0) < 0.70,
            apply=lambda h, p: h.update({"context_strategy": "sliding_window"}),
            priority=8,
        ))

        self.add(Rule(
            name="summary_for_high_long_context",
            description="If long-context is excellent, use summaries to save tokens",
            condition=lambda p: (p.get("long_context") or 0) > 0.90,
            apply=lambda h, p: h.update({"context_strategy": "summary"}),
            priority=3,
        ))

        # Self-repair rules
        self.add(Rule(
            name="repair_loop_for_low_self_repair",
            description="If self-repair is weak, add test→repair→test loop with more retries",
            condition=lambda p: (p.get("self_repair") or 1.0) < 0.50,
            apply=lambda h, p: self._add_repair_loop(h),
            priority=9,
        ))

        self.add(Rule(
            name="minimal_retry_for_high_self_repair",
            description="If self-repair is strong, minimal retry overhead",
            condition=lambda p: (p.get("self_repair") or 0) > 0.90,
            apply=lambda h, p: h.update({"retry_policy": "none", "max_retries": 1}),
            priority=4,
        ))

        # Tool usage rules
        self.add(Rule(
            name="compensating_tools_for_low_tool_usage",
            description="If tool usage is poor, use limited tools + explicit recommendations",
            condition=lambda p: (p.get("tool_usage") or 1.0) < 0.75,
            apply=lambda h, p: h.update({
                "tool_policy": "limited",
                "recommended_tools": ["ripgrep", "tree-sitter", "pytest"],
            }),
            priority=7,
        ))

        self.add(Rule(
            name="full_tools_for_high_tool_usage",
            description="If tool usage is excellent, give full tool access",
            condition=lambda p: (p.get("tool_usage") or 0) > 0.90,
            apply=lambda h, p: h.update({"tool_policy": "all"}),
            priority=3,
        ))

        # Exploration rules
        self.add(Rule(
            name="review_after_each_for_low_exploration",
            description="Low exploration → review after each step to catch issues",
            condition=lambda p: (p.get("exploration") or 1.0) < 0.50,
            apply=lambda h, p: h.update({"review_policy": "after_each"}),
            priority=6,
        ))

        # Speed rules
        self.add(Rule(
            name="parallelize_for_slow_models",
            description="Slow models benefit from parallelizable steps",
            condition=lambda p: (p.get("speed") or 1.0) < 0.50,
            apply=lambda h, p: h.update({"parallelize": True}),
            priority=4,
        ))

    def add(self, rule: Rule) -> None:
        """Register a new rule."""
        self.rules.append(rule)
        self.rules.sort(key=lambda r: r.priority, reverse=True)

    def apply_all(self, profile: dict, harness_config: dict) -> dict:
        """Apply all matching rules to build a harness configuration.

        Args:
            profile: Capability profile dict.
            harness_config: Initial harness config (will be modified).

        Returns:
            Modified harness config.
        """
        dims = profile.get("dimensions", {})
        for rule in self.rules:
            try:
                if rule.condition(dims):
                    rule.apply(harness_config, dims)
            except Exception:
                pass
        return harness_config

    @staticmethod
    def _insert_gene(config: dict, gene: str, position: int) -> None:
        genes = config.get("genes", [])
        if gene not in genes:
            genes.insert(position, gene)
            config["genes"] = genes

    @staticmethod
    def _insert_gene_before(config: dict, gene: str, target: str) -> None:
        genes = config.get("genes", [])
        if gene not in genes:
            try:
                idx = genes.index(target)
                genes.insert(idx, gene)
            except ValueError:
                genes.append(gene)
            config["genes"] = genes

    @staticmethod
    def _add_repair_loop(config: dict) -> None:
        genes = config.get("genes", [])
        if "repair" not in genes:
            try:
                idx = genes.index("test")
                genes.insert(idx + 1, "repair")
                genes.insert(idx + 2, "test")
            except ValueError:
                genes.extend(["repair", "test"])
            config["genes"] = genes
        config.update({"retry_policy": "always", "max_retries": 5})
