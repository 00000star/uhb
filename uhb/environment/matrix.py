"""Environment matrix — cross environment × model testing.

Runs the same tasks across multiple environments to measure
how model performance varies by development context.
"""

import itertools
from dataclasses import dataclass, field
from typing import Optional

from uhb.core.logging import get_logger
from . import BaseEnvironment, create_environment, ENV_REGISTRY

log = get_logger(__name__)


@dataclass
class MatrixCell:
    """A single cell in the environment matrix."""
    model: str
    environment: str
    task_id: str
    score: float = 0.0
    passed: bool = False
    error: Optional[str] = None


@dataclass
class MatrixResult:
    """Full matrix results."""
    models: list[str]
    environments: list[str]
    tasks: list[str]
    cells: list[MatrixCell] = field(default_factory=list)

    def get_cell(self, model: str, env: str, task: str) -> Optional[MatrixCell]:
        for c in self.cells:
            if c.model == model and c.environment == env and c.task_id == task:
                return c
        return None

    def model_env_average(self, model: str, env: str) -> float:
        scores = [
            c.score for c in self.cells
            if c.model == model and c.environment == env and c.error is None
        ]
        return sum(scores) / len(scores) if scores else 0.0

    def to_heatmap(self) -> dict:
        """Generate a heatmap: model × environment → average score."""
        heatmap = {}
        for model in self.models:
            heatmap[model] = {}
            for env in self.environments:
                heatmap[model][env] = self.model_env_average(model, env)
        return heatmap

    def best_environment_for(self, model: str) -> tuple[str, float]:
        """Find the best environment for a specific model."""
        best_env = ""
        best_score = -1.0
        for env in self.environments:
            score = self.model_env_average(model, env)
            if score > best_score:
                best_score = score
                best_env = env
        return best_env, best_score

    def summary(self) -> str:
        lines = ["=" * 70, "Environment Matrix Results", "=" * 70]
        heatmap = self.to_heatmap()

        header = f"{'Model':<30}" + "".join(f"{e:<14}" for e in self.environments)
        lines.append(header)
        lines.append("-" * len(header))

        for model in self.models:
            row = f"{model:<30}"
            for env in self.environments:
                score = heatmap[model][env]
                row += f"{score:<14.3f}"
            lines.append(row)

        lines.append("")
        lines.append("Best environment per model:")
        for model in self.models:
            env, score = self.best_environment_for(model)
            lines.append(f"  {model}: {env} ({score:.3f})")

        return "\n".join(lines)


class MatrixRunner:
    """Runs benchmarks across the environment matrix."""

    def __init__(self, models: list[str], environments: Optional[list[str]] = None,
                 tasks: Optional[list[str]] = None):
        self.models = models
        self.environments = environments or list(ENV_REGISTRY.keys())
        self.tasks = tasks or []  # populated later from benchmark registry

    def run(self, benchmark_runner_factory, task_ids: Optional[list[str]] = None) -> MatrixResult:
        """Run benchmarks across all model × environment combinations.

        Args:
            benchmark_runner_factory: Callable(model_key) → BenchmarkRunner.
            task_ids: Specific tasks to run.

        Returns:
            MatrixResult with all cell scores.
        """
        from uhb.benchmark.tasks.registry import discover_tasks, get_registry

        if not self.tasks:
            registry = discover_tasks("uhb.benchmark.tasks")
            self.tasks = [s.task_id for s in registry.list_all()]
        if task_ids:
            self.tasks = task_ids

        result = MatrixResult(
            models=self.models,
            environments=self.environments,
            tasks=self.tasks,
        )

        total = len(self.models) * len(self.environments) * len(self.tasks)
        done = 0
        log.info(f"Running environment matrix: {total} total cells")

        for model, env_id in itertools.product(self.models, self.environments):
            log.info(f"  Model={model}, Environment={env_id}")

            try:
                runner = benchmark_runner_factory(model)
                env_results = runner.run_all(seeds=1, task_ids=self.tasks)

                for task_result in env_results:
                    result.cells.append(MatrixCell(
                        model=model,
                        environment=env_id,
                        task_id=task_result.task_id,
                        score=task_result.score,
                        passed=task_result.passed,
                        error=task_result.error,
                    ))
                    done += 1
            except Exception as e:
                log.error(f"  Failed model={model} env={env_id}: {e}")
                # Fill all tasks for this cell with errors
                for task_id in self.tasks:
                    result.cells.append(MatrixCell(
                        model=model,
                        environment=env_id,
                        task_id=task_id,
                        score=0.0,
                        error=str(e),
                    ))
            finally:
                if 'runner' in dir():
                    runner.close()

        log.info(f"Matrix complete: {done}/{total} cells")
        return result
