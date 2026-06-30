"""Tool use task — measures ability to use external tools effectively.

The model must complete a task that requires calling specific tools.
"""

from ..base import TaskBase, TaskSpec, TaskContext, TaskResult, Message, ToolDefinition


TOOL_USE_SCENARIOS = [
    {
        "name": "file_search",
        "prompt": """You need to find all Python files in the project that contain the word "TODO".

Use the available tools to search the project. Report:
1. How many files contain "TODO"
2. List the file paths
3. What is the most common TODO category (e.g., "TODO: refactor", "TODO: test")?

Available tools: grep_search, file_list""",
        "expected_tools": ["grep_search"],
        "key_findings": ["TODO count", "file paths"],
    },
    {
        "name": "data_analysis",
        "prompt": """You have access to a CSV file called 'market_data.csv'.

Use the available tools to:
1. Read the CSV file
2. Calculate the mean and standard deviation of the 'close' column
3. Report the date range of the data
4. Find the maximum price and its date

Available tools: read_file, execute_python""",
        "expected_tools": ["read_file", "execute_python"],
        "key_findings": ["mean", "std", "max price"],
    },
    {
        "name": "git_investigation",
        "prompt": """Investigate the git repository to answer:

1. How many commits are on the current branch?
2. Who is the most recent committer?
3. What files changed in the most recent commit?
4. Are there any uncommitted changes?

Available tools: git_log, git_diff, git_status""",
        "expected_tools": ["git_log", "git_status"],
        "key_findings": ["commit count", "recent committer"],
    },
]


class ToolUseTask(TaskBase):
    spec = TaskSpec(
        task_id="tool_use",
        name="Tool Use",
        description="Use external tools to accomplish a task",
        dimension="tool_usage",
        difficulty="medium",
    )

    def generate(self, seed: int = 0) -> TaskContext:
        template = TOOL_USE_SCENARIOS[seed % len(TOOL_USE_SCENARIOS)]
        return TaskContext(
            system_prompt="You have access to tools. Use them effectively to answer the question. Be thorough.",
            problem_statement=template["prompt"],
            tools_enabled=template["expected_tools"],
        )

    def score(self, context: TaskContext, model_output: str,
              conversation: list[Message]) -> TaskResult:
        # Check if model actually used the expected tools
        tool_calls = [msg for msg in conversation if msg.role == "tool"]
        tools_used = set()
        for msg in tool_calls:
            if msg.name:
                tools_used.add(msg.name)

        expected = set(context.tools_enabled)
        if expected:
            tool_usage_ratio = len(tools_used & expected) / len(expected)
        else:
            tool_usage_ratio = 1.0

        # Score based on tool usage and output quality
        has_output = len(model_output.strip()) > 50  # meaningful response
        output_present = 0.3 if has_output else 0.0

        score = 0.4 * tool_usage_ratio + 0.3 * output_present + 0.3 * self._answer_quality(model_output)

        return TaskResult(
            task_id=self.spec.task_id,
            task_name=self.spec.name,
            dimension=self.spec.dimension,
            score=score,
            passed=score >= self.passing_threshold(),
            details={
                "tools_used": list(tools_used),
                "expected_tools": list(expected),
                "tool_usage_ratio": tool_usage_ratio,
            },
            model_output=model_output,
        )

    def _answer_quality(self, output: str) -> float:
        """Heuristic answer quality assessment."""
        output_lower = output.lower()
        quality = 0.0
        # Has structure (numbered items, bullet points, sections)
        if any(marker in output for marker in ['1.', '2.', '3.', '- ', '* ', '## ']):
            quality += 0.4
        # Contains specific findings (numbers, filenames)
        import re
        if re.search(r'\d+', output):
            quality += 0.3
        if re.search(r'\.(py|csv|json|yaml|md)', output_lower):
            quality += 0.3
        return min(1.0, quality)
