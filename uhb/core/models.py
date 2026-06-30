"""LLM abstraction layer — unified interface for all providers via litellm."""

import abc
import os
import time
import json
from dataclasses import dataclass, field
from typing import Optional, Any, Iterator, Literal

from .config import get_config, ModelSpec
from .cost import TokenUsage
from .logging import get_logger

log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class Message:
    """A single message in a conversation."""
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    tool_call_id: Optional[str] = None
    name: Optional[str] = None


@dataclass
class ToolDefinition:
    """Definition of a tool the model can call."""
    name: str
    description: str
    parameters: dict  # JSON Schema for the tool's arguments


@dataclass
class ToolCall:
    """A tool call made by the model."""
    id: str
    name: str
    arguments: dict


@dataclass
class LLMResponse:
    """Unified response from any LLM backend."""
    content: str
    tool_calls: list = field(default_factory=list)
    usage: Optional[TokenUsage] = None
    stop_reason: Optional[str] = None
    model: str = ""
    latency_ms: float = 0.0


@dataclass
class LLMStreamChunk:
    """A chunk from streaming LLM output."""
    content: str = ""
    tool_call_delta: Optional[dict] = None
    usage: Optional[TokenUsage] = None


# ---------------------------------------------------------------------------
# Base class
# ---------------------------------------------------------------------------

class BaseLLMBackend(abc.ABC):
    """Abstract base for all LLM backends."""

    def __init__(self, model_spec: ModelSpec):
        self.spec = model_spec
        self._api_key: Optional[str] = None

    @property
    def api_key(self) -> Optional[str]:
        if self._api_key is None:
            self._api_key = os.environ.get(self.spec.api_key_env)
        return self._api_key

    @abc.abstractmethod
    def send(self, messages: list[Message], tools: Optional[list[ToolDefinition]] = None,
             max_tokens: Optional[int] = None, temperature: float = 0.0,
             system: Optional[str] = None) -> LLMResponse:
        """Send a request and get a complete response."""
        ...

    @abc.abstractmethod
    def stream(self, messages: list[Message], tools: Optional[list[ToolDefinition]] = None,
               max_tokens: Optional[int] = None, temperature: float = 0.0,
               system: Optional[str] = None) -> Iterator[LLMStreamChunk]:
        """Send a request and stream response chunks."""
        ...

    def close(self) -> None:
        """Release any backend resources."""
        pass


# ---------------------------------------------------------------------------
# LiteLLM backend
# ---------------------------------------------------------------------------

