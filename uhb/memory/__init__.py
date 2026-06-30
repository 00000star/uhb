"""Agent memory benchmark — evaluate short-term, long-term, retrieval, compression, and forgetting."""

from .suite import MemorySuite, MemoryResult, MemoryProfile, MemoryDimension
from .strategies import (
    MemoryStrategy, StrategyType, STRATEGY_PRESETS,
    summarize, compress, sliding_window, vector_store,
)

# Shared filler text for memory tests
LOREM_PARAGRAPHS = [
    "The quantum computing paradigm represents a fundamental shift in computational complexity. Traditional binary systems operate on bits that exist in one of two states, but quantum systems leverage superposition to explore multiple states simultaneously. This property enables certain algorithms to achieve exponential speedups over classical counterparts.",
    "Microservices architecture decomposes applications into independently deployable services, enabling greater autonomy and faster iteration. Each service owns its data store and communicates via well-defined APIs. However, this introduces complexity in distributed transactions, eventual consistency, and service discovery.",
    "Reinforcement learning from human feedback (RLHF) aligns large language models with human preferences. The process involves collecting preference data, training a reward model, and using proximal policy optimization to fine-tune the language model against the reward signal.",
    "The Linux kernel's memory management subsystem implements virtual memory through page tables, TLBs, and demand paging. When a process accesses a virtual address, the MMU traverses the page table to find the corresponding physical frame. TLB misses add significant latency.",
    "TypeScript's structural type system enables expressive modeling of JavaScript patterns. Unlike nominal type systems, TypeScript uses structural subtyping where compatibility is determined by shape. This enables discriminated unions, mapped types, and conditional types.",
    "Apache Kafka provides a distributed commit log that forms the backbone of event-driven architectures. Producers append records to topics partitioned across brokers. Consumers read using offsets, enabling replay. Kafka guarantees ordering within a partition.",
    "Graph neural networks extend deep learning to graph-structured data through message passing. Each node aggregates information from neighbors, transforms it through a neural network, and updates its representation. Variants include GCNs, GATs, and GraphSAGE.",
    "Database indexing is critical for query performance. B-tree indexes provide logarithmic time for point queries and range scans. Hash indexes offer O(1) point lookups. Bitmap indexes suit low-cardinality columns. Query optimizers use statistics to choose access paths.",
    "Docker containers provide OS-level virtualization using Linux namespaces and cgroups. Each container has isolated process trees, network interfaces, and mount points while sharing the host kernel. Images use layered filesystems for efficient storage and distribution.",
    "The transformer architecture revolutionized NLP through self-attention. Transformers compute attention between all token pairs in parallel. Multi-head attention allows different representation subspaces. Positional encodings inject order information.",
    "Rust's ownership system guarantees memory safety without garbage collection. Each value has exactly one owner. References have explicit lifetimes verified by the borrow checker. This eliminates use-after-free, double-free, and data races at compile time.",
    "Kubernetes orchestrates containerized applications across clusters. The control plane manages desired state while nodes run pods. Workloads are declared via YAML manifests. Controllers reconcile actual state toward desired state continuously.",
    "CI/CD pipelines automate the software delivery process. Continuous integration builds and tests code on every commit. Continuous deployment automatically releases passing changes to production. Modern pipelines use declarative configurations and container-based runners.",
    "The OWASP Top 10 catalogs the most critical web application security risks. It includes injection attacks, broken authentication, sensitive data exposure, XML external entities, broken access control, security misconfiguration, and cross-site scripting.",
    "Time series databases optimize for storing and querying timestamped data. They use columnar storage, efficient compression, and time-based partitioning. InfluxDB, TimescaleDB, and Prometheus are popular choices with different trade-offs.",
]

__version__ = "0.1.0"
__all__ = [
    "MemorySuite", "MemoryResult", "MemoryProfile", "MemoryDimension",
    "MemoryStrategy", "StrategyType", "StrategyPresets",
    "summarize", "compress", "sliding_window", "vector_store",
]
