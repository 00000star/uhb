"""Task registry — auto-discovers and catalogs all TaskBase subclasses."""

import importlib
import pkgutil
from pathlib import Path
from typing import Dict, Type, Optional

from .base import TaskBase, TaskSpec


class TaskRegistry:
    """Registry of all available benchmark tasks."""

    def __init__(self):
        self._tasks: Dict[str, Type[TaskBase]] = {}

    def register(self, task_cls: Type[TaskBase]) -> None:
        """Register a task class."""
        # Instantiate temporarily to get the spec
        instance = task_cls()
        self._tasks[instance.spec.task_id] = task_cls

    def get(self, task_id: str) -> Optional[Type[TaskBase]]:
        """Get a task class by ID."""
        return self._tasks.get(task_id)

    def list_all(self) -> list[TaskSpec]:
        """List all registered task specs."""
        specs = []
        for cls in self._tasks.values():
            specs.append(cls().spec)
        return specs

    def list_by_dimension(self, dimension: str) -> list[TaskSpec]:
        """List tasks for a specific capability dimension."""
        return [s for s in self.list_all() if s.dimension == dimension]

    @property
    def dimensions(self) -> list[str]:
        """Return all unique dimensions covered."""
        return sorted(set(s.dimension for s in self.list_all()))

    @property
    def task_count(self) -> int:
        return len(self._tasks)


# Global singleton
_registry: Optional[TaskRegistry] = None


def get_registry() -> TaskRegistry:
    """Get the global task registry."""
    global _registry
    if _registry is None:
        _registry = TaskRegistry()
    return _registry


def discover_tasks(package_path: str = "uhb.benchmark.tasks") -> TaskRegistry:
    """Auto-discover TaskBase subclasses in the tasks package.

    This walks the package directory and imports all modules,
    collecting any TaskBase subclass it finds.
    """
    registry = get_registry()

    try:
        package = importlib.import_module(package_path)
    except ImportError:
        return registry

    package_dir = Path(package.__file__).parent if package.__file__ else None
    if package_dir is None:
        return registry

    for _, module_name, is_pkg in pkgutil.iter_modules([str(package_dir)]):
        full_name = f"{package_path}.{module_name}"
        try:
            mod = importlib.import_module(full_name)
            # Scan for TaskBase subclasses
            for attr_name in dir(mod):
                attr = getattr(mod, attr_name)
                if (isinstance(attr, type)
                        and issubclass(attr, TaskBase)
                        and attr is not TaskBase):
                    registry.register(attr)
        except ImportError as e:
            import logging
            logging.getLogger("uhb").warning(f"Could not import task module {full_name}: {e}")

    return registry
