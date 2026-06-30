"""Search documentation task — measures ability to find and apply information.

The model must search for information and apply it correctly.
"""

from ..base import TaskBase, TaskSpec, TaskContext, TaskResult, Message


SEARCH_TASKS = [
    {
        "name": "api_usage",
        "prompt": """I need to use an unfamiliar Python library. Please look up how to do the following:

Parse a TOML configuration file in Python, extract a nested value at path "database.credentials.password", and handle the case where the key might not exist.

Show me the complete working code snippet. You have access to search tools — use them if needed.""",
        "expected_elements": ["tomllib", "toml", "load", "get", "except", "try"],
    },
    {
        "name": "error_resolution",
        "prompt": """I'm getting this error in my Python code:

```
TypeError: cannot concatenate 'str' and 'int' objects
```

Search for the standard way to handle this in Python 3.11+ (the modern approach with type hints). Show me both:
1. Why this error occurs
2. Three different ways to fix it
3. Which fix is most Pythonic""",
        "expected_elements": ["str()", "f-string", "TypeError", "concatenat"],
    },
]


class SearchDocsTask(TaskBase):
    spec = TaskSpec(
        task_id="search_docs",
        name="Search Documentation",
        description="Find and apply information from external sources",
        dimension="exploration",
        difficulty="easy",
    )

    def generate(self, seed: int = 0) -> TaskContext:
        template = SEARCH_TASKS[seed % len(SEARCH_TASKS)]
        return TaskContext(
            system_prompt="You are a helpful programming assistant with access to web search tools. Use them to find accurate, up-to-date information. Cite sources.",
            problem_statement=template["prompt"],
            tools_enabled=["web_search", "web_fetch"],
        )

    def score(self, context: TaskContext, model_output: str,
              conversation: list[Message]) -> TaskResult:
        output_lower = model_output.lower()

        # Scoring heuristics
        scores = []

        # Length: must have substantive content
        if len(model_output) > 100:
            scores.append(0.15)
        else:
            scores.append(0.0)

        # Structure
        if any(m in model_output for m in ['```', '1.', '2.', '## ']):
            scores.append(0.15)

        # Contains code examples
        if '```' in model_output:
            scores.append(0.25)

        # Cites sources or shows research
        if any(word in output_lower for word in ['docs.python.org', 'documentation', 'according to', 'source']):
            scores.append(0.20)

        # Answers the actual question (contains expected elements)
        template = SEARCH_TASKS[0]  # simplified; in reality track which template was used
        matches = sum(1 for elem in template.get("expected_elements", []) if elem.lower() in output_lower)
        if len(template.get("expected_elements", [])) > 0:
            scores.append(0.25 * min(1.0, matches / len(template["expected_elements"])))

        score = sum(scores)

        return TaskResult(
            task_id=self.spec.task_id,
            task_name=self.spec.name,
            dimension=self.spec.dimension,
            score=score,
            passed=score >= self.passing_threshold(),
            details={"content_length": len(model_output)},
            model_output=model_output,
        )
