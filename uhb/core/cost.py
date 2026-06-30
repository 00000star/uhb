"""Cost intelligence — track and optimize accuracy × cost × latency × energy."""

import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TokenUsage:
    """Token consumption for a single LLM call."""
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def __add__(self, other: "TokenUsage") -> "TokenUsage":
        return TokenUsage(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            cache_read_tokens=self.cache_read_tokens + other.cache_read_tokens,
            cache_write_tokens=self.cache_write_tokens + other.cache_write_tokens,
        )


@dataclass
class CostSnapshot:
    """Cost and performance snapshot for a single operation."""
    operation: str                     # "send_message", "run_task", "benchmark_suite"
    model_id: str
    token_usage: TokenUsage = field(default_factory=TokenUsage)
    latency_ms: float = 0.0            # wall-clock time
    cost_usd: float = 0.0              # computed cost
    retry_count: int = 0
    success: bool = True
    error_message: Optional[str] = None

    # Energy estimate in watt-hours (rough: 0.0003 kWh per 1k tokens for inference)
    @property
    def energy_wh(self) -> float:
        return self.token_usage.total_tokens / 1000 * 0.0003


@dataclass
class BenchmarkCost:
    """Aggregated cost for a full benchmark run."""

    model_id: str
    task_count: int = 0
    tasks_passed: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    total_latency_ms: float = 0.0
    total_energy_wh: float = 0.0
    snapshots: list = field(default_factory=list)

    @property
    def accuracy(self) -> float:
        """Overall accuracy (tasks passed / total)."""
        return self.tasks_passed / self.task_count if self.task_count > 0 else 0.0

    @property
    def avg_latency_ms(self) -> float:
        return self.total_latency_ms / self.task_count if self.task_count > 0 else 0.0

    def add_snapshot(self, snapshot: CostSnapshot) -> None:
        self.snapshots.append(snapshot)
        self.total_tokens += snapshot.token_usage.total_tokens
        self.total_cost_usd += snapshot.cost_usd
        self.total_latency_ms += snapshot.latency_ms
        self.total_energy_wh += snapshot.energy_wh
        self.task_count += 1
        if snapshot.success:
            self.tasks_passed += 1

    def to_dict(self) -> dict:
        return {
            "model_id": self.model_id,
            "task_count": self.task_count,
            "tasks_passed": self.tasks_passed,
            "accuracy": round(self.accuracy, 4),
            "total_tokens": self.total_tokens,
            "total_cost_usd": round(self.total_cost_usd, 6),
            "total_latency_ms": round(self.total_latency_ms, 1),
            "avg_latency_ms": round(self.avg_latency_ms, 1),
            "total_energy_wh": round(self.total_energy_wh, 6),
        }

    def performance_frontier_tuple(self) -> tuple:
        """Return (accuracy, cost_usd, avg_latency_ms) for frontier plotting."""
        return (self.accuracy, self.total_cost_usd, self.avg_latency_ms)


class CostTracker:
    """Tracks cost across a session — used as context manager or standalone."""

    def __init__(self, model_id: str, input_cost_per_1k: float = 0.0, output_cost_per_1k: float = 0.0):
        self.model_id = model_id
        self.input_cost_per_1k = input_cost_per_1k
        self.output_cost_per_1k = output_cost_per_1k
        self.benchmark_cost = BenchmarkCost(model_id=model_id)

    def _compute_cost(self, usage: TokenUsage) -> float:
        return (
            usage.input_tokens / 1000 * self.input_cost_per_1k
            + usage.output_tokens / 1000 * self.output_cost_per_1k
        )

    def record(self, operation: str, usage: TokenUsage, latency_ms: float,
               retries: int = 0, success: bool = True, error: Optional[str] = None) -> CostSnapshot:
        cost = self._compute_cost(usage)
        snapshot = CostSnapshot(
            operation=operation,
            model_id=self.model_id,
            token_usage=usage,
            latency_ms=latency_ms,
            cost_usd=cost,
            retry_count=retries,
            success=success,
            error_message=error,
        )
        self.benchmark_cost.add_snapshot(snapshot)
        return snapshot

    @property
    def total_cost(self) -> float:
        return self.benchmark_cost.total_cost_usd

    def summary(self) -> dict:
        return self.benchmark_cost.to_dict()


class Timer:
    """Simple context manager for latency measurement."""

    def __init__(self):
        self.start_time: float = 0.0
        self.end_time: float = 0.0

    def __enter__(self) -> "Timer":
        self.start_time = time.monotonic()
        return self

    def __exit__(self, *args) -> None:
        self.end_time = time.monotonic()

    @property
    def elapsed_ms(self) -> float:
        return (self.end_time - self.start_time) * 1000
