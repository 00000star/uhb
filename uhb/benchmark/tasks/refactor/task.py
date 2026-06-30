"""Refactor task — measures ability to improve code without breaking it.

The model receives working but poorly structured code and must improve it
while preserving all functionality.
"""

import subprocess
import tempfile
import re
import os
import shutil
from pathlib import Path

from ..base import TaskBase, TaskSpec, TaskContext, TaskResult, Message


REFACTOR_TASKS = [
    {
        "name": "simplify_conditionals",
        "prompt": "Refactor the following Python function to be cleaner and more Pythonic. Preserve exact behavior.\n\n```python\ndef get_grade(score):\n    if score >= 90:\n        return 'A'\n    else:\n        if score >= 80:\n            return 'B'\n        else:\n            if score >= 70:\n                return 'C'\n            else:\n                if score >= 60:\n                    return 'D'\n                else:\n                    return 'F'\n```\n\nReturn the refactored code in a Python code block.",
        "original_code": "def get_grade(score):\n    if score >= 90:\n        return 'A'\n    else:\n        if score >= 80:\n            return 'B'\n        else:\n            if score >= 70:\n                return 'C'\n            else:\n                if score >= 60:\n                    return 'D'\n                else:\n                    return 'F'\n",
        "test": """
import pytest
def test_grades():
    from solution import get_grade
    assert get_grade(95) == 'A'
    assert get_grade(85) == 'B'
    assert get_grade(75) == 'C'
    assert get_grade(65) == 'D'
    assert get_grade(55) == 'F'
    assert get_grade(100) == 'A'
    assert get_grade(0) == 'F'
""",
        "quality_checks": [
            "nested_if_reduced",  # shouldn't have deep nesting
            "pythonic",           # should use elif or bisect or dict
        ],
    },
    {
        "name": "extract_function",
        "prompt": "Refactor this long function by extracting appropriate helper functions.\n\n```python\ndef process_order(order):\n    # Validate\n    if not order.get('items'):\n        raise ValueError('No items')\n    for item in order['items']:\n        if item['qty'] <= 0:\n            raise ValueError(f'Invalid qty for {item[\"name\"]}')\n    # Calculate\n    subtotal = sum(item['price'] * item['qty'] for item in order['items'])\n    tax = subtotal * 0.08\n    if subtotal > 100:\n        shipping = 0\n    else:\n        shipping = 10\n    total = subtotal + tax + shipping\n    # Format receipt\n    lines = ['=== ORDER ===']\n    for item in order['items']:\n        lines.append(f'{item[\"name\"]}: ${item[\"price\"]:.2f} x {item[\"qty\"]}')\n    lines.append(f'Subtotal: ${subtotal:.2f}')\n    lines.append(f'Tax: ${tax:.2f}')\n    lines.append(f'Shipping: ${shipping:.2f}')\n    lines.append(f'Total: ${total:.2f}')\n    return '\\n'.join(lines)\n```\n\nReturn the refactored code with extracted helper functions.",
        "original_code": "def process_order(order):\n    if not order.get('items'):\n        raise ValueError('No items')\n    for item in order['items']:\n        if item['qty'] <= 0:\n            raise ValueError(f'Invalid qty for {item[\"name\"]}')\n    subtotal = sum(item['price'] * item['qty'] for item in order['items'])\n    tax = subtotal * 0.08\n    if subtotal > 100:\n        shipping = 0\n    else:\n        shipping = 10\n    total = subtotal + tax + shipping\n    lines = ['=== ORDER ===']\n    for item in order['items']:\n        lines.append(f'{item[\"name\"]}: ${item[\"price\"]:.2f} x {item[\"qty\"]}')\n    lines.append(f'Subtotal: ${subtotal:.2f}')\n    lines.append(f'Tax: ${tax:.2f}')\n    lines.append(f'Shipping: ${shipping:.2f}')\n    lines.append(f'Total: ${total:.2f}')\n    return '\\n'.join(lines)\n",
        "test": """
import pytest
def test_process_order():
    from solution import process_order
    order = {'items': [
        {'name': 'Widget', 'price': 25.0, 'qty': 2},
        {'name': 'Gadget', 'price': 10.0, 'qty': 1},
    ]}
    receipt = process_order(order)
    assert 'Subtotal: $60.00' in receipt
    assert 'Total: $74.80' in receipt
    assert 'Widget' in receipt

def test_free_shipping():
    from solution import process_order
    order = {'items': [{'name': 'Expensive', 'price': 200.0, 'qty': 1}]}
    receipt = process_order(order)
    assert 'Shipping: $0.00' in receipt

def test_empty_order():
    from solution import process_order
    import pytest as pt
    with pt.raises(ValueError):
        process_order({'items': []})
""",
        "quality_checks": ["has_helper_functions", "improved_readability"],
    },
]


