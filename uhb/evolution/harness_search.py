"""Harness search — grid search, Bayesian optimization, and random search.

Three search strategies for finding optimal harness configurations
without running the full evolutionary algorithm.
"""

import random
import itertools
from typing import Optional, Callable

from uhb.core.logging import get_logger

from .genome import HarnessGenome, ALL_GENES, Gene, DEFAULT_GENOME

log = get_logger(__name__)


class HarnessSearcher:
    """Search harness configuration space for optimal settings."""

    def __init__(self, evaluator_fn: Callable[[HarnessGenome], float]):
        """Initialize with an evaluator that returns a single fitness score."""
        self.evaluate = evaluator_fn  # (genome) -> fitness (0.0–1.0)
        self.results: list[tuple[HarnessGenome, float]] = []

    def grid_search(self, gene_permutations: Optional[list[list[Gene]]] = None,
                    context_strategies: Optional[list[str]] = None,
                    tool_policies: Optional[list[str]] = None,
                    retry_policies: Optional[list[str]] = None,
                    max_configs: int = 200) -> list[tuple[HarnessGenome, float]]:
        """Exhaustive grid search over specified parameters.

        Args:
            gene_permutations: List of gene sequences to try.
            context_strategies: Context strategies to try.
            tool_policies: Tool policies to try.
            retry_policies: Retry policies to try.
            max_configs: Maximum number of configs to evaluate (to prevent explosion).

        Returns:
            List of (genome, fitness) sorted by fitness descending.
        """
        if gene_permutations is None:
            # Default: try several reasonable gene sequences
            gene_permutations = [
                [Gene.CODE, Gene.TEST],
                [Gene.PLAN, Gene.CODE, Gene.TEST],
                [Gene.PLAN, Gene.CODE, Gene.TEST, Gene.REVIEW],
                [Gene.RESEARCH, Gene.CODE, Gene.TEST],
                [Gene.PLAN, Gene.CODE, Gene.TEST, Gene.REPAIR, Gene.REVIEW],
                [Gene.RESEARCH, Gene.PLAN, Gene.CODE, Gene.TEST, Gene.REVIEW],
                [Gene.CODE, Gene.TEST, Gene.REPAIR, Gene.TEST],
                [Gene.RESEARCH, Gene.PLAN, Gene.ARCHITECT, Gene.CODE, Gene.TEST, Gene.REVIEW],
            ]

        if context_strategies is None:
            context_strategies = ["full", "sliding_window", "summary"]
        if tool_policies is None:
            tool_policies = ["all", "limited"]
        if retry_policies is None:
            retry_policies = ["none", "on_failure"]

        configs = list(itertools.product(
            gene_permutations, context_strategies, tool_policies, retry_policies
        ))

        # Limit to prevent explosion
        if len(configs) > max_configs:
            rng = random.Random(42)
            configs = rng.sample(configs, max_configs)

        log.info(f"Grid search: {len(configs)} configurations")
        self.results = []

        for i, (genes, ctx, tool, retry) in enumerate(configs):
            genome = HarnessGenome(
                genes=list(genes),
                context_strategy=ctx,
                tool_policy=tool,
                retry_policy=retry,
            )
            fitness = self.evaluate(genome)
            self.results.append((genome, fitness))

            if i % 50 == 0:
                log.info(f"  Grid search progress: {i}/{len(configs)}")

        self.results.sort(key=lambda x: x[1], reverse=True)
        return self.results

    def random_search(self, num_configs: int = 100,
                      seed: int = None) -> list[tuple[HarnessGenome, float]]:
        """Random search over the genome space.

        Args:
            num_configs: Number of random configurations to try.
            seed: Random seed for reproducibility.

        Returns:
            List of (genome, fitness) sorted by fitness descending.
        """
        from .population import random_genome

        rng = random.Random(seed)
        log.info(f"Random search: {num_configs} configurations")
        self.results = []

        for i in range(num_configs):
            genome = random_genome(rng)
            fitness = self.evaluate(genome)
            self.results.append((genome, fitness))

        self.results.sort(key=lambda x: x[1], reverse=True)
        return self.results

    def best(self, n: int = 5) -> list[tuple[HarnessGenome, float]]:
        """Return the top N results."""
        return self.results[:n]

    def best_genome(self) -> Optional[HarnessGenome]:
        """Return the single best genome found."""
        if not self.results:
            return None
        return self.results[0][0]
