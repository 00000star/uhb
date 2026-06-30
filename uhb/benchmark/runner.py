"""Benchmark runner — executes tasks against models and collects results."""

import time
import traceback
from typing import Optional

from uhb.core.models import BaseLLMBackend, Message, create_backend
from uhb.core.cost import CostTracker, Timer
from uhb.core.logging import get_logger

from .tasks.base import TaskBase, TaskResult
from .tasks.registry import TaskRegistry, get_registry, discover_tasks

log = get_logger(__name__)


class BenchmarkRunner:
    """Executes a suite of benchmark tasks against a model."""

    def __init__(self, model_key: str, registry: Optional[TaskRegistry] = None):
        self.model_key = model_key
        self.backend = create_backend(model_key)
        self.registry = registry or get_registry()
        self.results: list[TaskResult] = []

    def run_task(self, task: TaskBase, seed: int = 0) -> TaskResult:
        """Run a single task and return its result.

        Args:
            task: The task instance to run.
            seed: Deterministic seed for task generation.

        Returns:
            TaskResult with score and details.
        """
        log.info(f"Running task: {task.spec.task_id} (seed={seed})")

        # Generate fresh instance
        ctx = task.generate(seed=seed)

        # Get tools for this task
        tools = task.get_tools()

        # Build conversation
        messages = []
        if ctx.system_prompt:
            messages.append(Message(role="system", content=ctx.system_prompt))
        messages.append(Message(role="user", content=ctx.problem_statement))

        # Execute
        timer = Timer()
        try:
            task.setup()
            with timer:
                response = self.backend.send(
                    messages=messages,
                    tools=tools if tools else None,
                    max_tokens=task.spec.max_tokens,
                )
        except Exception as e:
            log.error(f"Task {task.spec.task_id} failed with error: {e}")
            traceback.print_exc()
            return TaskResult(
                task_id=task.spec.task_id,
                task_name=task.spec.name,
                dimension=task.spec.dimension,
                score=0.0,
                passed=False,
                error=str(e),
            )
        finally:
            task.teardown()

        # Record assistant response
        conversation = messages + [Message(role="assistant", content=response.content)]

        # Score
        result = task.score(ctx, response.content, conversation)
        result.details["latency_ms"] = round(timer.elapsed_ms, 1)
        if response.usage:
            result.details["tokens_input"] = response.usage.input_tokens
            result.details["tokens_output"] = response.usage.output_tokens

        log.info(f"  Score: {result.score:.2f} — {'PASS' if result.passed else 'FAIL'}")
        return result

    def run_all(self, seeds: int = 3, task_ids: Optional[list[str]] = None) -> list[TaskResult]:
        """Run all registered tasks.

        Args:
            seeds: Number of seeds to run per task (averaged).
            task_ids: Specific task IDs to run (None = all).

        Returns:
            List of TaskResults.
        """
        specs = self.registry.list_all()
        if task_ids:
            specs = [s for s in specs if s.task_id in task_ids]

        log.info(f"Running {len(specs)} tasks × {seeds} seeds against {self.model_key}")

        self.results = []
        for spec in specs:
            task_cls = self.registry.get(spec.task_id)
            if task_cls is None:
                log.warning(f"Task class not found for {spec.task_id}")
                continue

            task_seeds_results = []
            for seed in range(seeds):
                task_instance = task_cls()
                result = self.run_task(task_instance, seed=seed)
                task_seeds_results.append(result)

            # Average across seeds for this task
            avg_score = sum(r.score for r in task_seeds_results) / len(task_seeds_results)
            best_result = task_seeds_results[0]
            best_result.score = avg_score
            best_result.passed = avg_score >= task_cls().passing_threshold()
            best_result.details["seeds_run"] = seeds
            best_result.details["individual_scores"] = [r.score for r in task_seeds_results]

            self.results.append(best_result)

        return self.results

    def close(self) -> None:
        self.backend.close()
