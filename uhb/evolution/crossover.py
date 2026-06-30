"""Crossover operators for harness genome recombination.

Performs two-parent recombination at gene boundaries.
"""

import random
from typing import Optional

from .genome import HarnessGenome


class CrossoverOperator:
    """Performs genetic crossover between two parent genomes."""

    def __init__(self, crossover_rate: float = 0.7, seed: int = None):
        self.crossover_rate = crossover_rate
        self.rng = random.Random(seed)

    def single_point(self, parent1: HarnessGenome,
                     parent2: HarnessGenome) -> tuple[HarnessGenome, HarnessGenome]:
        """Single-point crossover: split each at random point, swap tails."""
        if len(parent1) < 2 or len(parent2) < 2:
            return parent1.copy(), parent2.copy()

        cp1 = self.rng.randint(1, len(parent1) - 1)
        cp2 = self.rng.randint(1, len(parent2) - 1)

        child1_genes = parent1.genes[:cp1] + parent2.genes[cp2:]
        child2_genes = parent2.genes[:cp2] + parent1.genes[cp1:]

        child1 = HarnessGenome(
            genes=list(child1_genes),
            context_strategy=parent1.context_strategy if self.rng.random() < 0.5 else parent2.context_strategy,
            tool_policy=parent1.tool_policy if self.rng.random() < 0.5 else parent2.tool_policy,
            retry_policy=parent1.retry_policy if self.rng.random() < 0.5 else parent2.retry_policy,
            max_retries=parent1.max_retries if self.rng.random() < 0.5 else parent2.max_retries,
        )

        child2 = HarnessGenome(
            genes=list(child2_genes),
            context_strategy=parent2.context_strategy if self.rng.random() < 0.5 else parent1.context_strategy,
            tool_policy=parent2.tool_policy if self.rng.random() < 0.5 else parent1.tool_policy,
            retry_policy=parent2.retry_policy if self.rng.random() < 0.5 else parent1.retry_policy,
            max_retries=parent2.max_retries if self.rng.random() < 0.5 else parent1.max_retries,
        )

        return child1, child2

    def uniform(self, parent1: HarnessGenome,
                parent2: HarnessGenome) -> tuple[HarnessGenome, HarnessGenome]:
        """Uniform crossover: each gene independently from either parent."""
        max_len = max(len(parent1), len(parent2))
        p1_padded = list(parent1.genes) + [None] * (max_len - len(parent1))
        p2_padded = list(parent2.genes) + [None] * (max_len - len(parent2))

        child1_genes = []
        child2_genes = []
        for g1, g2 in zip(p1_padded, p2_padded):
            if g1 is None and g2 is None:
                continue
            if g1 is None:
                child1_genes.append(g2); child2_genes.append(g2)
            elif g2 is None:
                child1_genes.append(g1); child2_genes.append(g1)
            elif self.rng.random() < 0.5:
                child1_genes.append(g1); child2_genes.append(g2)
            else:
                child1_genes.append(g2); child2_genes.append(g1)

        child1 = HarnessGenome(genes=[g for g in child1_genes if g is not None])
        child2 = HarnessGenome(genes=[g for g in child2_genes if g is not None])
        return child1, child2

    def crossover(self, parent1: HarnessGenome,
                  parent2: HarnessGenome) -> tuple[HarnessGenome, HarnessGenome]:
        """Perform crossover with probability = crossover_rate.

        Returns (child1, child2) — may be copies of parents if no crossover.
        """
        if self.rng.random() > self.crossover_rate:
            return parent1.copy(), parent2.copy()
        return self.single_point(parent1, parent2)

    def crossover_population(self, parents: list[HarnessGenome],
                             target_size: int) -> list[HarnessGenome]:
        """Generate a new population through crossover of selected parents.

        Uses tournament selection within the parents list.
        """
        if len(parents) < 2:
            return [p.copy() for p in parents * target_size]

        offspring = []
        while len(offspring) < target_size:
            # Tournament selection: pick 2 random parents
            p1 = self.rng.choice(parents)
            p2 = self.rng.choice(parents)
            c1, c2 = self.crossover(p1, p2)
            offspring.append(c1)
            if len(offspring) < target_size:
                offspring.append(c2)

        return offspring[:target_size]
