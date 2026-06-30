"""Mock LLM backend for testing UHB without API keys.

Simulates a model with configurable capability levels.
Perfect for CI/CD, development, and trying out UHB.
"""

import time
import random
from typing import Optional, Iterator

from .models import BaseLLMBackend, Message, LLMResponse, LLMStreamChunk, ToolDefinition, TokenUsage
from .config import ModelSpec


class MockBackend(BaseLLMBackend):
    """A simulated LLM backend that returns plausible responses.

    Capabilities can be tuned to simulate different model profiles:
    - coding_skill: 0.0–1.0 (affects code quality)
    - reasoning_skill: 0.0–1.0
    - planning_skill: 0.0–1.0
    - tool_usage_skill: 0.0–1.0
    - context_retention: 0.0–1.0
    - verbosity: tokens per response
    - failure_rate: 0.0–1.0 (how often it fails)
    """

    # Pre-built code solutions for common task patterns
    CODE_TEMPLATES = {
        "fibonacci": '''
def fibonacci(n: int) -> int:
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b
''',
        "binary_search": '''
def binary_search(arr: list[int], target: int) -> int:
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1
''',
        "group_anagrams": '''
from collections import defaultdict
def group_anagrams(words: list[str]) -> list[list[str]]:
    groups = defaultdict(list)
    for w in words:
        key = ''.join(sorted(w))
        groups[key].append(w)
    return [sorted(g) for g in groups.values()]
''',
        "lru_cache": '''
from collections import OrderedDict
class LRUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = OrderedDict()
    def get(self, key: int) -> int:
        if key not in self.cache:
            return -1
        self.cache.move_to_end(key)
        return self.cache[key]
    def put(self, key: int, value: int) -> None:
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)
''',
    }

    PLAN_TEMPLATE = """# Implementation Plan

## 1. Architecture
- Use a layered architecture with clear separation of concerns
- API layer → Service layer → Data layer

## 2. Component Breakdown
- Authentication module
- Core business logic
- Data access layer
- API endpoints

## 3. Data Model
- Users table with hashed passwords
- Sessions with TTL
- Related entities with foreign keys

## 4. API Design
- RESTful endpoints
- JSON request/response format
- Proper HTTP status codes

## 5. Testing Strategy
- Unit tests for business logic
- Integration tests for API endpoints
- E2E tests for critical flows

## 6. Timeline
- Week 1: Core setup and data model
- Week 2: API endpoints
- Week 3: Testing and documentation
"""

    def __init__(self, model_spec: ModelSpec = None,
                 coding_skill: float = 0.9,
                 reasoning_skill: float = 0.85,
                 planning_skill: float = 0.8,
                 tool_usage_skill: float = 0.75,
                 context_retention: float = 0.9,
                 verbosity: int = 500,
                 failure_rate: float = 0.0,
                 seed: int = 42):
        spec = model_spec or ModelSpec(
            provider="mock",
            model_id="mock-model",
            api_key_env="MOCK_API_KEY",
        )
        super().__init__(spec)
        self.coding_skill = coding_skill
        self.reasoning_skill = reasoning_skill
        self.planning_skill = planning_skill
        self.tool_usage_skill = tool_usage_skill
        self.context_retention = context_retention
        self.verbosity = verbosity
        self.failure_rate = failure_rate
        self.rng = random.Random(seed)

    def send(self, messages: list[Message],
             tools: Optional[list[ToolDefinition]] = None,
             max_tokens: Optional[int] = None,
             temperature: float = 0.0,
             system: Optional[str] = None) -> LLMResponse:
        # Simulate latency
        time.sleep(0.05)

        # Simulate failure
        if self.rng.random() < self.failure_rate:
            raise RuntimeError("Simulated API failure")

        # Determine what kind of task this is from the messages
        user_content = ""
        for msg in reversed(messages):
            if msg.role == "user":
                user_content = msg.content.lower()
                break

        # Generate appropriate response based on task type
        if "fibonacci" in user_content:
            code = self._maybe_break_code(self.CODE_TEMPLATES["fibonacci"])
            content = f"```python\n{code}\n```"
        elif "binary_search" in user_content or "binary search" in user_content:
            code = self._maybe_break_code(self.CODE_TEMPLATES["binary_search"])
            content = f"```python\n{code}\n```"
        elif "group_anagrams" in user_content or "anagram" in user_content:
            code = self._maybe_break_code(self.CODE_TEMPLATES["group_anagrams"])
            content = f"```python\n{code}\n```"
        elif "lru" in user_content:
            code = self._maybe_break_code(self.CODE_TEMPLATES["lru_cache"])
            content = f"```python\n{code}\n```"
        elif "plan" in user_content and "feature" in user_content:
            content = self._generate_plan()
        elif "debug" in user_content or "bug" in user_content:
            content = self._generate_debug_response(user_content)
        elif "pr" in user_content or "review" in user_content:
            content = self._generate_review()
        elif "sum" in user_content and ("1 to" in user_content or "n" in user_content):
            content = "The bug is that `range(n)` starts at 0 and goes to n-1. Fix: `range(1, n+1)`.\n\n```python\ndef sum_to_n(n: int) -> int:\n    total = 0\n    for i in range(1, n + 1):\n        total += i\n    return total\n```"
        elif "divide" in user_content or "division" in user_content:
            content = "The bug is no handling for `b == 0`. Fixed:\n\n```python\ndef safe_divide(a: float, b: float) -> float:\n    if b == 0:\n        return None\n    return a / b\n```"
        elif "refactor" in user_content:
            content = "Here's the refactored code:\n\n```python\ndef get_grade(score):\n    if score >= 90:\n        return 'A'\n    elif score >= 80:\n        return 'B'\n    elif score >= 70:\n        return 'C'\n    elif score >= 60:\n        return 'D'\n    return 'F'\n```"
        elif "document" in user_content and "paragraph" in user_content:
            # Long context task — simulate recall based on context_retention
            recalled = int(3 * self.context_retention)
            facts = ["orange", "blue-elephant-42", "Thursday at 3pm", "sk-test-9a8b7c6d5e4f",
                     "10.42.7.13", "memory leaks in the image processing pipeline",
                     "23 engineers", "2am and 4am UTC on Sundays", "500", "4.2.0"]
            answers = self.rng.sample(facts, recalled)
            content = "\n".join(f"{i+1}. {a}" for i, a in enumerate(answers))
        else:
            content = self._generate_generic_response()

        # Cap verbosity
        if len(content) > self.verbosity:
            content = content[:self.verbosity]

        return LLMResponse(
            content=content,
            tool_calls=[],
            usage=TokenUsage(input_tokens=len(user_content)//4, output_tokens=len(content)//4),
            stop_reason="end_turn",
            model=self.spec.model_id,
            latency_ms=self.rng.uniform(200, 2000),
        )

    def stream(self, messages: list[Message],
               tools: Optional[list[ToolDefinition]] = None,
               max_tokens: Optional[int] = None,
               temperature: float = 0.0,
               system: Optional[str] = None) -> Iterator[LLMStreamChunk]:
        response = self.send(messages, tools, max_tokens, temperature, system)
        # Simulate streaming by chunking the response
        words = response.content.split()
        for word in words:
            yield LLMStreamChunk(content=word + " ")

    def _maybe_break_code(self, code: str) -> str:
        """Introduce bugs based on (1 - coding_skill)."""
        if self.rng.random() > self.coding_skill:
            # Introduce a simple bug
            lines = code.split('\n')
            if len(lines) > 3:
                bug_line = self.rng.randint(1, len(lines)-2)
                if 'return' in lines[bug_line]:
                    lines[bug_line] = lines[bug_line].replace('return', 'return  # BUG: wrong return')
            return '\n'.join(lines)
        return code

    def _generate_plan(self) -> str:
        """Generate a plan, quality depends on planning_skill."""
        if self.planning_skill > 0.8:
            return self.PLAN_TEMPLATE
        elif self.planning_skill > 0.5:
            return self.PLAN_TEMPLATE[:len(self.PLAN_TEMPLATE)//2]
        else:
            return "Just code it. We'll figure it out as we go."

    def _generate_debug_response(self, prompt: str) -> str:
        if self.reasoning_skill > 0.7:
            return "Bug found: the loop initializes incorrectly. The variable should start at 1, not 0.\n\n```python\n# Fixed version\nfor i in range(1, n+1):\n    total += i\n```"
        else:
            return "The code looks fine to me. Maybe try restarting?"

    def _generate_review(self) -> str:
        if self.reasoning_skill > 0.7:
            return "**Critical:** SQL injection vulnerability on line 2. Use parameterized queries.\n**High:** Hardcoded secret key on line 8. Move to environment variable.\n**Medium:** Password validation weakened from 8 chars to 6 — security regression."
        else:
            return "LGTM 👍"

    def _generate_generic_response(self) -> str:
        return "Based on the requirements, here is the implementation.\n\nThe solution addresses the core requirements and includes appropriate error handling."


# Pre-configured mock profiles
MOCK_PROFILES = {
    "mock/strong": MockBackend(
        coding_skill=0.95, reasoning_skill=0.92, planning_skill=0.90,
        tool_usage_skill=0.85, context_retention=0.93, verbosity=800,
    ),
    "mock/medium": MockBackend(
        coding_skill=0.75, reasoning_skill=0.70, planning_skill=0.65,
        tool_usage_skill=0.70, context_retention=0.75, verbosity=500,
    ),
    "mock/weak": MockBackend(
        coding_skill=0.50, reasoning_skill=0.45, planning_skill=0.40,
        tool_usage_skill=0.55, context_retention=0.50, verbosity=300,
    ),
    "mock/flaky": MockBackend(
        coding_skill=0.85, reasoning_skill=0.80, planning_skill=0.75,
        failure_rate=0.2, verbosity=600,
    ),
}
