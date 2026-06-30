"""Mutation operators for harness genome evolution.

Operators: reorder, duplicate, remove, merge, split, conditional, insert.
"""

import random
from typing import Callable

from .genome import HarnessGenome, Gene, ALL_GENES


def mutate_reorder(genome: HarnessGenome, rng: random.Random) -> HarnessGenome:
    """Swap two random genes."""
    if len(genome) < 2:
        return genome
    i = rng.randint(0, len(genome) - 1)
    j = rng.randint(0, len(genome) - 1)
    return genome.reorder(i, j)


def mutate_duplicate(genome: HarnessGenome, rng: random.Random) -> HarnessGenome:
    """Duplicate a random gene."""
    i = rng.randint(0, len(genome) - 1)
    return genome.duplicate(i)


def mutate_remove(genome: HarnessGenome, rng: random.Random) -> HarnessGenome:
    """Remove a random gene (minimum 2 genes)."""
    if len(genome) <= 2:
        return genome
    i = rng.randint(0, len(genome) - 1)
    return genome.remove(i)


def mutate_merge(genome: HarnessGenome, rng: random.Random) -> HarnessGenome:
    """Merge two adjacent genes into one."""
    if len(genome) < 2:
        return genome
    i = rng.randint(0, len(genome) - 2)
    return genome.merge(i, i + 1)


def mutate_split(genome: HarnessGenome, rng: random.Random) -> HarnessGenome:
    """Split a gene into two specialized variants."""
    i = rng.randint(0, len(genome) - 1)
    return genome.split(i)


def mutate_conditional(genome: HarnessGenome, rng: random.Random) -> HarnessGenome:
    """Add a conditional branch at a random position."""
    if len(genome) < 2:
        return genome
    i = rng.randint(0, len(genome) - 2)
    condition = rng.choice([Gene.TEST, Gene.ANALYZE, Gene.REVIEW])
    success = [rng.choice(ALL_GENES)]
    failure = [Gene.REPAIR]
    return genome.conditional(i, condition, success, failure)


def mutate_insert(genome: HarnessGenome, rng: random.Random) -> HarnessGenome:
    """Insert a random gene at a random position."""
    gene = rng.choice(ALL_GENES)
    i = rng.randint(0, len(genome))
    return genome.insert(i, gene)


def mutate_context_strategy(genome: HarnessGenome, rng: random.Random) -> HarnessGenome:
    """Change context strategy."""
    strategies = ["full", "sliding_window", "summary"]
    new = genome.copy()
    current = new.context_strategy
    choices = [s for s in strategies if s != current]
    if choices:
        new.context_strategy = rng.choice(choices)
    return new


def mutate_tool_policy(genome: HarnessGenome, rng: random.Random) -> HarnessGenome:
    """Change tool policy."""
    policies = ["all", "limited", "read_only"]
    new = genome.copy()
    current = new.tool_policy
    choices = [p for p in policies if p != current]
    if choices:
        new.tool_policy = rng.choice(choices)
    return new


def mutate_retry_policy(genome: HarnessGenome, rng: random.Random) -> HarnessGenome:
    """Change retry policy."""
    policies = ["none", "on_failure", "always"]
    new = genome.copy()
    current = new.retry_policy
    choices = [p for p in policies if p != current]
    if choices:
        new.retry_policy = rng.choice(choices)
    return new


# Registry of mutation operators with relative weights
MUTATION_OPERATORS: list[tuple[Callable, float]] = [
    (mutate_reorder, 0.15),
    (mutate_duplicate, 0.10),
    (mutate_remove, 0.10),
    (mutate_merge, 0.10),
    (mutate_split, 0.10),
    (mutate_conditional, 0.10),
    (mutate_insert, 0.15),
    (mutate_context_strategy, 0.05),
    (mutate_tool_policy, 0.05),
    (mutate_retry_policy, 0.10),
]


class Mutator:
    """Applies mutation operators to genomes probabilistically."""

    def __init__(self, operators: list[tuple[Callable, float]] = None,
                 mutation_rate: float = 0.3, seed: int = None):
        self.operators = operators or MUTATION_OPERATORS
        self.mutation_rate = mutation_rate
        self.rng = random.Random(seed)

    def mutate(self, genome: HarnessGenome) -> HarnessGenome:
        """Apply mutation with probability = mutation_rate.

        May apply multiple mutations in one pass (compound mutation).
        """
        result = genome.copy()
        while self.rng.random() < self.mutation_rate:
            # Weighted random selection of operator
            total_weight = sum(w for _, w in self.operators)
            r = self.rng.random() * total_weight
            cumulative = 0
            for op, weight in self.operators:
                cumulative += weight
                if r <= cumulative:
                    result = op(result, self.rng)
                    break
        return result

    def mutate_population(self, population: list[HarnessGenome],
                          keep_elites: int = 2) -> list[HarnessGenome]:
        """Mutate all genomes in a population, preserving elites."""
        elites = population[:keep_elites]
        mutated = [self.mutate(g) for g in population[keep_elites:]]
        return elites + mutated
