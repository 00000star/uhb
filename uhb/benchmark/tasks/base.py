"""Task base class — every benchmark task implements this."""

import abc
from dataclasses import dataclass, field
from typing import Optional, Any

from uhb.core.models import BaseLLMBackend, Message, ToolDefinition


@dataclass
class TaskSpec:
    """Describes a task to be benchmarked."""
    task_id: str                    # unique, e.g. "code_from_spec_001"
    name: str                       # human-readable name
    description: str                # what the task measures
    dimension: str                  # capability dimension this falls under
    difficulty: str = "medium"      # easy, medium, hard
    max_tokens: int = 16_000        # token budget for this task
    time_limit_seconds: int = 600   # wall-clock limit
    environment: str = "terminal"   # default environment to run in


@dataclass
class TaskContext:
    """The context provided to a model for a task."""
    system_prompt: str = ""
    problem_statement: str = ""     # the task description for the model
    starter_code: str = ""          # optional: code to modify/start from
    test_code: str = ""             # test suite to evaluate against
    files: dict[str, str] = field(default_factory=dict)  # filename → content
    tools_enabled: list[str] = field(default_factory=list)  # tool names available


@dataclass
class TaskResult:
    """Result of executing a single task."""
    task_id: str
    task_name: str
    dimension: str
    score: float                    # 0.0–1.0 normalized score
    passed: bool                    # did it meet the passing threshold?
    details: dict = field(default_factory=dict)
    model_output: str = ""
    error: Optional[str] = None


class TaskBase(abc.ABC):
    """Abstract base class for all benchmark tasks.

    To add a new task type:
    1. Create a subpackage under tasks/
    2. Subclass TaskBase
    3. The registry auto-discovers it
    """

    spec: TaskSpec

    @abc.abstractmethod
    def generate(self, seed: int = 0) -> TaskContext:
        """Generate a fresh task instance from the given seed.

        Seeds MUST be deterministic: same seed = same task.
        This prevents benchmark contamination through memorization.
        """
        ...

    @abc.abstractmethod
    def score(self, context: TaskContext, model_output: str,
              conversation: list[Message]) -> TaskResult:
        """Score the model's output against expected behavior.

        Args:
            context: The task context that was given to the model.
            model_output: The model's final text output.
            conversation: The full conversation history.

        Returns:
            A TaskResult with a normalized score (0.0–1.0).
        """
        ...

    def get_tools(self) -> list[ToolDefinition]:
        """Return tools the model is allowed to use for this task.

        Override in subclasses that need specific tools.
        """
        return []

    def setup(self) -> None:
        """Optional setup before task execution (create files, start services)."""
        pass

    def teardown(self) -> None:
        """Optional cleanup after task execution."""
        pass

    def passing_threshold(self) -> float:
        """Score threshold to consider the task passed. Override for harder tasks."""
        if self.spec.difficulty == "hard":
            return 0.7
        return 0.8
