"""Self-repair task — measures ability to fix own mistakes.

The model is given a task, deliberately disrupted with a misleading hint,
and must recognize and recover from the error.
"""

from ..base import TaskBase, TaskSpec, TaskContext, TaskResult, Message


class SelfRepairTask(TaskBase):
    spec = TaskSpec(
        task_id="self_repair",
        name="Self-Repair",
        description="Recover from mistakes with corrective feedback",
        dimension="self_repair",
        difficulty="medium",
    )

    def generate(self, seed: int = 0) -> TaskContext:
        return TaskContext(
            system_prompt="You are a careful programmer. When you make a mistake, acknowledge it and fix it.",
            problem_statement="""I have a Python list of integers and I need to find all pairs that sum to a target value.

Example: given [1, 2, 3, 4, 5] and target=7, the pairs are [(2, 5), (3, 4)].

Write a function `find_pairs(arr, target)` that returns a list of unique pairs (as tuples) that sum to target. Each pair should have the smaller number first. Don't include duplicate pairs.

Return your solution in a Python code block.""",
            test_code="""def test_pairs():
    from solution import find_pairs
    result = find_pairs([1, 2, 3, 4, 5], 7)
    assert sorted(result) == [(2, 5), (3, 4)], f"Got {result}"

    result = find_pairs([1, 1, 2, 2, 3, 3], 4)
    assert sorted(result) == [(1, 3), (2, 2)], f"Got {result}"

    result = find_pairs([], 5)
    assert result == [], f"Got {result}"

    result = find_pairs([1, 2, 3], 10)
    assert result == [], f"Got {result}"
""",
            tools_enabled=[],
        )

    def score(self, context: TaskContext, model_output: str,
              conversation: list[Message]) -> TaskResult:
        import subprocess
        import tempfile
        import re
        import os
        import shutil
        from pathlib import Path

        # Extract code
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

        score = pass_rate

        return TaskResult(
            task_id=self.spec.task_id,
            task_name=self.spec.name,
            dimension=self.spec.dimension,
            score=score,
            passed=score >= self.passing_threshold(),
            details={"tests_passed": tests_passed, "pass_rate": pass_rate},
            model_output=model_output,
        )

    @staticmethod
    def _parse_pass_rate(stdout: str) -> float:
        import re
        match = re.search(r'(\d+) passed', stdout)
        passed = int(match.group(1)) if match else 0
        match = re.search(r'(\d+) failed', stdout)
        failed = int(match.group(1)) if match else 1
        return passed / (passed + failed) if (passed + failed) > 0 else 0.0
