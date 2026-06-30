"""System benchmark runner — executes tasks against AI coding systems."""

import time
import tempfile
from pathlib import Path
from typing import Optional, Callable

from uhb.core.logging import get_logger

from .base import AICodingSystem, SystemOutput, SystemState
from .metrics import SystemProfile, SystemMetric
from .compare import SystemComparator

log = get_logger(__name__)


# Task definitions for system-level benchmarking
SYSTEM_TASKS = {
    SystemMetric.REPO_UNDERSTANDING: [
        "Explain the architecture of this project. What are the main modules and how do they interact?",
        "What design patterns are used in this codebase? Give specific examples.",
        "Find the most complex function in this project and explain what it does.",
    ],
    SystemMetric.ARCHITECTURE: [
        "What are the architectural weaknesses of this project? Suggest 3 improvements.",
        "If we needed to add a new feature (user authentication), where would you add it and why?",
        "Identify any circular dependencies or tight coupling in this codebase.",
    ],
    SystemMetric.REFACTORING: [
        "Find a function that could be improved and refactor it. Make sure tests still pass.",
        "Identify duplicate code and consolidate it into a shared utility.",
    ],
    SystemMetric.DEBUGGING: [
        "I've noticed a bug: the application sometimes returns incorrect results for edge cases. Find and fix it.",
        "Run the test suite. If any tests fail, fix the code until all pass.",
    ],
    SystemMetric.TESTING: [
        "Write unit tests for the main business logic. Aim for 80%+ coverage on new code.",
        "Add integration tests for the most important user flows.",
    ],
    SystemMetric.PLANNING: [
        "Plan the implementation of a REST API versioning migration. Break it down into steps.",
        "Design a feature flag system. Produce a detailed implementation plan.",
    ],
    SystemMetric.DOCUMENTATION: [
        "Generate API documentation for the public-facing functions in this project.",
        "Write a comprehensive README for this project including setup, usage, and architecture.",
    ],
    SystemMetric.AUTONOMY: [
        "Add a simple feature (request logging middleware) end-to-end without asking questions.",
        "Set up CI/CD pipeline configuration for this project.",
    ],
    SystemMetric.RECOVERY: [
        "I intentionally broke the build by removing a critical import. Fix it and get tests passing again.",
        "The database connection string is wrong. Find and fix the configuration issue.",
    ],
    SystemMetric.COST_EFFICIENCY: [
        # Measured automatically from all tasks
    ],
}


class SystemBenchmarkRunner:
    """Runs system-level benchmarks against AI coding systems."""

    def __init__(self, system: AICodingSystem, repo_path: Path):
        self.system = system
        self.repo_path = repo_path
        self.profile = SystemProfile(
            system_name=system.name,
            system_version=system.version,
            repo_used=str(repo_path),
        )

    def run(self, dimensions: Optional[list[SystemMetric]] = None,
            tasks_per_dimension: int = 2) -> SystemProfile:
        """Run the benchmark.

        Args:
            dimensions: Which dimensions to benchmark (default: all).
            tasks_per_dimension: Number of tasks per dimension.

        Returns:
            SystemProfile with scores.
        """
        if dimensions is None:
            dimensions = list(SystemMetric)

        log.info(f"Benchmarking {self.system.name} on {self.repo_path}")

        # Setup
        start_time = time.monotonic()
        try:
            initial_state = self.system.setup(self.repo_path)
        except Exception as e:
            log.error(f"Setup failed: {e}")
            return self.profile

        for dim in dimensions:
            if dim == SystemMetric.COST_EFFICIENCY:
                continue  # Computed from other tasks

            tasks = SYSTEM_TASKS.get(dim, [])
            if not tasks:
                continue

            dim_scores = []
            for i, task in enumerate(tasks[:tasks_per_dimension]):
                log.info(f"  [{dim.value}] Task {i+1}: {task[:80]}...")

                try:
                    output = self.system.send_task(task)
                    state = self.system.observe()

                    # Score based on output
                    score = self._score_output(dim, task, output, state)
                    dim_scores.append(score)

                    self.profile.task_results.append({
                        "dimension": dim.value,
                        "task": task,
                        "success": output.success,
                        "duration": output.duration_seconds,
                        "human_interventions": output.human_interventions,
                        "score": score,
                    })

                    self.profile.total_cost_usd += self._estimate_cost(output)
                    self.profile.total_human_interventions += output.human_interventions

                except Exception as e:
                    log.error(f"  Task failed: {e}")
                    dim_scores.append(0.0)

            # Average score for this dimension
            if dim_scores:
                self.profile.dimensions[dim.value] = round(
                    sum(dim_scores) / len(dim_scores), 4
                )

        # Cost efficiency: overall_score / cost
        if self.profile.total_cost_usd > 0:
            self.profile.dimensions[SystemMetric.COST_EFFICIENCY.value] = round(
                min(1.0, self.profile.overall_score() / (self.profile.total_cost_usd + 0.01)), 4
            )
        else:
            self.profile.dimensions[SystemMetric.COST_EFFICIENCY.value] = 1.0

        self.profile.total_time_seconds = time.monotonic() - start_time

        # Teardown
        try:
            self.system.teardown()
        except Exception:
            pass

        return self.profile

    def _score_output(self, dim: SystemMetric, task: str,
                      output: SystemOutput, state: SystemState) -> float:
        """Score a task output rigorously."""
        score = 0.0

        # Success flag based on process termination / output
        if output.success:
            score += 0.2

        # Rigorous checks: 
        # Files actually modified?
        if state.files_modified or output.files_changed:
            score += 0.3
            
        # Tests still passing?
        if state.test_suite_passing:
            score += 0.2
        else:
            score -= 0.2 # Penalty for breaking tests
            
        # Lint errors?
        if state.lint_errors == 0:
            score += 0.1
        else:
            score -= 0.1

        # Specific dimension heuristics
        if dim == SystemMetric.DOCUMENTATION:
            if any(ext in str(state.files_modified) for ext in ['.md', '.rst', '.txt']) or "def " not in output.stdout:
                score += 0.2
        
        if dim == SystemMetric.TESTING:
            if any("test" in f.lower() for f in state.files_modified):
                score += 0.2

        # Independent tool use
        if output.tool_calls_made > 0:
            score += 0.1

        # Penalty for requiring human intervention
        if output.human_interventions > 0:
            score -= (output.human_interventions * 0.1)

        return max(0.0, min(1.0, score))

    def _estimate_cost(self, output: SystemOutput) -> float:
        """Estimate cost from output characteristics.

        This is a rough heuristic. In production, hook into actual API cost tracking.
        """
        # Rough estimate: $0.01 per tool call, $0.001 per 100 chars of output
        tool_cost = output.tool_calls_made * 0.01
        output_cost = len(output.stdout) / 100 * 0.001
        return tool_cost + output_cost
