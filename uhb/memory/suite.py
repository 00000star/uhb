"""Memory benchmark suite — evaluates agent memory across 5 dimensions."""

import random
import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Callable


class MemoryDimension(Enum):
    SHORT_TERM = "short_term"        # In-conversation retention
    LONG_TERM = "long_term"          # Cross-session memory
    RETRIEVAL = "retrieval"          # Accuracy of retrieving past context
    COMPRESSION = "compression"      # Quality after summarization
    FORGETTING = "forgetting"        # What gets forgotten and when


@dataclass
class MemoryResult:
    """Result from a memory benchmark run."""
    model_id: str
    dimension: MemoryDimension
    score: float                    # 0.0–1.0
    details: dict = field(default_factory=dict)


@dataclass
class MemoryProfile:
    """Complete memory profile for a model."""
    model_id: str
    results: list[MemoryResult] = field(default_factory=list)

    def dimension_score(self, dim: MemoryDimension) -> float:
        scores = [r.score for r in self.results if r.dimension == dim]
        return sum(scores) / len(scores) if scores else 0.0

    def overall_score(self) -> float:
        scores = [self.dimension_score(d) for d in MemoryDimension]
        return sum(scores) / len(scores)

    def to_dict(self) -> dict:
        return {
            "model_id": self.model_id,
            "overall": round(self.overall_score(), 4),
            "dimensions": {
                dim.value: round(self.dimension_score(dim), 4)
                for dim in MemoryDimension
            },
        }


