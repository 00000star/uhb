"""Long context task — measures ability to retain information across long conversations.

The model is given a large amount of filler text, then asked questions about
specific details buried within it.
"""

import hashlib
import random
from typing import Optional

from ..base import TaskBase, TaskSpec, TaskContext, TaskResult, Message


LOREM_PARAGRAPHS = [
    "The quantum computing paradigm shift represents a fundamental change in how we approach computational complexity. Traditional binary systems operate on bits that exist in one of two states, but quantum systems leverage superposition to explore multiple states simultaneously. This property, combined with entanglement, enables certain algorithms to achieve exponential speedups over their classical counterparts. However, quantum decoherence remains a significant engineering challenge that limits the practical scalability of current quantum processors.",
    "Microservices architecture has emerged as the dominant pattern for building large-scale distributed systems. By decomposing applications into independently deployable services, teams can achieve greater autonomy and faster iteration cycles. Each service owns its data store, communicates via well-defined APIs, and can be scaled independently based on demand. However, this architecture introduces complexity in areas like distributed transactions, eventual consistency, service discovery, and observability.",
    "Reinforcement learning from human feedback (RLHF) has become the standard approach for aligning large language models with human preferences. The process involves collecting human preference data over model outputs, training a reward model to predict these preferences, and then using proximal policy optimization (PPO) to fine-tune the language model against the reward signal. Recent research has explored alternatives like direct preference optimization (DPO) that simplify this pipeline by directly optimizing the policy from preference pairs.",
    "The Linux kernel's memory management subsystem implements virtual memory through a combination of page tables, translation lookaside buffers (TLBs), and demand paging. When a process accesses a virtual address, the memory management unit (MMU) traverses the page table to find the corresponding physical frame. A TLB miss triggers a page walk that can add significant latency. The kernel uses various optimizations including huge pages, page cache, and memory-mapped I/O to improve performance.",
    "TypeScript's type system is a structural type system that allows for expressive modeling of JavaScript patterns. Unlike nominal type systems found in languages like Java or C#, TypeScript uses structural subtyping where compatibility is determined by the shape of types rather than their declared names. This enables powerful patterns like discriminated unions, mapped types, conditional types, and template literal types. The compiler performs type inference to reduce annotation burden while still catching common errors.",
    "Apache Kafka provides a distributed commit log abstraction that has become the backbone of many event-driven architectures. Producers append records to topics, which are partitioned across brokers for horizontal scalability. Consumers read from partitions using an offset pointer, enabling replay of historical data. Kafka's design guarantees ordering within a partition, durability through replication, and high throughput through zero-copy I/O and batched operations.",
    "Graph neural networks (GNNs) extend deep learning to graph-structured data by learning representations that capture both node features and graph topology. Message passing is the dominant paradigm: each node aggregates information from its neighbors, transforms it through a neural network, and updates its representation. Variants include Graph Convolutional Networks (GCNs) that use spectral convolution, Graph Attention Networks (GATs) that learn edge weights, and GraphSAGE that samples neighbors for scalability.",
    "Database indexing is critical for query performance in relational systems. B-tree indexes provide logarithmic time complexity for point queries and range scans, making them the default choice for most workloads. Hash indexes offer O(1) point lookups but don't support range queries. Bitmap indexes are effective for low-cardinality columns. The query optimizer uses index statistics and cost models to select the most efficient access path for each query.",
    "Docker containers provide operating-system-level virtualization by leveraging Linux kernel features like namespaces and cgroups. Each container has its own isolated view of the process tree, network interfaces, mount points, and user IDs, while sharing the host kernel. This provides lighter-weight isolation than virtual machines while maintaining strong security boundaries. Container images are built from layered filesystems, enabling efficient storage and distribution through registries.",
    "The transformer architecture has revolutionized natural language processing through its self-attention mechanism. Unlike recurrent networks that process tokens sequentially, transformers compute attention scores between all pairs of tokens in parallel. Multi-head attention allows the model to attend to information from different representation subspaces. Positional encodings inject sequence order information since the architecture itself is permutation-invariant.",
    "Rust's ownership system guarantees memory safety without garbage collection through a set of compile-time rules. Each value has exactly one owner at a time, and references come with explicit lifetimes that the borrow checker verifies. Move semantics transfer ownership, while borrowing allows temporary access. These rules eliminate entire classes of bugs including use-after-free, double-free, and data races, making Rust particularly suitable for systems programming.",
    "Kubernetes orchestrates containerized applications across clusters of machines. The control plane (API server, scheduler, controller manager) manages the desired state, while nodes run kubelet agents that maintain running pods. Workloads are defined declaratively through YAML manifests specifying containers, resources, networking, and storage. Controllers continuously reconcile actual state toward desired state. Service meshes like Istio add advanced traffic management, security, and observability at the network layer.",
]

# Hidden facts the model must recall after reading filler text
HIDDEN_FACTS = {
    "quantum_color": "The quantum computer in lab 7 is painted bright orange.",
    "database_password": "The staging database password is 'blue-elephant-42'.",
    "meeting_time": "The architecture review meeting is scheduled for Thursday at 3pm.",
    "api_key": "The test API key is 'sk-test-9a8b7c6d5e4f'.",
    "server_ip": "The backup server IP is 10.42.7.13.",
    "bug_ticket": "The critical bug ticket #7842 is about memory leaks in the image processing pipeline.",
    "team_size": "There are exactly 23 engineers working on the authentication service.",
    "deploy_window": "Production deployments are only allowed between 2am and 4am UTC on Sundays.",
    "config_value": "The MAX_CONNECTIONS setting must be set to 500 for the load balancer.",
    "dependency_version": "The project requires Django version 4.2.0 or higher, but not 5.x.",
}


