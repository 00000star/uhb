"""Results cache to avoid re-running identical model+task+harness combos."""

import hashlib
import json
import os
from pathlib import Path
from typing import Optional, Any
from datetime import datetime, timedelta, timezone

import diskcache

from .config import get_config


class ResultCache:
    """Persistent cache for benchmark results using diskcache."""

    def __init__(self, cache_dir: Optional[Path] = None):
        cfg = get_config()
        directory = cache_dir or cfg.cache_dir
        directory.mkdir(parents=True, exist_ok=True)
        self._cache = diskcache.Cache(str(directory))
        self._ttl_seconds = cfg.cache_ttl_hours * 3600

    @staticmethod
    def _make_key(model_id: str, task_id: str, harness_hash: str,
                  environment: str = "default") -> str:
        """Generate a deterministic cache key."""
        raw = f"{model_id}|{task_id}|{harness_hash}|{environment}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    def get(self, model_id: str, task_id: str, harness_hash: str,
            environment: str = "default") -> Optional[Any]:
        """Retrieve a cached result if it exists and is not expired."""
        if not get_config().cache_enabled:
            return None
        key = self._make_key(model_id, task_id, harness_hash, environment)
        return self._cache.get(key)

    def set(self, model_id: str, task_id: str, harness_hash: str,
            result: Any, environment: str = "default") -> None:
        """Store a result in the cache."""
        if not get_config().cache_enabled:
            return
        key = self._make_key(model_id, task_id, harness_hash, environment)
        self._cache.set(key, result, expire=self._ttl_seconds)

    def invalidate(self, model_id: Optional[str] = None) -> int:
        """Invalidate cache entries. If model_id is None, clear all."""
        if model_id is None:
            count = len(self._cache)
            self._cache.clear()
            return count
        # Selective invalidation: iterate and delete matching
        deleted = 0
        for key in list(self._cache.iterkeys()):
            self._cache.delete(key)
            deleted += 1
        return deleted

    def stats(self) -> dict:
        """Return cache statistics."""
        return {
            "size": len(self._cache),
            "volume_bytes": self._cache.volume(),
            "directory": self._cache.directory,
        }

    def close(self) -> None:
        self._cache.close()


def hash_harness(harness_config: dict) -> str:
    """Produce a stable hash for a harness configuration."""
    canonical = json.dumps(harness_config, sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]
