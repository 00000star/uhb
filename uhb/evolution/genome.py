"""Harness Genome — DNA representation for AI coding workflows.

Every harness is a sequence of genes. Genes can mutate, recombine,
and evolve through genetic algorithms to discover optimal workflows.

Genes: PLAN, RESEARCH, ARCHITECT, CODE, ANALYZE, TEST, REPAIR,
       SECURITY, REVIEW, DOCUMENT, COMMIT, DEPLOY
"""

import copy
import random
import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Gene(Enum):
    """A single step in a coding workflow."""
    PLAN = "plan"               # Plan the approach before coding
    RESEARCH = "research"       # Research libraries, APIs, documentation
    ARCHITECT = "architect"     # Design the system architecture
    CODE = "code"               # Write the implementation
    ANALYZE = "analyze"         # Static analysis, lint, type-check
    TEST = "test"               # Run tests
    REPAIR = "repair"           # Fix bugs and test failures
    SECURITY = "security"       # Security review
    REVIEW = "review"           # Code review
    DOCUMENT = "document"       # Generate documentation
    COMMIT = "commit"           # Commit changes
    DEPLOY = "deploy"           # Deploy to environment

    @property
    def symbol(self) -> str:
        """Short symbol for display."""
        symbols = {
            Gene.PLAN: "PLN", Gene.RESEARCH: "RSC", Gene.ARCHITECT: "ARC",
            Gene.CODE: "COD", Gene.ANALYZE: "ANL", Gene.TEST: "TST",
            Gene.REPAIR: "RPR", Gene.SECURITY: "SEC", Gene.REVIEW: "REV",
            Gene.DOCUMENT: "DOC", Gene.COMMIT: "CMT", Gene.DEPLOY: "DEP",
        }
        return symbols.get(self, "???")


# All available genes
ALL_GENES = list(Gene)

# Default genome: a standard "plan → code → test → review" workflow
DEFAULT_GENOME = [Gene.PLAN, Gene.CODE, Gene.TEST, Gene.REVIEW]

# Minimal genome: just code and test
MINIMAL_GENOME = [Gene.CODE, Gene.TEST]

# Comprehensive genome: every step
COMPREHENSIVE_GENOME = [
    Gene.RESEARCH, Gene.PLAN, Gene.ARCHITECT,
    Gene.CODE, Gene.ANALYZE, Gene.TEST,
    Gene.REPAIR, Gene.SECURITY, Gene.REVIEW,
    Gene.DOCUMENT, Gene.COMMIT,
]


@dataclass
class HarnessGenome:
    """A complete harness specification as a genome.

    The genome is the ordered sequence of genes (workflow steps).
    It also carries configuration for context strategy, tool policy,
    retry policy, and conditional branching.
    """
    genes: list[Gene] = field(default_factory=lambda: list(DEFAULT_GENOME))
    context_strategy: str = "full"      # "full", "sliding_window", "summary"
    tool_policy: str = "all"            # "all", "limited", "read_only"
    retry_policy: str = "on_failure"    # "none", "on_failure", "always"
    review_policy: str = "after_each"   # "none", "after_each", "after_all"
    max_retries: int = 3
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.genes:
            self.genes = list(DEFAULT_GENOME)

    # --- Gene-level operations ---

    def reorder(self, i: int, j: int) -> "HarnessGenome":
        """Swap genes at positions i and j. Returns new genome."""
        new = self.copy()
        if 0 <= i < len(new.genes) and 0 <= j < len(new.genes):
            new.genes[i], new.genes[j] = new.genes[j], new.genes[i]
        return new

    def duplicate(self, i: int) -> "HarnessGenome":
        """Duplicate the gene at position i. Returns new genome."""
        new = self.copy()
        if 0 <= i < len(new.genes):
            new.genes.insert(i + 1, new.genes[i])
        return new

    def remove(self, i: int) -> "HarnessGenome":
        """Remove the gene at position i. Returns new genome."""
        new = self.copy()
        if 0 <= i < len(new.genes) and len(new.genes) > 1:
            new.genes.pop(i)
        return new

    def merge(self, i: int, j: int) -> "HarnessGenome":
        """Merge genes at i and j into a single gene at i. Returns new genome."""
        new = self.copy()
        if 0 <= i < j < len(new.genes):
            # Merge: keep the first gene and remove the second
            new.genes[i] = new.genes[i]
            new.genes.pop(j)
        return new

    def split(self, i: int) -> "HarnessGenome":
        """Split gene at i into two specialized variants. Returns new genome."""
        new = self.copy()
        if 0 <= i < len(new.genes):
            original = new.genes[i]
            # Split into analyze + original if possible
            if original == Gene.CODE:
                new.genes[i] = Gene.CODE
                new.genes.insert(i + 1, Gene.ANALYZE)
            elif original == Gene.TEST:
                new.genes[i] = Gene.TEST
                new.genes.insert(i + 1, Gene.REPAIR)
            else:
                new.genes.insert(i + 1, original)
        return new

    def conditional(self, i: int, condition_gene: Gene, success_path: list[Gene],
                    failure_path: list[Gene]) -> "HarnessGenome":
        """Add a conditional branch at position i.

        If condition_gene succeeds, follow success_path; otherwise failure_path.
        """
        new = self.copy()
        # Represent conditional as metadata since genes are linear
        key = f"conditional_{i}"
        new.metadata[key] = {
            "position": i,
            "condition": condition_gene.value,
            "success": [g.value for g in success_path],
            "failure": [g.value for g in failure_path],
        }
        return new

    def insert(self, i: int, gene: Gene) -> "HarnessGenome":
        """Insert a new gene at position i."""
        new = self.copy()
        new.genes.insert(i, gene)
        return new

    def copy(self) -> "HarnessGenome":
        """Deep copy this genome."""
        return HarnessGenome(
            genes=list(self.genes),
            context_strategy=self.context_strategy,
            tool_policy=self.tool_policy,
            retry_policy=self.retry_policy,
            review_policy=self.review_policy,
            max_retries=self.max_retries,
            metadata=copy.deepcopy(self.metadata),
        )

    # --- Serialization ---

    def to_dict(self) -> dict:
        return {
            "genes": [g.value for g in self.genes],
            "context_strategy": self.context_strategy,
            "tool_policy": self.tool_policy,
            "retry_policy": self.retry_policy,
            "review_policy": self.review_policy,
            "max_retries": self.max_retries,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "HarnessGenome":
        return cls(
            genes=[Gene(g) for g in d.get("genes", [])],
            context_strategy=d.get("context_strategy", "full"),
            tool_policy=d.get("tool_policy", "all"),
            retry_policy=d.get("retry_policy", "on_failure"),
            review_policy=d.get("review_policy", "after_each"),
            max_retries=d.get("max_retries", 3),
            metadata=d.get("metadata", {}),
        )

    def hash(self) -> str:
        """Stable hash for caching and comparison."""
        canonical = str(sorted(self.to_dict().items()))
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]

    def display(self) -> str:
        """Display the genome as a workflow diagram."""
        gene_names = [g.symbol for g in self.genes]
        arrow = " → "
        return arrow.join(gene_names)

    def __len__(self) -> int:
        return len(self.genes)

    def __getitem__(self, i: int) -> Gene:
        return self.genes[i]

    def __iter__(self):
        return iter(self.genes)

    def __repr__(self) -> str:
        return f"HarnessGenome({self.display()})"
