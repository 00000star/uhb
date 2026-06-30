"""Pareto frontier — track non-dominated solutions in multi-objective optimization."""

from typing import Optional

from .genome import HarnessGenome
from .fitness import FitnessScore


class ParetoFrontier:
    """Maintains the set of non-dominated (Pareto-optimal) solutions.

    A solution A dominates solution B if A is at least as good as B
    in all objectives and strictly better in at least one.
    """

    def __init__(self):
        self.genomes: list[HarnessGenome] = []
        self.scores: dict[str, FitnessScore] = {}

    def update(self, genomes: list[HarnessGenome],
               fitness_scores: dict[str, FitnessScore]) -> None:
        """Update the frontier with new genomes.

        For each new genome:
        1. If dominated by any existing frontier member → skip
        2. If dominates any existing frontier members → remove them
        3. Add to frontier
        """
        for genome in genomes:
            h = genome.hash()
            if h not in fitness_scores:
                continue

            score = fitness_scores[h]
            self._add(genome, score)

    def _add(self, genome: HarnessGenome, score: FitnessScore) -> bool:
        """Attempt to add a genome to the frontier.

        Returns True if added, False if dominated.
        """
        h = genome.hash()

        # Check if dominated by any existing member
        for existing_h, existing_score in self.scores.items():
            if self._dominates(existing_score, score):
                return False  # New genome is dominated

        # Remove any existing members dominated by the new genome
        dominated_keys = []
        for existing_h, existing_score in self.scores.items():
            if self._dominates(score, existing_score):
                dominated_keys.append(existing_h)

        for key in dominated_keys:
            self.scores.pop(key, None)
            self.genomes = [g for g in self.genomes if g.hash() != key]

        # Add to frontier
        self.genomes.append(genome)
        self.scores[h] = score
        return True

    @staticmethod
    def _dominates(a: FitnessScore, b: FitnessScore) -> bool:
        """Check if solution A Pareto-dominates solution B."""
        objectives_a = [a.success_rate, a.cost_efficiency, a.speed_score,
                       a.retry_penalty, a.autonomy_score]
        objectives_b = [b.success_rate, b.cost_efficiency, b.speed_score,
                       b.retry_penalty, b.autonomy_score]

        at_least_one_better = False
        for va, vb in zip(objectives_a, objectives_b):
            if va < vb:
                return False
            if va > vb:
                at_least_one_better = True
        return at_least_one_better

    @property
    def size(self) -> int:
        return len(self.genomes)

    def best_by_objective(self, objective: str) -> Optional[HarnessGenome]:
        """Get the best genome for a specific objective."""
        if not self.scores:
            return None

        if objective == "success_rate":
            key = max(self.scores, key=lambda h: self.scores[h].success_rate)
        elif objective == "cost_efficiency":
            key = max(self.scores, key=lambda h: self.scores[h].cost_efficiency)
        elif objective == "speed_score":
            key = max(self.scores, key=lambda h: self.scores[h].speed_score)
        else:
            key = max(self.scores, key=lambda h: self.scores[h].combined)

        for g in self.genomes:
            if g.hash() == key:
                return g
        return None

    def to_dict(self) -> dict:
        """Export the Pareto frontier."""
        return {
            "size": self.size,
            "points": [
                {
                    "genome": g.to_dict(),
                    "genome_display": g.display(),
                    "fitness": self.scores[g.hash()].to_dict(),
                }
                for g in self.genomes
            ],
        }
