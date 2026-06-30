"""Harness evolution engine — discover optimal workflows through genetic algorithms."""

from .genome import HarnessGenome, Gene, ALL_GENES
from .population import Population
from .fitness import FitnessEvaluator, FitnessScore, MultiObjectiveFitness
from .mutate import Mutator, MUTATION_OPERATORS
from .crossover import CrossoverOperator
from .evolve import EvolutionEngine
from .pareto import ParetoFrontier
from .harness_search import HarnessSearcher

__version__ = "0.1.0"
__all__ = [
    "HarnessGenome", "Gene", "ALL_GENES",
    "Population", "FitnessEvaluator", "FitnessScore", "MultiObjectiveFitness",
    "Mutator", "MUTATION_OPERATORS", "CrossoverOperator",
    "EvolutionEngine", "ParetoFrontier", "HarnessSearcher",
]
