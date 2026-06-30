"""Harness compiler — takes a capability profile and outputs an optimal harness."""

from dataclasses import dataclass, field
from typing import Optional

from .rules import RuleEngine
from .meta_learning import MetaLearningEngine


@dataclass
class CompiledHarness:
    """Output of the harness compiler — a complete harness specification."""
    model_id: str
    genes: list[str]                # ordered workflow steps
    context_strategy: str
    tool_policy: str
    retry_policy: str
    review_policy: str
    max_retries: int
    recommended_tools: list[str]    # tools that complement this model
    rationale: str                  # why this harness was chosen
    confidence: float               # 0.0–1.0 confidence in this recommendation

    def to_dict(self) -> dict:
        return {
            "model_id": self.model_id,
            "genes": self.genes,
            "context_strategy": self.context_strategy,
            "tool_policy": self.tool_policy,
            "retry_policy": self.retry_policy,
            "review_policy": self.review_policy,
            "max_retries": self.max_retries,
            "recommended_tools": self.recommended_tools,
            "rationale": self.rationale,
            "confidence": self.confidence,
        }


class HarnessCompiler:
    """Compiles a capability profile into an optimal harness configuration.

    Uses:
    1. Cached results from evolution/search (fastest)
    2. Meta-learned rules (heuristic)
    3. Preset templates (fallback)
    """

    def __init__(self, rule_engine: Optional[RuleEngine] = None,
                 meta_engine: Optional[MetaLearningEngine] = None):
        self.rules = rule_engine or RuleEngine()
        self.meta = meta_engine or MetaLearningEngine()

    def compile(self, profile: dict, search_results: Optional[list] = None) -> CompiledHarness:
        """Compile a harness for the given capability profile.

        Args:
            profile: A capability profile dict (from uhb.benchmark.report.generate_profile).
            search_results: Optional pre-computed search/evolution results.

        Returns:
            A CompiledHarness with the optimal configuration.
        """
        model_id = profile.get("model_id", "unknown")
        dimensions = profile.get("dimensions", {})

        # Strategy 1: Use search/evolution results if available
        if search_results:
            best = search_results[0] if search_results else None
            if best:
                return self._from_search_result(model_id, best)

        # Strategy 2: Apply meta-learned rules
        harness = self._from_rules(model_id, dimensions)

        # Strategy 3: Fall back to heuristic defaults
        if harness is None:
            harness = self._default_harness(model_id)

        return harness

    def _from_search_result(self, model_id: str, result: tuple) -> CompiledHarness:
        """Build from a search result (genome, fitness)."""
        genome, fitness = result[0], result[1]
        return CompiledHarness(
            model_id=model_id,
            genes=[g.value for g in genome.genes],
            context_strategy=genome.context_strategy,
            tool_policy=genome.tool_policy,
            retry_policy=genome.retry_policy,
            review_policy=genome.review_policy,
            max_retries=genome.max_retries,
            recommended_tools=[],
            rationale=f"Discovered via evolutionary search (fitness={fitness:.4f})",
            confidence=min(1.0, fitness * 1.1),
        )

    def _from_rules(self, model_id: str, dimensions: dict) -> Optional[CompiledHarness]:
        """Apply meta-learned rules to generate a harness."""
        rules_fired = []

        genes = ["plan", "code", "test", "review"]  # default
        context = "full"
        tool_policy = "all"
        retry = "on_failure"
        review = "after_each"
        max_retries = 3
        tools = []
        confidence = 0.5

        # Rule: if reasoning > 0.90 AND planning < 0.60 → force planning
        reasoning = dimensions.get("reasoning", 0.5)
        planning = dimensions.get("planning", 0.5)
        if reasoning is not None and planning is not None:
            if reasoning > 0.85 and planning < 0.60:
                if "plan" not in genes:
                    genes.insert(0, "plan")
                rules_fired.append("High reasoning + low planning → forced planning step")
                confidence += 0.15

        # Rule: if long_context < 0.70 → sliding window
        long_ctx = dimensions.get("long_context", 0.8)
        if long_ctx is not None and long_ctx < 0.70:
            context = "sliding_window"
            rules_fired.append("Low long-context retention → sliding window strategy")
            confidence += 0.10

        # Rule: if self_repair < 0.70 → add repair step after test
        self_repair = dimensions.get("self_repair", 0.8)
        if self_repair is not None:
            if self_repair < 0.50:
                genes.insert(genes.index("test") + 1 if "test" in genes else len(genes), "repair")
                genes.insert(genes.index("repair") + 1, "test")  # test again after repair
                rules_fired.append("Low self-repair → added test-repair retest loop")
                retry = "always"
                max_retries = 5
                confidence += 0.10
            elif self_repair < 0.70:
                retry = "on_failure"
                max_retries = 3
                if "repair" not in genes:
                    genes.insert(genes.index("test") + 1 if "test" in genes else len(genes), "repair")

        # Rule: if tool_usage < 0.75 → recommend compensating tools
        tool_usage = dimensions.get("tool_usage", 0.8)
        if tool_usage is not None and tool_usage < 0.75:
            tool_policy = "limited"
            tools = ["ripgrep", "tree-sitter", "pytest"]
            rules_fired.append("Low tool usage → limited tool policy with compensating tools")
            confidence += 0.10

        # Rule: if planning > 0.80 → add research step
        if planning is not None and planning > 0.80:
            if "research" not in genes and "plan" in genes:
                genes.insert(genes.index("plan"), "research")
                rules_fired.append("High planning ability → added research step before planning")

        # Rule: if exploration < 0.50 → add explicit instructions in prompt
        exploration = dimensions.get("exploration", 0.6)
        if exploration is not None and exploration < 0.50:
            review = "after_each"
            rules_fired.append("Low exploration → review after each step")
            confidence += 0.05

        # Remove duplicate consecutive genes
        deduped = []
        for g in genes:
            if not deduped or deduped[-1] != g:
                deduped.append(g)
        genes = deduped

        return CompiledHarness(
            model_id=model_id,
            genes=genes,
            context_strategy=context,
            tool_policy=tool_policy,
            retry_policy=retry,
            review_policy=review,
            max_retries=max_retries,
            recommended_tools=tools,
            rationale="; ".join(rules_fired) if rules_fired else "Rule-based compilation",
            confidence=min(1.0, confidence),
        )

    def _default_harness(self, model_id: str) -> CompiledHarness:
        """Fallback default harness."""
        return CompiledHarness(
            model_id=model_id,
            genes=["plan", "code", "test", "review"],
            context_strategy="full",
            tool_policy="all",
            retry_policy="on_failure",
            review_policy="after_each",
            max_retries=3,
            recommended_tools=["ripgrep", "git", "pytest"],
            rationale="Default harness — no profile data available",
            confidence=0.3,
        )


def compile_from_profile(profile: dict, search_results: list = None) -> dict:
    """Convenience function: compile a harness from a profile dict.

    Args:
        profile: Capability profile dict.
        search_results: Optional search/evolution results.

    Returns:
        CompiledHarness as dict.
    """
    compiler = HarnessCompiler()
    return compiler.compile(profile, search_results).to_dict()
