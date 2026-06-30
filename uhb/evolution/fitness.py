"""Fitness evaluation — multi-objective scoring of harness genomes.

Objectives:
1. Success rate (weight: 0.50) — does the task pass?
2. Token cost (weight: 0.20) — how many tokens consumed?
3. Wall time (weight: 0.15) — how fast?
4. Retry count (weight: 0.15) — how many retries needed?
5. Autonomy (bonus) — human interventions required?
"""

import random
from dataclasses import dataclass, field
from typing import Optional, Callable

from .genome import HarnessGenome


@dataclass
class FitnessScore:
    """Multi-objective fitness for a single harness genome."""
    genome_hash: str
    success_rate: float = 0.0       # 0.0–1.0
    cost_efficiency: float = 0.0    # 1.0 - (cost / max_cost), higher is better
    speed_score: float = 0.0        # 1.0 - (time / max_time), higher is better
    retry_penalty: float = 0.0      # 0.0–1.0, lower is better
    autonomy_score: float = 0.0     # 1.0 = fully autonomous
    combined: float = 0.0           # Weighted combination

    def __post_init__(self):
        self.combined = self._combine()

    def _combine(self) -> float:
        return (
            0.50 * self.success_rate
            + 0.20 * self.cost_efficiency
            + 0.15 * self.speed_score
            + 0.10 * self.retry_penalty
            + 0.05 * self.autonomy_score
        )

    def to_dict(self) -> dict:
        return {
            "genome_hash": self.genome_hash,
            "success_rate": round(self.success_rate, 4),
            "cost_efficiency": round(self.cost_efficiency, 4),
            "speed_score": round(self.speed_score, 4),
            "retry_penalty": round(self.retry_penalty, 4),
            "autonomy_score": round(self.autonomy_score, 4),
            "combined": round(self.combined, 4),
        }


@dataclass
class MultiObjectiveFitness:
    """Holds the Pareto-optimal objectives for multi-objective optimization."""
    objectives: dict[str, float] = field(default_factory=dict)

    def dominates(self, other: "MultiObjectiveFitness") -> bool:
        """Check if this fitness Pareto-dominates another.

        Self dominates other if: all objectives >= other's, and at least one is >.
        """
        if set(self.objectives.keys()) != set(other.objectives.keys()):
            return False
        at_least_one_better = False
        for key in self.objectives:
            if self.objectives[key] < other.objectives[key]:
                return False
            if self.objectives[key] > other.objectives[key]:
                at_least_one_better = True
        return at_least_one_better


class FitnessEvaluator:
    """Evaluates harness genome fitness by running benchmarks."""

    def __init__(self, benchmark_fn: Callable, max_cost_usd: float = 10.0,
                 max_time_seconds: float = 300.0):
        """Initialize the evaluator.

        Args:
            benchmark_fn: Function(genome: HarnessGenome) -> dict with keys:
                          success, cost_usd, time_seconds, retries, autonomous.
            max_cost_usd: Maximum expected cost for normalization.
            max_time_seconds: Maximum expected time for normalization.
        """
        self.benchmark = benchmark_fn
        self.max_cost = max_cost_usd
        self.max_time = max_time_seconds
        self.cache: dict[str, FitnessScore] = {}

    async def evaluate(self, genome: HarnessGenome) -> FitnessScore:
        """Evaluate fitness of a genome.

        Uses caching to avoid re-evaluating identical genomes.
        """
        h = genome.hash()
        if h in self.cache:
            return self.cache[h]

        import asyncio
        import inspect

        # Run the benchmark concurrently
        if inspect.iscoroutinefunction(self.benchmark):
            result = await self.benchmark(genome)
        else:
            result = await asyncio.to_thread(self.benchmark, genome)

        # Normalize each objective
        success_rate = result.get("success", 0.0)
        cost_efficiency = max(0.0, 1.0 - result.get("cost_usd", 0.0) / self.max_cost)
        speed_score = max(0.0, 1.0 - result.get("time_seconds", 0.0) / self.max_time)
        retries = result.get("retries", 0)
        retry_penalty = max(0.0, 1.0 - retries / 5)  # 0 retries = 1.0, 5+ = 0.0
        autonomy = result.get("autonomous", True)

        score = FitnessScore(
            genome_hash=h,
            success_rate=success_rate,
            cost_efficiency=cost_efficiency,
            speed_score=speed_score,
            retry_penalty=retry_penalty,
            autonomy_score=1.0 if autonomy else 0.5,
        )

        self.cache[h] = score
        return score

    async def _evaluate_population_async(self, population: list[HarnessGenome]) -> list[FitnessScore]:
        import asyncio
        return await asyncio.gather(*(self.evaluate(g) for g in population))

    def evaluate_population(self, population: list[HarnessGenome]) -> list[FitnessScore]:
        """Evaluate fitness for all genomes in a population concurrently."""
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            # If already in an event loop, we should avoid asyncio.run
            # In a real setup, if EvolutionEngine becomes async, this should just be await
            import nest_asyncio
            nest_asyncio.apply()
            return loop.run_until_complete(self._evaluate_population_async(population))
        except RuntimeError:
            return asyncio.run(self._evaluate_population_async(population))
