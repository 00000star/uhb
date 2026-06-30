"""Population management for harness genome evolution."""

import random
from typing import Optional

from .genome import HarnessGenome, DEFAULT_GENOME, COMPREHENSIVE_GENOME, MINIMAL_GENOME, ALL_GENES, Gene


def random_genome(rng: random.Random, min_length: int = 2, max_length: int = 8) -> HarnessGenome:
    """Generate a random harness genome.

    Args:
        rng: Random number generator for reproducibility.
        min_length: Minimum number of genes.
        max_length: Maximum number of genes.

    Returns:
        A randomly generated HarnessGenome.
    """
    length = rng.randint(min_length, max_length)
    genes = [rng.choice(ALL_GENES) for _ in range(length)]

    # Ensure CODE and TEST are present (they're essential)
    if Gene.CODE not in genes:
        genes.insert(rng.randint(0, len(genes)), Gene.CODE)
    if Gene.TEST not in genes:
        genes.insert(rng.randint(0, len(genes)), Gene.TEST)

    strategies = ["full", "sliding_window", "summary"]
    policies = ["all", "limited", "read_only"]
    retries = ["none", "on_failure", "always"]

    return HarnessGenome(
        genes=genes,
        context_strategy=rng.choice(strategies),
        tool_policy=rng.choice(policies),
        retry_policy=rng.choice(retries),
        max_retries=rng.randint(1, 5),
    )


class Population:
    """A population of harness genomes evolving toward optimal fitness."""

    # Seed genomes that are always included
    SEED_GENOMES = [
        HarnessGenome(genes=DEFAULT_GENOME),                                  # PLN → COD → TST → REV
        HarnessGenome(genes=list(COMPREHENSIVE_GENOME)),                      # Full pipeline
        HarnessGenome(genes=[Gene.CODE, Gene.TEST]),                          # Code & test only
        HarnessGenome(genes=[Gene.PLAN, Gene.RESEARCH, Gene.CODE, Gene.TEST]), # Research-heavy
        HarnessGenome(genes=[Gene.CODE, Gene.TEST, Gene.REPAIR, Gene.TEST]),  # Test-repair loop
        HarnessGenome(genes=[Gene.PLAN, Gene.CODE, Gene.TEST, Gene.REPAIR, Gene.REVIEW]),
        HarnessGenome(genes=[Gene.RESEARCH, Gene.CODE, Gene.ANALYZE, Gene.TEST, Gene.SECURITY, Gene.REVIEW]),
    ]

    def __init__(self, size: int = 50, seed: int = None):
        self.size = size
        self.rng = random.Random(seed)
        self.genomes: list[HarnessGenome] = []
        self.fitness_scores: dict[str, any] = {}  # genome hash → FitnessScore
        self.generation = 0

    def initialize(self) -> list[HarnessGenome]:
        """Initialize the population with seed genomes + random genomes."""
        self.genomes = []

        # Add all seed genomes (up to half the population)
        seeds_to_add = self.SEED_GENOMES[:max(2, self.size // 4)]
        self.genomes.extend(seeds_to_add)

        # Fill the rest with random genomes
        while len(self.genomes) < self.size:
            genome = random_genome(self.rng)
            # Avoid duplicates (by hash)
            if genome.hash() not in {g.hash() for g in self.genomes}:
                self.genomes.append(genome)

        self.generation = 0
        return self.genomes

    def select_elites(self, n: int) -> list[HarnessGenome]:
        """Select the top N genomes by fitness."""
        scored = [(g, self.fitness_scores.get(g.hash())) for g in self.genomes]
        scored.sort(key=lambda x: x[1].combined if x[1] else 0.0, reverse=True)
        return [g for g, _ in scored[:n]]

    def tournament_select(self, tournament_size: int = 3) -> HarnessGenome:
        """Select a genome using tournament selection."""
        candidates = self.rng.sample(self.genomes, min(tournament_size, len(self.genomes)))
        best = max(candidates, key=lambda g: self.fitness_scores.get(g.hash()).combined
                   if self.fitness_scores.get(g.hash()) else 0.0)
        return best

    def update_fitness(self, evaluator) -> None:
        """Update fitness scores for all genomes."""
        scores = evaluator.evaluate_population(self.genomes)
        for genome, score in zip(self.genomes, scores):
            self.fitness_scores[genome.hash()] = score

    def best_genome(self) -> HarnessGenome:
        """Return the genome with the highest fitness."""
        if not self.fitness_scores:
            return self.genomes[0]
        return max(self.genomes,
                   key=lambda g: self.fitness_scores.get(g.hash()).combined
                   if self.fitness_scores.get(g.hash()) else 0.0)

    def average_fitness(self) -> float:
        """Average combined fitness across the population."""
        scores = [self.fitness_scores.get(g.hash()) for g in self.genomes]
        valid = [s.combined for s in scores if s]
        return sum(valid) / len(valid) if valid else 0.0

    def diversity(self) -> float:
        """Measure genetic diversity (unique hashes / population size)."""
        unique = len({g.hash() for g in self.genomes})
        return unique / len(self.genomes) if self.genomes else 0.0

    def stats(self) -> dict:
        """Population statistics."""
        return {
            "generation": self.generation,
            "size": len(self.genomes),
            "best_fitness": self.fitness_scores.get(self.best_genome().hash()).combined
                            if self.best_genome().hash() in self.fitness_scores else 0.0,
            "avg_fitness": self.average_fitness(),
            "diversity": self.diversity(),
        }
