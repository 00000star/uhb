"""Review PR task — measures code review and critical analysis ability.

The model must review a pull request and identify issues.
"""

from ..base import TaskBase, TaskSpec, TaskContext, TaskResult, Message


PR_REVIEW_SCENARIOS = [
    {
        "name": "security_review",
        "diff": """```diff
+def get_user_by_id(user_id):
+    query = f"SELECT * FROM users WHERE id = {user_id}"
+    return db.execute(query).fetchone()

-def validate_password(password):
-    return len(password) >= 8 and any(c.isupper() for c in password)
+def validate_password(password):
+    return len(password) >= 6

+SECRET_KEY = "my-secret-key-12345"
```
""",
        "prompt": """Review this pull request diff. Identify ALL issues including:
1. Security vulnerabilities
2. Code quality concerns
3. Regression risks
4. Any other problems

For each issue, explain the problem and suggest a fix. Rate severity (critical/high/medium/low).""",
        "known_issues": [
            "sql_injection",           # f-string in SQL query
            "hardcoded_secret",        # SECRET_KEY in source
            "weaker_password_policy",  # 6 chars down from 8, removed uppercase check
        ],
    },
    {
        "name": "performance_review",
        "diff": """```diff
+def find_duplicates(items):
+    duplicates = []
+    for i in range(len(items)):
+        for j in range(len(items)):
+            if i != j and items[i] == items[j] and items[i] not in duplicates:
+                duplicates.append(items[i])
+    return duplicates

-def process_data(data):
-    return [transform(x) for x in data if validate(x)]
+def process_data(data):
+    results = []
+    for x in data:
+        if validate(x):
+            results.append(transform(x))
+    return results
```
""",
        "prompt": """Review this pull request diff. Identify ALL issues including:
1. Performance problems
2. Algorithmic complexity issues
3. Better alternatives
4. Any other problems

For each issue, explain the problem and suggest a fix.""",
        "known_issues": [
            "O(n^2)_duplicate_find",   # quadratic algorithm
            "inefficient_loop",         # O(n) in list not in set
        ],
    },
]


class ReviewPRTask(TaskBase):
    spec = TaskSpec(
        task_id="review_pr",
        name="Review a Pull Request",
        description="Critically review code changes and identify issues",
        dimension="reasoning",
        difficulty="medium",
    )

    def generate(self, seed: int = 0) -> TaskContext:
        template = PR_REVIEW_SCENARIOS[seed % len(PR_REVIEW_SCENARIOS)]
        return TaskContext(
            system_prompt="You are a thorough code reviewer. Identify security, performance, correctness, and style issues. Be specific — reference exact lines. Rate severity of each finding.",
            problem_statement=template["prompt"],
            files={"diff.patch": template["diff"]},
            tools_enabled=[],
        )

    def score(self, context: TaskContext, model_output: str,
              conversation: list[Message]) -> TaskResult:
        output_lower = model_output.lower()
        template = PR_REVIEW_SCENARIOS[0]

        # How many known issues were found?
        known = template.get("known_issues", [])
        found = sum(1 for issue in known if issue.lower() in output_lower)
        recall = found / len(known) if known else 1.0

        # False positive penalty (mentioning issues that don't exist)
        # Simple heuristic: check for hallucinated keywords
        false_positive_indicators = []
        false_positive_score = 1.0  # no penalty by default

        # Structure and thoroughness
        structure_score = 0.0
        if len(model_output) > 200:
            structure_score += 0.3
        if any(marker in model_output for marker in ['1.', '2.', '3.', '- ', '## ', '**']):
            structure_score += 0.3
        if any(word in output_lower for word in ['severity', 'critical', 'high', 'medium', 'low']):
            structure_score += 0.2
        if 'fix' in output_lower or 'suggest' in output_lower or 'recommend' in output_lower:
            structure_score += 0.2

        # Composite score
        score = 0.5 * recall + 0.3 * structure_score + 0.2 * false_positive_score

        return TaskResult(
            task_id=self.spec.task_id,
            task_name=self.spec.name,
            dimension=self.spec.dimension,
            score=score,
            passed=score >= self.passing_threshold(),
            details={
                "issues_found": found,
                "total_issues": len(known),
                "recall": recall,
            },
            model_output=model_output,
        )
