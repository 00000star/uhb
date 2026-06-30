"""Plan feature task — measures planning and decomposition ability.

The model must plan a complex feature before (or instead of) implementing it.
"""

from ..base import TaskBase, TaskSpec, TaskContext, TaskResult, Message


PLANNING_SCENARIOS = [
    {
        "name": "real_time_chat",
        "prompt": """Plan the implementation of a real-time chat feature for a Django web application.

Requirements:
- Users can send messages in real-time (no page refresh)
- Messages persist to the database
- Support for multiple chat rooms
- Online/offline status indicators
- Typing indicators
- Message history scrollback (lazy loading)
- Must support 10k concurrent users

Produce a detailed plan covering:
1. Architecture decisions (WebSocket vs SSE vs polling — justify)
2. Component breakdown
3. Data model schema
4. API design
5. Scaling strategy
6. Testing approach
7. Estimated timeline (with breakdown)

Do NOT write code. This is a planning exercise.""",
        "expected_sections": ["architecture", "component", "data model", "api", "scaling", "testing", "timeline"],
    },
    {
        "name": "migration_strategy",
        "prompt": """Plan the migration of a monolithic Python/Flask application to microservices.

Current state:
- Single Flask app with 200 routes
- PostgreSQL database (80 tables)
- Redis for caching and sessions
- Celery for background tasks
- 50k lines of Python code
- Deployed on AWS EC2

The team has 5 backend engineers. Zero-downtime migration is required.

Produce a detailed migration plan covering:
1. Service boundary identification strategy
2. Migration order (which services first and why)
3. Data separation approach
4. Inter-service communication design
5. CI/CD pipeline changes
6. Rollback strategy
7. Timeline and risk assessment

Do NOT write code. This is a planning exercise.""",
        "expected_sections": ["boundar", "order", "data", "communication", "ci/cd", "rollback", "timeline", "risk"],
    },
]


class PlanFeatureTask(TaskBase):
    spec = TaskSpec(
        task_id="plan_feature",
        name="Plan a Feature",
        description="Produce a detailed implementation plan for a complex feature",
        dimension="planning",
        difficulty="hard",
    )

    def generate(self, seed: int = 0) -> TaskContext:
        template = PLANNING_SCENARIOS[seed % len(PLANNING_SCENARIOS)]
        return TaskContext(
            system_prompt="You are a senior software architect. Produce thorough, well-structured plans. Do NOT write code — this is a design and planning exercise.",
            problem_statement=template["prompt"],
            tools_enabled=[],
        )

    def score(self, context: TaskContext, model_output: str,
              conversation: list[Message]) -> TaskResult:
        output_lower = model_output.lower()

        # Scoring dimensions
        scores = []

        # 1. Length and substance
        if len(model_output) > 500:
            scores.append(0.10)
        if len(model_output) > 1500:
            scores.append(0.10)

        # 2. Has structure (sections, headings)
        if model_output.count('#') >= 3:
            scores.append(0.15)
        elif model_output.count('#') >= 1:
            scores.append(0.08)

        # 3. Covers expected topics
        template = PLANNING_SCENARIOS[0]
        expected = template.get("expected_sections", [])
        covered = sum(1 for e in expected if e.lower() in output_lower)
        if expected:
            scores.append(0.30 * min(1.0, covered / len(expected)))

        # 4. Contains concrete details (not vague)
        concrete_indicators = ['days', 'weeks', 'engineers', 'postgresql', 'redis', 'websocket',
                              'api gateway', 'kubernetes', 'docker', 'postgres', 'mysql']
        concrete_count = sum(1 for ind in concrete_indicators if ind in output_lower)
        scores.append(0.15 * min(1.0, concrete_count / 5))

        # 5. Trade-offs mentioned
        if any(word in output_lower for word in ['trade-off', 'tradeoff', 'alternative', 'however', 'pros', 'cons']):
            scores.append(0.10)

        # 6. No code (penalize if model wrote code anyway)
        if '```' in model_output:
            scores.append(-0.10)

        score = max(0.0, sum(scores))

        return TaskResult(
            task_id=self.spec.task_id,
            task_name=self.spec.name,
            dimension=self.spec.dimension,
            score=score,
            passed=score >= self.passing_threshold(),
            details={"length": len(model_output), "sections_found": covered},
            model_output=model_output,
        )
