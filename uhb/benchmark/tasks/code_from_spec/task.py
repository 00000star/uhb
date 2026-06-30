"""Code from specification task — measures coding ability.

The model receives a spec and must write a function that passes tests.
"""

import hashlib
from typing import Any

from ..base import TaskBase, TaskSpec, TaskContext, TaskResult, Message


SPEC_TEMPLATES = [
    {
        "name": "fibonacci",
        "prompt": "Write a Python function `fibonacci(n: int) -> int` that returns the nth Fibonacci number (0-indexed, F(0)=0, F(1)=1). Must handle n up to 1000 efficiently.",
        "test": """
import pytest
def test_fib_small():
    from solution import fibonacci
    assert fibonacci(0) == 0
    assert fibonacci(1) == 1
    assert fibonacci(10) == 55
    assert fibonacci(20) == 6765

def test_fib_large():
    from solution import fibonacci
    assert fibonacci(50) == 12586269025
    assert fibonacci(100) == 354224848179261915075

def test_fib_type():
    from solution import fibonacci
    assert isinstance(fibonacci(5), int)
""",
        "key_assertions": ["fibonacci(10) == 55", "fibonacci(0) == 0"],
    },
    {
        "name": "group_anagrams",
        "prompt": "Write a Python function `group_anagrams(words: list[str]) -> list[list[str]]` that groups anagrams together. Each group should be sorted alphabetically. Groups can be in any order.",
        "test": """
import pytest
def test_basic():
    from solution import group_anagrams
    result = group_anagrams(["eat", "tea", "tan", "ate", "nat", "bat"])
    expected = [["ate", "eat", "tea"], ["bat"], ["nat", "tan"]]
    assert sorted([sorted(g) for g in result]) == sorted([sorted(g) for g in expected])

def test_empty():
    from solution import group_anagrams
    assert group_anagrams([]) == []
    assert group_anagrams([""]) == [[""]]
""",
        "key_assertions": ["sorted anagram groups"],
    },
    {
        "name": "binary_search",
        "prompt": "Write a Python function `binary_search(arr: list[int], target: int) -> int` that returns the index of target in a sorted array, or -1 if not found. Must be O(log n).",
        "test": """
import pytest
def test_found():
    from solution import binary_search
    assert binary_search([1, 3, 5, 7, 9], 5) == 2
    assert binary_search([1, 3, 5, 7, 9], 1) == 0
    assert binary_search([1, 3, 5, 7, 9], 9) == 4

def test_not_found():
    from solution import binary_search
    assert binary_search([1, 3, 5, 7, 9], 4) == -1
    assert binary_search([], 1) == -1
""",
        "key_assertions": ["binary_search returns correct index"],
    },
    {
        "name": "lru_cache",
        "prompt": "Write a Python class `LRUCache` with `get(key)` and `put(key, value)` methods, with a fixed capacity. When full, evict the least recently used item.",
        "test": """
import pytest
def test_basic():
    from solution import LRUCache
    cache = LRUCache(2)
    cache.put(1, 1)
    cache.put(2, 2)
    assert cache.get(1) == 1
    cache.put(3, 3)
    assert cache.get(2) == -1
    cache.put(4, 4)
    assert cache.get(1) == -1
    assert cache.get(3) == 3
    assert cache.get(4) == 4
""",
        "key_assertions": ["LRU eviction works correctly"],
    },
]


class CodeFromSpecTask(TaskBase):
    spec = TaskSpec(
        task_id="code_from_spec",
        name="Code from Specification",
        description="Write code given a natural language specification",
        dimension="coding",
        difficulty="medium",
    )

    def generate(self, seed: int = 0) -> TaskContext:
        template = SPEC_TEMPLATES[seed % len(SPEC_TEMPLATES)]
        return TaskContext(
            system_prompt="You are a skilled Python programmer. Write clean, correct, efficient code. Return ONLY the solution code in a Python code block.",
            problem_statement=template["prompt"],
            test_code=template["test"],
            tools_enabled=[],
        )

    def score(self, context: TaskContext, model_output: str,
              conversation: list[Message]) -> TaskResult:
        import subprocess
        import tempfile
        import re

        # Extract code block
        code_match = re.search(r'```(?:python)?\s*\n(.*?)\n```', model_output, re.DOTALL)
        code = code_match.group(1) if code_match else model_output

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', prefix='solution_', delete=False) as f:
            f.write(code)
            solution_path = f.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', prefix='test_', delete=False) as f:
            f.write(context.test_code.replace('from solution import', f'from {__import__("pathlib").Path(solution_path).stem} import'))
            test_path = f.name

        try:
            result = subprocess.run(
                ['pytest', test_path, '-q', '--tb=short'],
                capture_output=True, text=True, timeout=30,
                cwd=str(__import__('pathlib').Path(solution_path).parent)
            )
            passed = result.returncode == 0
            score = 1.0 if passed else max(0.0, self._parse_pass_rate(result.stdout))
        except Exception:
            passed = False
            score = 0.0
        finally:
            import os
            os.unlink(solution_path)
            os.unlink(test_path)
            # Clean up pycache
            pycache = __import__('pathlib').Path(solution_path).parent / '__pycache__'
            if pycache.exists():
                import shutil
                shutil.rmtree(pycache)

        return TaskResult(
            task_id=self.spec.task_id,
            task_name=self.spec.name,
            dimension=self.spec.dimension,
            score=score,
            passed=score >= self.passing_threshold(),
            details={"test_output": getattr(result, 'stdout', '')[:500]},
            model_output=model_output,
        )

    @staticmethod
    def _parse_pass_rate(stdout: str) -> float:
        """Parse pytest output for pass/fail counts."""
        import re
        match = re.search(r'(\d+) passed', stdout)
        passed = int(match.group(1)) if match else 0
        match = re.search(r'(\d+) failed', stdout)
        failed = int(match.group(1)) if match else 1  # assume at least 1 if failed
        total = passed + failed
        return passed / total if total > 0 else 0.0