class LiteLLMBackend(BaseLLMBackend):
    """Unified backend using litellm for all models."""

    def _convert_messages(self, messages: list[Message]) -> list[dict]:
        converted = []
        for msg in messages:
            entry = {"role": msg.role, "content": msg.content}
            if msg.tool_call_id:
                entry["tool_call_id"] = msg.tool_call_id
            if msg.name:
                entry["name"] = msg.name
            converted.append(entry)
        return converted

    def _convert_tools(self, tools: list[ToolDefinition]) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in tools
        ]

    def _parse_tool_calls(self, message_obj) -> list[ToolCall]:
        if not hasattr(message_obj, 'tool_calls') or not message_obj.tool_calls:
            return []
        calls = []
        for tc in message_obj.tool_calls:
            try:
                args = json.loads(tc.function.arguments)
            except (json.JSONDecodeError, AttributeError, TypeError):
                args = {}
            calls.append(ToolCall(
                id=getattr(tc, 'id', ''),
                name=getattr(tc.function, 'name', ''),
                arguments=args,
            ))
        return calls

    def send(self, messages: list[Message], tools: Optional[list[ToolDefinition]] = None,
             max_tokens: Optional[int] = None, temperature: float = 0.0,
             system: Optional[str] = None) -> LLMResponse:
        import litellm

        if not self.api_key:
            raise ValueError(f"API key not found for {self.spec.model_id}. "
                           f"Set {self.spec.api_key_env} environment variable.")

        max_tok = max_tokens or self.spec.default_max_tokens

        api_messages = self._convert_messages(messages)
        if system:
            api_messages.insert(0, {"role": "system", "content": system})

        model_name = f"{self.spec.provider}/{self.spec.model_id}" if self.spec.provider not in ("openai",) else self.spec.model_id

        kwargs = {
            "model": model_name,
            "messages": api_messages,
            "max_tokens": max_tok,
            "temperature": temperature,
            "api_key": self.api_key,
        }
        if self.spec.base_url:
            kwargs["api_base"] = self.spec.base_url
        if tools:
            kwargs["tools"] = self._convert_tools(tools)

        start = time.monotonic()
        try:
            response = litellm.completion(**kwargs)
        except Exception as e:
            log.error(f"LiteLLM API error for {self.spec.model_id}: {e}")
            raise

        latency = (time.monotonic() - start) * 1000
        choice = response.choices[0] if getattr(response, 'choices', None) else None
        content = getattr(getattr(choice, 'message', None), 'content', "") or ""

        usage = TokenUsage(
            input_tokens=getattr(response.usage, 'prompt_tokens', 0) if getattr(response, 'usage', None) else 0,
            output_tokens=getattr(response.usage, 'completion_tokens', 0) if getattr(response, 'usage', None) else 0,
        )

        return LLMResponse(
            content=content,
            tool_calls=self._parse_tool_calls(getattr(choice, 'message', None) if choice else None),
            usage=usage,
            stop_reason=getattr(choice, 'finish_reason', None) if choice else None,
            model=getattr(response, 'model', self.spec.model_id),
            latency_ms=latency,
        )

    def stream(self, messages: list[Message], tools: Optional[list[ToolDefinition]] = None,
               max_tokens: Optional[int] = None, temperature: float = 0.0,
               system: Optional[str] = None) -> Iterator[LLMStreamChunk]:
        import litellm

        if not self.api_key:
            raise ValueError(f"API key not found for {self.spec.model_id}.")

        max_tok = max_tokens or self.spec.default_max_tokens
        api_messages = self._convert_messages(messages)
        if system:
            api_messages.insert(0, {"role": "system", "content": system})

        model_name = f"{self.spec.provider}/{self.spec.model_id}" if self.spec.provider not in ("openai",) else self.spec.model_id

        kwargs = {
            "model": model_name,
            "messages": api_messages,
            "max_tokens": max_tok,
            "temperature": temperature,
            "stream": True,
            "api_key": self.api_key,
        }
        if self.spec.base_url:
            kwargs["api_base"] = self.spec.base_url
        if tools:
            kwargs["tools"] = self._convert_tools(tools)

        try:
            stream = litellm.completion(**kwargs)
            for event in stream:
                chunk = LLMStreamChunk()
                if getattr(event, 'choices', None) and getattr(event.choices[0], 'delta', None):
                    delta = event.choices[0].delta
                    if getattr(delta, 'content', None):
                        chunk.content = delta.content
                    if getattr(delta, 'tool_calls', None):
                        chunk.tool_call_delta = {
                            "index": delta.tool_calls[0].index if delta.tool_calls else 0,
                            "id": getattr(delta.tool_calls[0], 'id', None),
                            "function": {
                                "name": delta.tool_calls[0].function.name if getattr(delta.tool_calls[0], 'function', None) else None,
                                "arguments": delta.tool_calls[0].function.arguments if getattr(delta.tool_calls[0], 'function', None) else None,
                            },
                        }
                yield chunk
        except Exception as e:
            log.error(f"LiteLLM streaming error: {e}")
            raise


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def create_backend(model_key: str) -> BaseLLMBackend:
    """Create a backend for the given model key.

    Args:
        model_key: Key in MODEL_REGISTRY.

    Returns:
        A configured BaseLLMBackend instance.

    Raises:
        ValueError: If the model key is not found.
    """
    cfg = get_config()
    spec = cfg.model_spec(model_key)
    if spec is None:
        raise ValueError(
            f"Unknown model key: {model_key}. "
            f"Available: {list(cfg.MODEL_REGISTRY.keys())}"
        )

    provider = spec.provider.lower()
    if provider == "mock":
        from .mock import MOCK_PROFILES
        return MOCK_PROFILES.get(model_key, MOCK_PROFILES["mock/medium"])
    else:
        return LiteLLMBackend(spec)


def send_message(backend: BaseLLMBackend, content: str,
                 system: Optional[str] = None,
                 tools: Optional[list[ToolDefinition]] = None) -> LLMResponse:
    """Convenience: send a single user message and get a response."""
    messages = [Message(role="user", content=content)]
    return backend.send(messages, tools=tools, system=system)
