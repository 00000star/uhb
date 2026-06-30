"""Global configuration for UHB — env vars, model registry, defaults."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any


@dataclass
class ModelSpec:
    """Specification for a model entry in the registry."""
    provider: str          # "anthropic", "openai", "openrouter"
    model_id: str          # e.g. "claude-sonnet-4-6"
    api_key_env: str       # environment variable for the API key
    base_url: Optional[str] = None
    default_max_tokens: int = 4096
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0


# Known model registry — extend by setting UHB_MODEL_REGISTRY env var
MODEL_REGISTRY: Dict[str, ModelSpec] = {
    "anthropic/claude-sonnet-4-6": ModelSpec(
        provider="anthropic",
        model_id="claude-sonnet-4-6-20250514",
        api_key_env="ANTHROPIC_API_KEY",
        cost_per_1k_input=0.003,
        cost_per_1k_output=0.015,
    ),
    "anthropic/claude-opus-4-8": ModelSpec(
        provider="anthropic",
        model_id="claude-opus-4-8-20250514",
        api_key_env="ANTHROPIC_API_KEY",
        cost_per_1k_input=0.015,
        cost_per_1k_output=0.075,
    ),
    "anthropic/claude-haiku-4-5": ModelSpec(
        provider="anthropic",
        model_id="claude-haiku-4-5-20251001",
        api_key_env="ANTHROPIC_API_KEY",
        cost_per_1k_input=0.001,
        cost_per_1k_output=0.005,
    ),
    "openai/gpt-4o": ModelSpec(
        provider="openai",
        model_id="gpt-4o",
        api_key_env="OPENAI_API_KEY",
        cost_per_1k_input=0.005,
        cost_per_1k_output=0.015,
    ),
    "openai/gpt-4o-mini": ModelSpec(
        provider="openai",
        model_id="gpt-4o-mini",
        api_key_env="OPENAI_API_KEY",
        cost_per_1k_input=0.00015,
        cost_per_1k_output=0.0006,
    ),
    # DeepSeek (OpenAI-compatible API)
    "deepseek/chat": ModelSpec(
        provider="openai", model_id="deepseek-chat",
        api_key_env="DEEPSEEK_API_KEY", base_url="https://api.deepseek.com/v1",
        cost_per_1k_input=0.00027, cost_per_1k_output=0.00110,
    ),
    "deepseek/reasoner": ModelSpec(
        provider="openai", model_id="deepseek-reasoner",
        api_key_env="DEEPSEEK_API_KEY", base_url="https://api.deepseek.com/v1",
        cost_per_1k_input=0.00055, cost_per_1k_output=0.00219,
    ),
    # Mock models for testing without API keys
    "mock/strong": ModelSpec(
        provider="mock", model_id="mock-strong", api_key_env="MOCK_API_KEY",
    ),
    "mock/medium": ModelSpec(
        provider="mock", model_id="mock-medium", api_key_env="MOCK_API_KEY",
    ),
    "mock/weak": ModelSpec(
        provider="mock", model_id="mock-weak", api_key_env="MOCK_API_KEY",
    ),
    "mock/flaky": ModelSpec(
        provider="mock", model_id="mock-flaky", api_key_env="MOCK_API_KEY",
    ),
}


@dataclass
class UHBConfig:
    """Global UHB configuration."""

    # API keys (loaded from env)
    anthropic_api_key: Optional[str] = field(
        default_factory=lambda: os.environ.get("ANTHROPIC_API_KEY")
    )
    openai_api_key: Optional[str] = field(
        default_factory=lambda: os.environ.get("OPENAI_API_KEY")
    )
    openrouter_api_key: Optional[str] = field(
        default_factory=lambda: os.environ.get("OPENROUTER_API_KEY")
    )

    # Directories
    data_dir: Path = Path(os.environ.get("UHB_DATA_DIR", "/root/uhb/data"))
    cache_dir: Path = Path(os.environ.get("UHB_CACHE_DIR", "/root/uhb/data/cache"))
    results_dir: Path = Path(os.environ.get("UHB_RESULTS_DIR", "/root/uhb/data/results"))

    # Limits
    max_tokens_per_task: int = 100_000
    max_cost_per_benchmark: float = 50.0
    max_concurrent_requests: int = 4
    request_timeout_seconds: int = 300

    # Behavior
    cache_enabled: bool = True
    cache_ttl_hours: int = 24
    log_json: bool = False
    log_level: str = "INFO"

    def __post_init__(self):
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def model_spec(self, model_key: str) -> Optional[ModelSpec]:
        """Look up a model in the registry."""
        return MODEL_REGISTRY.get(model_key)

    def register_model(self, key: str, spec: ModelSpec) -> None:
        """Register a new model in the runtime registry."""
        MODEL_REGISTRY[key] = spec


# Global singleton
_config: Optional[UHBConfig] = None


def get_config() -> UHBConfig:
    """Get the global UHB configuration singleton."""
    global _config
    if _config is None:
        _config = UHBConfig()
    return _config


def reset_config() -> None:
    """Reset the global config (useful for testing)."""
    global _config
    _config = None
