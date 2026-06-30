"""Leaderboard — public and private rankings from community data."""

from typing import Optional

from .schema import CommunityDataset, CommunityRun


class Leaderboard:
    """Generates leaderboards from community benchmark data."""

    def __init__(self, dataset: CommunityDataset):
        self.dataset = dataset

    def top_models(self, n: int = 10, environment: Optional[str] = None) -> list[dict]:
        """Top N models by average score."""
        runs = self.dataset.load_all()
        if environment:
            runs = [r for r in runs if r.environment == environment]

        # Aggregate by model
        model_scores = {}
        for run in runs:
            if run.model not in model_scores:
                model_scores[run.model] = []
            model_scores[run.model].append(run.score)

        rankings = []
        for model, scores in model_scores.items():
            avg = sum(scores) / len(scores)
            rankings.append({
                "model": model,
                "avg_score": round(avg, 4),
                "runs": len(scores),
                "success_rate": round(sum(1 for s in scores if s >= 0.8) / len(scores), 4) if scores else 0.0,
                "avg_cost": round(sum(r.cost_usd for r in runs if r.model == model) / max(1, len(scores)), 4),
            })

        rankings.sort(key=lambda x: x["avg_score"], reverse=True)
        return rankings[:n]

    def top_harnesses(self, model: str, n: int = 5) -> list[dict]:
        """Top N harness configurations for a specific model."""
        runs = [r for r in self.dataset.load_all() if r.model == model]

        # Aggregate by harness signature
        harness_scores = {}
        for run in runs:
            sig = " → ".join(run.harness_genes) if run.harness_genes else "unknown"
            if sig not in harness_scores:
                harness_scores[sig] = []
            harness_scores[sig].append(run.score)

        rankings = []
        for sig, scores in harness_scores.items():
            avg = sum(scores) / len(scores)
            rankings.append({
                "harness": sig,
                "avg_score": round(avg, 4),
                "runs": len(scores),
            })

        rankings.sort(key=lambda x: x["avg_score"], reverse=True)
        return rankings[:n]

    def top_environments(self, model: str) -> list[dict]:
        """Best environments for a specific model."""
        runs = [r for r in self.dataset.load_all() if r.model == model]

        env_scores = {}
        for run in runs:
            if run.environment not in env_scores:
                env_scores[run.environment] = []
            env_scores[run.environment].append(run.score)

        rankings = []
        for env, scores in env_scores.items():
            avg = sum(scores) / len(scores)
            rankings.append({
                "environment": env,
                "avg_score": round(avg, 4),
                "runs": len(scores),
            })

        rankings.sort(key=lambda x: x["avg_score"], reverse=True)
        return rankings

    def most_cost_effective(self, n: int = 10) -> list[dict]:
        """Top N most cost-effective model+harness combinations."""
        runs = self.dataset.load_all()

        combos = {}
        for run in runs:
            key = f"{run.model} | {'→'.join(run.harness_genes) if run.harness_genes else 'default'}"
            if key not in combos:
                combos[key] = {"scores": [], "costs": []}
            combos[key]["scores"].append(run.score)
            combos[key]["costs"].append(run.cost_usd)

        rankings = []
        for key, data in combos.items():
            avg_score = sum(data["scores"]) / len(data["scores"])
            avg_cost = sum(data["costs"]) / len(data["costs"])
            efficiency = avg_score / max(0.001, avg_cost)
            rankings.append({
                "combo": key,
                "avg_score": round(avg_score, 4),
                "avg_cost": round(avg_cost, 4),
                "efficiency": round(efficiency, 2),
            })

        rankings.sort(key=lambda x: x["efficiency"], reverse=True)
        return rankings[:n]

    def print_leaderboard(self, top_n: int = 10) -> str:
        """Render a text leaderboard."""
        lines = ["=" * 70, "UHB Community Leaderboard", "=" * 70, ""]

        lines.append("Top Models:")
        for i, entry in enumerate(self.top_models(top_n), 1):
            lines.append(f"  {i:>2}. {entry['model']:<35} "
                        f"Score: {entry['avg_score']:.3f}  "
                        f"Runs: {entry['runs']}  "
                        f"Success: {entry['success_rate']:.1%}")

        lines.append("")
        lines.append("Most Cost-Effective:")
        for i, entry in enumerate(self.most_cost_effective(5), 1):
            lines.append(f"  {i}. {entry['combo']}")
            lines.append(f"     Score: {entry['avg_score']:.3f}  "
                        f"Cost: ${entry['avg_cost']:.4f}  "
                        f"Efficiency: {entry['efficiency']}")

        return "\n".join(lines)