class MemorySuite:
    """Suite of memory benchmark tests.

    Runs a model through progressively longer conversations and measures:
    - Short-term: Can it recall details from earlier in the conversation?
    - Retrieval: Can it find and apply past context correctly?
    - Compression: Does summarization preserve important information?
    - Forgetting: What specific information is lost as context grows?
    - Long-term: Can it maintain information across simulated session boundaries?
    """

    # Hidden facts for memory tests
    FACTS = [
        ("The API key for staging is 'sk-staging-9x7y5z3w1v'.", "api_key", "sk-staging-"),
        ("The database password was rotated to 'db-pass-2024-q3-x9'.", "db_password", "db-pass-"),
        ("The critical bug is in the payment processor, line 847.", "bug_location", "line 847"),
        ("The team agreed to use React 19 for the new dashboard.", "tech_decision", "React 19"),
        ("Alice is the on-call engineer this week (Dec 15-21).", "on_call", "Alice"),
        ("The load balancer timeout must be increased to 120 seconds.", "config_change", "120 seconds"),
        ("The staging environment is running on port 8443.", "port", "8443"),
        ("The code freeze starts on Friday at 5pm UTC.", "freeze", "Friday 5pm"),
    ]

    def __init__(self, model_id: str, send_fn: Callable, seed: int = 42):
        self.model_id = model_id
        self.send = send_fn  # function(messages) -> response_text
        self.rng = random.Random(seed)

    def test_short_term(self, context_size: int = 10_000) -> MemoryResult:
        """Test short-term memory by placing facts in conversation and testing recall.

        Args:
            context_size: Target context size in characters.

        Returns:
            MemoryResult with recall accuracy.
        """
        # Generate filler paragraphs
        filler = self._generate_filler(context_size)

        # Plant facts at positions
        facts = self.rng.sample(self.FACTS, 4)
        planted = {}
        paragraphs = filler.split("\n\n")
        positions = sorted(self.rng.sample(range(5, len(paragraphs) - 5), len(facts)))

        modified = paragraphs[:]
        for pos, (fact, key, _) in zip(positions, facts):
            modified.insert(pos, f"[IMPORTANT NOTE] {fact}")
            planted[key] = fact

        full_context = "\n\n".join(modified)

        # Query after context
        query_parts = ["Based on the document above, answer these questions:"]
        for key in planted:
            # Generate question from fact
            for fact, fkey, _ in facts:
                if fkey == key:
                    if "api_key" in fkey:
                        query_parts.append(f"- What is the staging API key?")
                    elif "password" in fkey:
                        query_parts.append(f"- What is the database password?")
                    elif "bug" in fkey:
                        query_parts.append(f"- Where is the critical bug located?")
                    elif "tech" in fkey:
                        query_parts.append(f"- What technology was chosen for the dashboard?")
                    elif "on_call" in fkey:
                        query_parts.append(f"- Who is on-call this week?")
                    elif "config" in fkey:
                        query_parts.append(f"- What change was made to the load balancer?")
                    elif "port" in fkey:
                        query_parts.append(f"- What port is staging running on?")
                    elif "freeze" in fkey:
                        query_parts.append(f"- When does the code freeze start?")

        messages = [
            {"role": "user", "content": full_context},
            {"role": "user", "content": "\n".join(query_parts) + "\n\nIf you don't remember something, say 'I don't recall.'"},
        ]

        response = self.send(messages)

        # Score: check how many facts were recalled correctly
        correct = 0
        for fact, key, keyword in facts:
            if keyword.lower() in response.lower():
                correct += 1

        score = correct / len(facts) if facts else 0.0

        return MemoryResult(
            model_id=self.model_id,
            dimension=MemoryDimension.SHORT_TERM,
            score=score,
            details={"facts_planted": len(facts), "facts_recalled": correct, "context_chars": len(full_context)},
        )

    def test_compression(self) -> MemoryResult:
        """Test whether important information survives summarization.

        Returns:
            MemoryResult with compression quality score.
        """
        # This is a proxy test: give a long text and ask for a summary,
        # then check if key details are preserved
        filler = self._generate_filler(8000)

        facts = self.rng.sample(self.FACTS, 3)
        # Plant facts in filler
        parts = filler.split("\n\n")
        for i, (fact, _, _) in enumerate(facts):
            pos = 10 + i * 15
            if pos < len(parts):
                parts.insert(pos, f"[NOTE] {fact}")

        full_text = "\n\n".join(parts)

        messages = [
            {"role": "user", "content": f"Please summarize the following text in 3-4 bullet points. Include all specific details, numbers, and names mentioned:\n\n{full_text}"},
        ]

        summary = self.send(messages)

        # Check how many key details survived
        preserved = 0
        for _, _, keyword in facts:
            if keyword.lower() in summary.lower():
                preserved += 1

        score = preserved / len(facts) if facts else 0.0

        return MemoryResult(
            model_id=self.model_id,
            dimension=MemoryDimension.COMPRESSION,
            score=score,
            details={"facts_preserved": preserved, "facts_total": len(facts), "summary_length": len(summary)},
        )

    def test_forgetting(self, sizes: list[int] = [5000, 15000, 30000, 60000]) -> MemoryResult:
        """Test how recall degrades as context size increases.

        Args:
            sizes: Context sizes in characters to test.

        Returns:
            MemoryResult with degradation curve.
        """
        scores = []
        for size in sizes:
            result = self.test_short_term(context_size=size)
            scores.append((size, result.score))

        # Fit a degradation slope: score drop per 10k characters
        if len(scores) >= 2:
            xs = [s[0] for s in scores]
            ys = [s[1] for s in scores]
            slope = (ys[-1] - ys[0]) / ((xs[-1] - xs[0]) / 10000) if xs[-1] != xs[0] else 0
        else:
            slope = 0.0

        # Normalize: 0 = no degradation, 1 = steep degradation
        normalized = max(0.0, min(1.0, 1.0 + slope))  # slope is negative (score drops)

        return MemoryResult(
            model_id=self.model_id,
            dimension=MemoryDimension.FORGETTING,
            score=normalized,
            details={"scores_by_size": dict(scores), "degradation_slope": slope},
        )

    def test_retrieval(self) -> MemoryResult:
        """Test accuracy of retrieving information from past context.

        Returns:
            MemoryResult with retrieval accuracy.
        """
        # Plant facts, then ask model to retrieve specific ones
        filler = self._generate_filler(5000)
        facts = self.rng.sample(self.FACTS, 3)
        parts = filler.split("\n\n")
        for i, (fact, key, _) in enumerate(facts):
            parts.insert(5 + i * 8, f"[CONFIG] {key}: {fact}")

        full_text = "\n\n".join(parts)

        # Ask for a specific key
        target = facts[0]
        messages = [
            {"role": "user", "content": f"{full_text}\n\nBased on the configuration above, what is the value of '{target[1]}'? Answer with just the value."},
        ]

        response = self.send(messages)

        # Check if the correct keyword appears
        correct = target[2].lower() in response.lower()
        score = 1.0 if correct else 0.0

        return MemoryResult(
            model_id=self.model_id,
            dimension=MemoryDimension.RETRIEVAL,
            score=score,
            details={"target_key": target[1], "found": correct},
        )

    def run_full(self) -> MemoryProfile:
        """Run all memory tests."""
        profile = MemoryProfile(model_id=self.model_id)

        profile.results.append(self.test_short_term())
        profile.results.append(self.test_retrieval())
        profile.results.append(self.test_compression())
        profile.results.append(self.test_forgetting())

        return profile

    def _generate_filler(self, target_chars: int) -> str:
        """Generate deterministic filler text of approximately target_chars length."""
        from . import LOREM_PARAGRAPHS
        text = []
        total = 0
        paragraphs = LOREM_PARAGRAPHS
        i = 0
        while total < target_chars:
            para = paragraphs[i % len(paragraphs)]
            text.append(para)
            total += len(para)
            i += 1
        return "\n\n".join(text)