class LongContextTask(TaskBase):
    spec = TaskSpec(
        task_id="long_context",
        name="Long Context Retention",
        description="Remember details after processing a large amount of text",
        dimension="long_context",
        difficulty="hard",
        max_tokens=32_000,
    )

    def generate(self, seed: int = 0) -> TaskContext:
        rng = random.Random(seed)

        # Build a large context by repeating paragraphs with hidden facts interspersed
        paragraphs = LOREM_PARAGRAPHS.copy()
        rng.shuffle(paragraphs)

        # Select 3 random facts to hide
        fact_keys = list(HIDDEN_FACTS.keys())
        rng.shuffle(fact_keys)
        selected_facts = fact_keys[:3]

        # Build the context: interleave paragraphs with facts
        context_parts = []
        fact_positions = {}
        para_idx = 0
        for i, fact_key in enumerate(selected_facts):
            # Add 3-5 paragraphs before each fact
            num_paras = rng.randint(3, 5)
            for _ in range(num_paras):
                if para_idx < len(paragraphs):
                    context_parts.append(paragraphs[para_idx])
                    para_idx = (para_idx + 1) % len(paragraphs)
            context_parts.append(f"[NOTE] {HIDDEN_FACTS[fact_key]}")
            fact_positions[fact_key] = len(context_parts)  # approximate position

        # Add more filler after facts
        for _ in range(rng.randint(10, 20)):
            context_parts.append(paragraphs[para_idx])
            para_idx = (para_idx + 1) % len(paragraphs)

        # Build the prompt with context and questions
        context_text = "\n\n".join(context_parts)

        questions = []
        for fk in selected_facts:
            fact = HIDDEN_FACTS[fk]
            # Generate a question from the fact
            if "painted" in fact:
                questions.append("What color is the quantum computer in lab 7?")
            elif "password" in fact:
                questions.append("What is the staging database password?")
            elif "meeting" in fact:
                questions.append("When is the architecture review meeting scheduled?")
            elif "API key" in fact:
                questions.append("What is the test API key?")
            elif "IP" in fact:
                questions.append("What is the backup server IP address?")
            elif "ticket" in fact:
                questions.append("What is the critical bug ticket about?")
            elif "engineers" in fact:
                questions.append("How many engineers work on the authentication service?")
            elif "deploy" in fact:
                questions.append("When are production deployments allowed?")
            elif "MAX_CONNECTIONS" in fact:
                questions.append("What value should MAX_CONNECTIONS be set to?")
            elif "Django" in fact:
                questions.append("Which version of Django does the project require?")

        full_prompt = f"""I'm going to share a large technical document with you. Please read it carefully.

--- BEGIN DOCUMENT ---
{context_text}
--- END DOCUMENT ---

Now, based ONLY on what you read in the document above, answer these questions:

{chr(10).join(f'{i+1}. {q}' for i, q in enumerate(questions))}

If you don't remember something, say "I don't recall" rather than guessing."""

        return TaskContext(
            system_prompt="You have excellent memory and attention to detail. Read everything carefully and answer questions based only on what was presented.",
            problem_statement=full_prompt,
            tools_enabled=[],
        )

    def score(self, context: TaskContext, model_output: str,
              conversation: list[Message]) -> TaskResult:
        output_lower = model_output.lower()

        # Extract the expected answers from the hidden facts embedded in the prompt
        problem = context.problem_statement
        # Find which facts were included
        fact_checks = []
        for key, fact in HIDDEN_FACTS.items():
            if fact in problem:
                # Extract the key information to check
                if "orange" in fact.lower():
                    fact_checks.append(("orange", fact))
                elif "blue-elephant-42" in fact.lower():
                    fact_checks.append(("blue-elephant-42", fact))
                elif "thursday" in fact.lower() or "3pm" in fact.lower():
                    fact_checks.append(("thursday", fact))
                elif "sk-test-9a8b7c6d5e4f" in fact.lower():
                    fact_checks.append(("sk-test-9a8b7c6d5e4f", fact))
                elif "10.42.7.13" in fact:
                    fact_checks.append(("10.42.7.13", fact))
                elif "memory leak" in fact.lower():
                    fact_checks.append(("memory leak", fact))
                elif "23" in fact:
                    fact_checks.append(("23", fact))
                elif "2am" in fact.lower() or "sunday" in fact.lower():
                    fact_checks.append(("2am", fact))
                elif "500" in fact:
                    fact_checks.append(("500", fact))
                elif "4.2.0" in fact:
                    fact_checks.append(("4.2.0", fact))

        # Count correct answers
        correct = 0
        for keyword, _ in fact_checks:
            if keyword.lower() in output_lower:
                correct += 1

        total = len(fact_checks) if fact_checks else 3
        recall = correct / total

        # Prefer "I don't recall" over hallucination
        honesty_bonus = 0.0
        if "don't recall" in output_lower or "don't remember" in output_lower:
            honesty_bonus = 0.1  # small bonus for admitting uncertainty

        score = min(1.0, recall + honesty_bonus)

        return TaskResult(
            task_id=self.spec.task_id,
            task_name=self.spec.name,
            dimension=self.spec.dimension,
            score=score,
            passed=score >= self.passing_threshold(),
            details={
                "facts_correct": correct,
                "facts_total": total,
                "recall": round(recall, 2),
            },
            model_output=model_output,
        )
