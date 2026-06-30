"""Memory strategies — compare different approaches to context management."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Callable


class StrategyType(Enum):
    FULL_CONTEXT = "full_context"      # Keep everything
    SUMMARIZE = "summarize"            # Summarize older messages
    SLIDING_WINDOW = "sliding_window"  # Keep only last N messages
    VECTOR_STORE = "vector_store"      # Dense retrieval from external store
    HYBRID = "hybrid"                  # Combine window + summarized history


@dataclass
class MemoryStrategy:
    """A memory management strategy with its configuration."""
    name: StrategyType
    description: str
    config: dict = field(default_factory=dict)


def summarize(messages: list, max_summary_tokens: int = 500) -> str:
    """Summarize a list of messages into a concise form.

    This is a client-side utility — the actual summarization happens
    via the model, but this defines the interface.
    """
    return "summarize"  # placeholder — model provides actual summarization


def compress(messages: list, compression_ratio: float = 0.3) -> list:
    """Compress conversation history by removing less important messages.

    Args:
        messages: List of conversation messages.
        compression_ratio: Fraction of messages to keep (0.0–1.0).

    Returns:
        Compressed message list.
    """
    if not messages:
        return []
    keep_count = max(1, int(len(messages) * compression_ratio))
    # Keep system message if present
    system_msgs = [m for m in messages if hasattr(m, 'role') and m.role == "system"]
    other_msgs = [m for m in messages if not (hasattr(m, 'role') and m.role == "system")]
    # Keep most recent messages (not oldest — recency bias)
    return system_msgs + other_msgs[-keep_count:]


def sliding_window(messages: list, window_size: int = 20) -> list:
    """Keep only the most recent N messages.

    Args:
        messages: List of conversation messages.
        window_size: Maximum number of messages to retain.

    Returns:
        Truncated message list.
    """
    if not messages:
        return []
    system_msgs = [m for m in messages if hasattr(m, 'role') and m.role == "system"]
    other_msgs = [m for m in messages if not (hasattr(m, 'role') and m.role == "system")]
    effective_window = max(1, window_size - len(system_msgs))
    return system_msgs + other_msgs[-effective_window:]


def vector_store(query: str, store: dict) -> list:
    """Retrieve relevant past context from a vector store.

    Args:
        query: The current query to match against.
        store: The vector store (placeholder interface).

    Returns:
        List of relevant past messages.
    """
    # Placeholder for actual vector store integration
    # In production, this would use embeddings + FAISS/Chroma/Pinecone
    return []


# Strategy presets with recommended configurations per model type
STRATEGY_PRESETS = {
    "default": MemoryStrategy(
        name=StrategyType.FULL_CONTEXT,
        description="Keep all context. Best for models with large context windows.",
    ),
    "cost_optimized": MemoryStrategy(
        name=StrategyType.SLIDING_WINDOW,
        description="Keep last 20 messages. Saves tokens, risks forgetting early context.",
        config={"window_size": 20},
    ),
    "balanced": MemoryStrategy(
        name=StrategyType.HYBRID,
        description="Sliding window of recent + summary of older messages.",
        config={"window_size": 15, "max_summary_tokens": 500},
    ),
    "comprehensive": MemoryStrategy(
        name=StrategyType.VECTOR_STORE,
        description="Store all context in vector DB, retrieve relevant chunks.",
        config={"top_k": 10, "embedding_model": "text-embedding-3-small"},
    ),
}