class RefactorTask(TaskBase):
    spec = TaskSpec(
        task_id="refactor",
        name="Refactor Code",
        description="Improve code structure while preserving behavior",
        dimension="reasoning",
        difficulty="medium",
    )

    def generate(self, seed: int = 0) -> TaskContext:
        template = REFACTOR_TASKS[seed % len(REFACTOR_TASKS)]
        return TaskContext(
            system_prompt="You are a code refactoring expert. Improve the code for readability, maintainability, and Pythonic style. Preserve all existing behavior exactly.",
            problem_statement=template["prompt"],
            test_code=template["test"],
            tools_enabled=[],
        )

    def score(self, context: TaskContext, model_output: str,
              conversation: list[Message]) -> TaskResult:
        code_match = re.search(r'```(?:python)?\s*\n(.*?)\n```', model_output, re.DOTALL)
        code = code_match.group(1) if code_match else model_output

        # Run tests
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
            tests_passed = result.returncode == 0
            pass_rate = self._parse_pass_rate(result.stdout) if not tests_passed else 1.0
        except Exception:
            tests_passed = False
            pass_rate = 0.0
        finally:
            os.unlink(solution_path)
            try: test_file.unlink()
            except FileNotFoundError: pass
            pycache = Path(solution_path).parent / '__pycache__'
            if pycache.exists():
                shutil.rmtree(pycache)

        # Quality heuristics
        quality_score = self._assess_quality(code, model_output)
        score = 0.7 * pass_rate + 0.3 * quality_score

        return TaskResult(
            task_id=self.spec.task_id,
            task_name=self.spec.name,
            dimension=self.spec.dimension,
            score=score,
            passed=score >= self.passing_threshold(),
            details={"test_pass_rate": pass_rate, "quality_score": quality_score},
            model_output=model_output,
        )

    def _parse_pass_rate(self, stdout: str) -> float:
        match = re.search(r'(\d+) passed', stdout)
        passed = int(match.group(1)) if match else 0
        match = re.search(r'(\d+) failed', stdout)
        failed = int(match.group(1)) if match else 1
        return passed / (passed + failed) if (passed + failed) > 0 else 0.0

    def _assess_quality(self, code: str, output: str) -> float:
        """Heuristic code quality assessment."""
        score = 0.5
        # Less nesting is better
        lines = code.split('\n')
        max_indent = max(len(line) - len(line.lstrip()) for line in lines if line.strip()) // 4
        if max_indent <= 2:
            score += 0.15
        elif max_indent <= 3:
            score += 0.05

        # Shorter is better (but not empty)
        if 0 < len(lines) < 60:
            score += 0.10

        # Has comments/docstring
        if '"""' in code or "'''" in code or '# ' in code:
            score += 0.10

        # Uses Pythonic constructs
        if any(kw in code for kw in ['elif', 'with', 'enumerate', 'zip', 'any(', 'all(']):
            score += 0.10

        return min(1.0, score)
