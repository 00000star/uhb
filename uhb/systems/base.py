"""Base class for AI coding system targets.

Every AI coding system (Claude Code, Codex CLI, Aider, etc.) implements this interface.
The benchmark treats each system as a black box.
"""

import abc
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class SystemOutput:
    """Output from an AI coding system after executing a task."""
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    files_changed: list[str] = field(default_factory=list)
    test_results: Optional[dict] = None
    duration_seconds: float = 0.0
    tool_calls_made: int = 0
    human_interventions: int = 0
    success: bool = False


@dataclass
class SystemState:
    """Observable state of the system before/after a task."""
    cwd: str = ""
    branch: str = ""
    files_modified: list[str] = field(default_factory=list)
    test_suite_passing: bool = True
    lint_errors: int = 0


class AICodingSystem(abc.ABC):
    """Abstract base for any AI coding system.

    To add a new system, subclass this and implement the four methods.
    """

    def __init__(self, name: str, version: str = "unknown"):
        self.name = name
        self.version = version

    @abc.abstractmethod
    def setup(self, repo: Path) -> SystemState:
        """Prepare the system to work on a repository.

        Args:
            repo: Path to the repository to work on.

        Returns:
            Initial system state.
        """
        ...

    @abc.abstractmethod
    def send_task(self, task: str) -> SystemOutput:
        """Send a task to the system and get the output.

        Args:
            task: Natural language task description.

        Returns:
            SystemOutput with results.
        """
        ...

    @abc.abstractmethod
    def observe(self) -> SystemState:
        """Observe the current state of the system.

        Returns:
            Current system state.
        """
        ...

    @abc.abstractmethod
    def teardown(self) -> None:
        """Clean up after benchmarking."""
        ...

    def __repr__(self) -> str:
        return f"{self.name} v{self.version}"
