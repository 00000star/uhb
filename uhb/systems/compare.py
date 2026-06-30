"""Cross-system comparison — side-by-side evaluation of AI coding systems."""

from dataclasses import dataclass, field
from typing import Optional

from .metrics import SystemProfile, SystemMetric


@dataclass
class SystemComparison:
    """Side-by-side comparison of multiple AI coding systems."""
    profiles: list[SystemProfile] = field(default_factory=list)

    def add(self, profile: SystemProfile) -> None:
        self.profiles.append(profile)

    def dimension_comparison(self, dim: SystemMetric) -> dict[str, float]:
        """Get all systems' scores for a dimension."""
        return {
            p.system_name: p.dimensions.get(dim.value)
            for p in self.profiles
        }

    def winner_per_dimension(self) -> dict[str, str]:
        """Find which system wins each dimension."""
        winners = {}
        for dim in SystemMetric:
            best_system = None
            best_score = -1.0
            for p in self.profiles:
                score = p.dimensions.get(dim.value)
                if score is not None and score > best_score:
                    best_score = score
                    best_system = p.system_name
            winners[dim.value] = best_system
        return winners

    def overall_ranking(self) -> list[tuple[str, float]]:
        """Rank systems by overall score."""
        ranked = [(p.system_name, p.overall_score()) for p in self.profiles]
        return sorted(ranked, key=lambda x: x[1], reverse=True)

    def cost_efficiency_ranking(self) -> list[tuple[str, float]]:
        """Rank by score per dollar."""
        ranked = []
        for p in self.profiles:
            if p.total_cost_usd > 0:
                efficiency = p.overall_score() / p.total_cost_usd
            else:
                efficiency = float('inf')
            ranked.append((p.system_name, efficiency))
        return sorted(ranked, key=lambda x: x[1], reverse=True)

    def to_dict(self) -> dict:
        return {
            "rankings": {
                "overall": [(name, round(score, 4)) for name, score in self.overall_ranking()],
                "cost_efficiency": [(name, round(eff, 4)) for name, eff in self.cost_efficiency_ranking()],
            },
            "dimension_winners": self.winner_per_dimension(),
            "profiles": [p.to_dict() for p in self.profiles],
        }

    def report(self) -> str:
        lines = ["=" * 70, "AI Coding System Comparison", "=" * 70, ""]

        lines.append("Overall Ranking:")
        for i, (name, score) in enumerate(self.overall_ranking(), 1):
            lines.append(f"  {i}. {name}: {score:.3f}")

        lines.append("")
        lines.append("Cost Efficiency (score/$):")
        for i, (name, eff) in enumerate(self.cost_efficiency_ranking(), 1):
            lines.append(f"  {i}. {name}: {eff:.2f}")

        lines.append("")
        lines.append("Dimension Winners:")
        for dim, winner in self.winner_per_dimension().items():
            lines.append(f"  {dim}: {winner}")

        lines.append("")
        lines.append(f"{'System':<20} {'Overall':<10} {'Cost':<10} {'Time':<10} {'Interventions'}")
        lines.append("-" * 60)
        for p in self.profiles:
            lines.append(f"{p.system_name:<20} {p.overall_score():<10.3f} "
                        f"${p.total_cost_usd:<9.2f} {p.total_time_seconds:<9.0f}s "
                        f"{p.total_human_interventions:<14}")

        return "\n".join(lines)


class SystemComparator:
    """Manages comparison of multiple AI coding systems."""

    def __init__(self):
        self.comparison = SystemComparison()

    def add_system(self, profile: SystemProfile) -> None:
        self.comparison.add(profile)

    def compare(self) -> SystemComparison:
        return self.comparison

    def save(self, path: str) -> None:
        """Save comparison to JSON."""
        import json
        from pathlib import Path
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.comparison.to_dict(), indent=2))
