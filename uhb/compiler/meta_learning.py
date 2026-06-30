"""Meta-learning engine — learns harness rules from benchmark data.

Discovers patterns like:
  IF reasoning > 90 AND planning < 60 THEN force planning
  IF long_context < 70 THEN use sliding_window
"""

from dataclasses import dataclass, field
from typing import Optional, Any
import json
from pathlib import Path


@dataclass
class LearnedRule:
    """A rule learned from benchmark data."""
    condition: str           # e.g., "dimensions.reasoning > 0.85 AND dimensions.planning < 0.60"
    action: str              # e.g., "force_gene('plan', position='first')"
    confidence: float        # 0.0–1.0
    evidence_count: int      # how many data points support this rule
    source: str = ""         # where this rule came from


class MetaLearningEngine:
    """Learns rules from benchmark data to predict optimal harness configs.

    Over time, builds a knowledge base that can predict good harnesses
    without running expensive searches for each new model.
    """

    def __init__(self, rules_file: Optional[Path] = None):
        self.rules: list[LearnedRule] = []
        self.rules_file = rules_file
        if rules_file and rules_file.exists():
            self.load(rules_file)

    def learn_from_profiles(self, profiles: list[dict],
                           optimal_harnesses: list[dict]) -> list[LearnedRule]:
        """Learn rules from (profile, optimal_harness) pairs.

        Args:
            profiles: List of capability profiles.
            optimal_harnesses: Corresponding optimal harness configs.

        Returns:
            Newly learned rules.
        """
        new_rules = []

        for profile, harness in zip(profiles, optimal_harnesses):
            dims = profile.get("dimensions", {})
            genes = harness.get("genes", [])

            # Rule: high reasoning + low planning → force plan
            reasoning = dims.get("reasoning")
            planning = dims.get("planning")
            if reasoning is not None and planning is not None:
                if reasoning > 0.85 and planning < 0.60:
                    if "plan" in genes and genes.index("plan") == 0:
                        rule = LearnedRule(
                            condition="reasoning > 0.85 AND planning < 0.60",
                            action="force_gene('plan', position='first')",
                            confidence=0.80,
                            evidence_count=1,
                            source=profile.get("model_id", "unknown"),
                        )
                        self._add_rule(rule)
                        new_rules.append(rule)

            # Rule: low context → sliding window
            long_ctx = dims.get("long_context")
            if long_ctx is not None and long_ctx < 0.70:
                ctx_strategy = harness.get("context_strategy", "full")
                if ctx_strategy == "sliding_window":
                    rule = LearnedRule(
                        condition="long_context < 0.70",
                        action="set_context_strategy('sliding_window')",
                        confidence=0.75,
                        evidence_count=1,
                        source=profile.get("model_id", "unknown"),
                    )
                    self._add_rule(rule)
                    new_rules.append(rule)

            # Rule: low self_repair → add repair step
            self_repair = dims.get("self_repair")
            if self_repair is not None and self_repair < 0.70:
                if "repair" in genes:
                    rule = LearnedRule(
                        condition="self_repair < 0.70",
                        action="add_gene('repair')",
                        confidence=0.70,
                        evidence_count=1,
                        source=profile.get("model_id", "unknown"),
                    )
                    self._add_rule(rule)
                    new_rules.append(rule)

            # Rule: low tool_usage → limited tools + compensating tools
            tool_usage = dims.get("tool_usage")
            if tool_usage is not None and tool_usage < 0.75:
                tool_policy = harness.get("tool_policy", "all")
                if tool_policy == "limited":
                    rule = LearnedRule(
                        condition="tool_usage < 0.75",
                        action="set_tool_policy('limited') AND recommend_tools(['ripgrep', 'tree-sitter'])",
                        confidence=0.65,
                        evidence_count=1,
                        source=profile.get("model_id", "unknown"),
                    )
                    self._add_rule(rule)
                    new_rules.append(rule)

        return new_rules

    def _add_rule(self, rule: LearnedRule) -> None:
        """Add a rule, merging with existing similar rules."""
        for existing in self.rules:
            if existing.condition == rule.condition and existing.action == rule.action:
                # Merge: update confidence with weighted average
                total = existing.evidence_count + rule.evidence_count
                existing.confidence = (
                    existing.confidence * existing.evidence_count
                    + rule.confidence * rule.evidence_count
                ) / total
                existing.evidence_count = total
                return
        self.rules.append(rule)

    def predict(self, profile: dict) -> list[LearnedRule]:
        """Find all rules that match a given profile.

        Args:
            profile: A capability profile dict.

        Returns:
            List of matching rules.
        """
        dims = profile.get("dimensions", {})
        matching = []

        for rule in self.rules:
            if self._rule_matches(rule, dims):
                matching.append(rule)

        return sorted(matching, key=lambda r: r.confidence, reverse=True)

    def _rule_matches(self, rule: LearnedRule, dims: dict) -> bool:
        """Check if a rule's condition matches the given dimensions."""
        condition = rule.condition
        # Simple evaluation: parse dimension references and thresholds
        try:
            # Replace dimension references
            for dim_name in ["reasoning", "coding", "planning", "tool_usage",
                           "long_context", "self_repair", "instruction_following",
                           "exploration", "creativity", "speed"]:
                if dim_name in condition:
                    val = dims.get(dim_name)
                    if val is None:
                        continue
                    # Replace threshold checks
                    import re
                    pattern = rf'{dim_name}\s*<\s*([\d.]+)'
                    match = re.search(pattern, condition)
                    if match:
                        threshold = float(match.group(1))
                        if not (val < threshold):
                            return False
                    pattern = rf'{dim_name}\s*>\s*([\d.]+)'
                    match = re.search(pattern, condition)
                    if match:
                        threshold = float(match.group(1))
                        if not (val > threshold):
                            return False

            # Handle AND/OR logic
            if "AND" in condition:
                # Already checked each clause above via return False
                pass

            return True
        except Exception:
            return False

    def save(self, path: Path) -> None:
        """Save learned rules to a JSON file."""
        data = {
            "rules": [
                {
                    "condition": r.condition,
                    "action": r.action,
                    "confidence": r.confidence,
                    "evidence_count": r.evidence_count,
                    "source": r.source,
                }
                for r in self.rules
            ]
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2))

    def load(self, path: Path) -> None:
        """Load learned rules from a JSON file."""
        data = json.loads(path.read_text())
        self.rules = [
            LearnedRule(**r) for r in data.get("rules", [])
        ]
