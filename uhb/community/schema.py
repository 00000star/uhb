"""Data schema for community-contributed benchmark runs."""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import json


@dataclass
class CommunityRun:
    """A single benchmark run contributed to the community dataset."""
    model: str                          # e.g., "anthropic/claude-sonnet-4-6"
    harness_genes: list[str] = field(default_factory=list)
    environment: str = "terminal"
    repo_hash: str = ""                 # SHA256 of repo URL (anonymized)
    task: str = ""                      # task description
    success: bool = False
    score: float = 0.0
    cost_usd: float = 0.0
    tokens: int = 0
    latency_seconds: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    submitter: str = "anonymous"
    tags: list[str] = field(default_factory=list)

    @staticmethod
    def anonymize_repo_url(url: str) -> str:
        """Hash a repo URL for anonymization."""
        return hashlib.sha256(url.encode()).hexdigest()[:16]

    def to_dict(self) -> dict:
        return {
            "model": self.model,
            "harness_genes": self.harness_genes,
            "environment": self.environment,
            "repo_hash": self.repo_hash,
            "task": self.task,
            "success": self.success,
            "score": self.score,
            "cost_usd": self.cost_usd,
            "tokens": self.tokens,
            "latency_seconds": self.latency_seconds,
            "timestamp": self.timestamp,
            "submitter": self.submitter,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "CommunityRun":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


class CommunityDataset:
    """Manages a local collection of community benchmark runs."""

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or Path("/root/uhb/data/community")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._runs: list[CommunityRun] = []

    def add(self, run: CommunityRun) -> None:
        """Add a run to the dataset."""
        self._runs.append(run)

    def submit(self, run: CommunityRun) -> str:
        """Submit a run — saves locally. Returns the run ID."""
        run_id = hashlib.sha256(
            f"{run.model}|{run.task}|{run.timestamp}".encode()
        ).hexdigest()[:12]
        self.add(run)
        self._save_run(run_id, run)
        return run_id

    def _save_run(self, run_id: str, run: CommunityRun) -> None:
        path = self.data_dir / f"{run_id}.json"
        path.write_text(json.dumps(run.to_dict(), indent=2))

    def load_all(self) -> list[CommunityRun]:
        """Load all saved runs."""
        runs = []
        for f in sorted(self.data_dir.glob("*.json")):
            try:
                data = json.loads(f.read_text())
                runs.append(CommunityRun.from_dict(data))
            except Exception:
                pass
        self._runs = runs
        return runs

    def query(self, model: Optional[str] = None,
              environment: Optional[str] = None,
              success_only: bool = False,
              min_score: float = 0.0,
              limit: int = 100) -> list[CommunityRun]:
        """Query the community dataset."""
        self.load_all()
        results = self._runs

        if model:
            results = [r for r in results if r.model == model]
        if environment:
            results = [r for r in results if r.environment == environment]
        if success_only:
            results = [r for r in results if r.success]
        if min_score > 0:
            results = [r for r in results if r.score >= min_score]

        return results[:limit]

    def stats(self) -> dict:
        """Dataset statistics."""
        runs = self.load_all()
        models = set(r.model for r in runs)
        environments = set(r.environment for r in runs)
        total_cost = sum(r.cost_usd for r in runs)

        return {
            "total_runs": len(runs),
            "unique_models": len(models),
            "unique_environments": len(environments),
            "total_cost_usd": round(total_cost, 4),
            "success_rate": round(sum(1 for r in runs if r.success) / max(1, len(runs)), 4),
        }
