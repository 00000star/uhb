"""Debug broken code task — measures debugging/self-repair ability.

The model receives broken code with bugs and must fix them so tests pass.
"""

import hashlib
import subprocess
import tempfile
import re
import os
import shutil
from pathlib import Path

from ..base import TaskBase, TaskSpec, TaskContext, TaskResult, Message


BUGGY_PROGRAMS = [
    {
        "name": "off_by_one",
        "prompt": "The following Python function has a bug. Find and fix it.\n\n```python\ndef sum_to_n(n: int) -> int:\n    '''Return sum of integers from 1 to n inclusive.'''\n    total = 0\n    for i in range(n):  # BUG: should be range(1, n+1) or similar\n        total += i\n    return total\n```\n\nFix the bug so the function returns the correct sum. Return the corrected code in a Python code block.",
        "buggy_code": "def sum_to_n(n: int) -> int:\n    total = 0\n    for i in range(n):\n        total += i\n    return total\n",
        "test": """
import pytest
def test_sum_small():
    from solution import sum_to_n
    assert sum_to_n(1) == 1
    assert sum_to_n(5) == 15
    assert sum_to_n(10) == 55
    assert sum_to_n(0) == 0
""",
    },
    {
        "name": "division_by_zero",
        "prompt": "The following function crashes on certain inputs. Find and fix the bug.\n\n```python\ndef safe_divide(a: float, b: float) -> float:\n    return a / b\n```\n\nFix it to handle division by zero gracefully (return None in that case). Return the corrected code.",
        "buggy_code": "def safe_divide(a: float, b: float) -> float:\n    return a / b\n",
        "test": """
import pytest
def test_normal_division():
    from solution import safe_divide
    assert safe_divide(10.0, 2.0) == 5.0
    assert safe_divide(7.0, 2.0) == 3.5
    assert safe_divide(0.0, 5.0) == 0.0

def test_zero_division():
    from solution import safe_divide
    assert safe_divide(5.0, 0.0) is None
    assert safe_divide(0.0, 0.0) is None
""",
    },
    {
        "name": "mutable_default",
        "prompt": "This function has a subtle Python bug. Find and fix it.\n\n```python\ndef append_to_list(item, target=None):\n    if target is None:\n        target = []\n    target.append(item)\n    return target\n```\n\nWait, that looks correct — the bug is actually different. Check carefully: the function seems to work but sometimes returns unexpected results when called multiple times. Find the REAL bug and explain it, then provide the fix.",
        # Trick: this one actually has no bug in the code shown, testing if model hallucinates a bug
        "buggy_code": "def append_to_list(item, target=None):\n    if target is None:\n        target = []\n    target.append(item)\n    return target\n",
        "test": """
import pytest
def test_append():
    from solution import append_to_list
    assert append_to_list(1) == [1]
    assert append_to_list(2, [1]) == [1, 2]
    assert append_to_list(3) == [3]  # fresh list each time
""",
        "expect_correct": True,  # code is actually correct, model should recognize this
    },
]


class DebugBrokenTask(TaskBase):
    spec = TaskSpec(
        task_id="debug_broken",
        name="Debug Broken Code",
        description="Find and fix bugs in broken code",
        dimension="self_repair",
        difficulty="easy",
    )

    def generate(self, seed: int = 0) -> TaskContext:
        template = BUGGY_PROGRAMS[seed % len(BUGGY_PROGRAMS)]
        return TaskContext(
            system_prompt="You are a debugging expert. Analyze the code, identify the bug, explain it clearly, and provide the corrected code in a Python code block.",
            problem_statement=template["prompt"],
            test_code=template["test"],
            tools_enabled=[],
        )

    def score(self, context: TaskContext, model_output: str,
              conversation: list[Message]) -> TaskResult:
        code_match = re.search(r'```(?:python)?\s*\n(.*?)\n```', model_output, re.DOTALL)
        code = code_match.group(1) if code_match else model_output

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', prefix='solution_', delete=False) as f:
            f.write(code)
            solution_path = f.name

        test_file = Path(solution_path).parent / f"test_{Path(solution_path).stem}.py"
        test_file.write_text(context.test_code.replace(
            'from solution import',
            f'from {Path(solution_path).stem} import'
        ))

        try:
            result = subprocess.run(
                ['pytest', str(test_file), '-q', '--tb=short'],
                capture_output=True, text=True, timeout=30,
                cwd=str(Path(solution_path).parent)
            )
            passed = result.returncode == 0
            score = 1.0 if passed else max(0.0, self._parse_pass_rate(result.stdout))
        except Exception:
            passed = False
            score = 0.0
        finally:
            os.unlink(solution_path)
            try:
                test_file.unlink()
            except FileNotFoundError:
                pass
            pycache = Path(solution_path).parent / '__pycache__'
            if pycache.exists():
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
        match = re.search(r'(\d+) passed', stdout)
        passed = int(match.group(1)) if match else 0
        match = re.search(r'(\d+) failed', stdout)
        failed = int(match.group(1)) if match else 1
        return passed / (passed + failed) if (passed + failed) > 0 else 0.0
