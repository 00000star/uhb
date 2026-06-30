"""Main evolutionary loop — the core of harness optimization."""

import random
import time
from typing import Optional, Callable

from uhb.core.logging import get_logger

from .genome import HarnessGenome
from .population import Population
from .fitness import FitnessEvaluator
from .mutate import Mutator
from .crossover import CrossoverOperator
from .pareto import ParetoFrontier

log = get_logger(__name__)


class EvolutionEngine:
    """Orchestrates the evolutionary optimization of harness genomes.

    Algorithm:
    1. Initialize population with seeds + random genomes
    2. Evaluate fitness of all genomes
    3. While generation < max_generations:
       a. Select parents via tournament selection
       b. Crossover to produce offspring
       c. Mutate offspring
       d. Evaluate offspring fitness
       e. Replace population (elitism: keep top N)
       f. Track Pareto frontier
    4. Return best genome(s) and Pareto frontier
    """

    def __init__(self,
                 evaluator: FitnessEvaluator,
                 population_size: int = 50,
                 elite_count: int = 5,
                 tournament_size: int = 3,
                 crossover_rate: float = 0.7,
                 mutation_rate: float = 0.3,
                 seed: int = None):
        self.evaluator = evaluator
        self.population_size = population_size
        self.elite_count = elite_count
        self.tournament_size = tournament_size
        self.seed = seed

        self.rng = random.Random(seed)
        self.population = Population(size=population_size, seed=seed)
        self.crossover = CrossoverOperator(crossover_rate=crossover_rate, seed=seed)
        self.mutator = Mutator(mutation_rate=mutation_rate, seed=seed)
        self.pareto = ParetoFrontier()

        self.history: list[dict] = []
        self.best_genome: Optional[HarnessGenome] = None
        self.best_fitness = 0.0

    def run(self, max_generations: int = 20,
            target_fitness: float = 0.95,
            early_stop_patience: int = 5,
            callback: Optional[Callable] = None) -> dict:
        """Run the evolutionary optimization.

        Args:
            max_generations: Maximum generations to evolve.
            target_fitness: Stop if best fitness reaches this threshold.
            early_stop_patience: Stop if no improvement for N generations.
            callback: Called after each generation with (generation, population, pareto).

        Returns:
            Dict with evolution results.
        """
        # Phase 1: Initialize
        log.info(f"Initializing population of {self.population_size} genomes")
        self.population.initialize()
        self.population.update_fitness(self.evaluator)

        best = self.population.best_genome()
        self.best_genome = best
        self.best_fitness = self.population.fitness_scores.get(best.hash()).combined if best.hash() in self.population.fitness_scores else 0.0

        self.pareto.update(self.population.genomes, self.population.fitness_scores)
        self._record_generation()

        patience_counter = 0

        # Phase 2: Evolve
        for gen in range(1, max_generations + 1):
            self.population.generation = gen

            # Selection + Crossover
            parents = [self.population.tournament_select(self.tournament_size)
                      for _ in range(self.population_size)]
            offspring = self.crossover.crossover_population(parents, self.population_size)

            # Mutation
            offspring = self.mutator.mutate_population(offspring, keep_elites=0)

            # Replace population with elitism
            elites = self.population.select_elites(self.elite_count)
            new_population = elites + offspring[:self.population_size - self.elite_count]
            self.population.genomes = new_population

            # Evaluate
            self.population.update_fitness(self.evaluator)
            self.pareto.update(self.population.genomes, self.population.fitness_scores)
            self._record_generation()

            # Check for improvement
            current_best = self.population.best_genome()
            current_fitness = self.population.fitness_scores.get(current_best.hash()).combined if current_best.hash() in self.population.fitness_scores else 0.0

            if current_fitness > self.best_fitness:
                self.best_genome = current_best
                old_best = self.best_fitness
                self.best_fitness = current_fitness
                patience_counter = 0
                log.info(f"Gen {gen}: new best fitness {current_fitness:.4f} (was {old_best:.4f})")
            else:
                patience_counter += 1

            log.info(f"Gen {gen}: best={self.best_fitness:.4f} avg={self.population.average_fitness():.4f} "
                    f"diversity={self.population.diversity():.2f} pareto_size={self.pareto.size}")

            if callback:
                callback(gen, self.population, self.pareto)

            # Early stopping
            if self.best_fitness >= target_fitness:
                log.info(f"Target fitness {target_fitness} reached at generation {gen}")
                break
            if patience_counter >= early_stop_patience:
                log.info(f"No improvement for {early_stop_patience} generations, stopping")
                break

        return self.results()

    def _record_generation(self) -> None:
        self.history.append(self.population.stats())

    def results(self) -> dict:
        """Return evolution results."""
        return {
            "generations_run": self.population.generation,
            "best_genome": self.best_genome.to_dict() if self.best_genome else None,
            "best_genome_display": self.best_genome.display() if self.best_genome else "",
            "best_fitness": self.best_fitness,
            "pareto_frontier": [g.to_dict() for g in self.pareto.genomes],
            "pareto_size": self.pareto.size,
            "history": self.history,
        }
