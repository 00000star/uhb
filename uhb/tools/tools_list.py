"""Known tools and their categories for the tool ecology benchmark."""

from dataclasses import dataclass


@dataclass
class Tool:
    """A tool that an AI coding agent can use."""
    name: str
    category: str           # "search", "analysis", "execution", "version_control", "container"
    description: str
    typical_benefit: str    # what this tool improves
    cli_example: str


TOOL_CATEGORIES = {
    "search": "Tools for finding and navigating code",
    "analysis": "Static analysis and linting tools",
    "execution": "Tools for running code and tests",
    "version_control": "Git and version control tools",
    "container": "Container and environment tools",
    "language_server": "LSP and IDE support tools",
    "formatting": "Code formatting tools",
}


KNOWN_TOOLS = [
    Tool(
        name="ripgrep",
        category="search",
        description="Extremely fast recursive grep. Searches directories for regex patterns.",
        typical_benefit="Reduces search time by 10-100x vs grep. Better defaults for code search.",
        cli_example="rg 'def function_name' --type py",
    ),
    Tool(
        name="tree-sitter",
        category="analysis",
        description="Incremental parsing library. Builds concrete syntax trees for precise code analysis.",
        typical_benefit="Enables precise structural search and refactoring that regex can't do.",
        cli_example="tree-sitter query '*.py' '(function_definition name: (identifier) @name)'",
    ),
    Tool(
        name="ast-grep",
        category="analysis",
        description="Structural code search using AST patterns instead of regex.",
        typical_benefit="Find code patterns by structure, not text — handles whitespace/formatting changes.",
        cli_example="ast-grep --pattern 'try { $$$ } catch($$$) { $$$ }'",
    ),
    Tool(
        name="pytest",
        category="execution",
        description="Python testing framework with rich fixture and plugin system.",
        typical_benefit="Fast test execution with detailed failure reports. Essential for TDD loops.",
        cli_example="pytest tests/ -x --tb=short -q",
    ),
    Tool(
        name="ruff",
        category="analysis",
        description="Extremely fast Python linter and formatter (Rust-based).",
        typical_benefit="Catch style and logic issues 10-100x faster than flake8+pylint combined.",
        cli_example="ruff check . --fix",
    ),
    Tool(
        name="mypy",
        category="analysis",
        description="Static type checker for Python.",
        typical_benefit="Catches type errors before runtime. Essential for large Python codebases.",
        cli_example="mypy src/ --strict",
    ),
    Tool(
        name="git",
        category="version_control",
        description="Distributed version control system.",
        typical_benefit="Track changes, create branches, collaborate. Essential for any coding agent.",
        cli_example="git diff --stat HEAD~1",
    ),
    Tool(
        name="gh",
        category="version_control",
        description="GitHub CLI for managing PRs, issues, and repos from terminal.",
        typical_benefit="Enables PR creation, review, and issue management without leaving terminal.",
        cli_example="gh pr create --title 'Fix auth bug' --body '...'",
    ),
    Tool(
        name="docker",
        category="container",
        description="Container runtime for isolated environments.",
        typical_benefit="Reproducible builds and testing. Isolate side effects.",
        cli_example="docker build -t app . && docker run app pytest",
    ),
    Tool(
        name="coverage",
        category="execution",
        description="Code coverage measurement for Python.",
        typical_benefit="Ensures tests exercise the code. Identifies untested paths.",
        cli_example="coverage run -m pytest && coverage report",
    ),
    Tool(
        name="pre-commit",
        category="analysis",
        description="Framework for managing git hook scripts.",
        typical_benefit="Runs linters/formatters before commit. Prevents bad code from entering repo.",
        cli_example="pre-commit run --all-files",
    ),
    Tool(
        name="jq",
        category="search",
        description="Lightweight command-line JSON processor.",
        typical_benefit="Extract and transform JSON data in shell pipelines.",
        cli_example="cat data.json | jq '.items[] | select(.score > 0.5)'",
    ),
]

# Tool combinations known to have synergy
SYNERGISTIC_PAIRS = [
    ("ripgrep", "ast-grep"),     # Text + structural search
    ("pytest", "coverage"),      # Test + coverage measurement
    ("ruff", "mypy"),            # Fast lint + thorough type check
    ("git", "gh"),               # Local git + GitHub integration
    ("docker", "pytest"),        # Isolated test execution
    ("tree-sitter", "ripgrep"),  # Parse + search
]

# Baseline: what tools a "naked" model gets (no tool access)
BASELINE_TOOLS = []  # No tools

# Minimal: basic tools every coding agent should have
MINIMAL_TOOLS = ["ripgrep", "git"]

# Standard: common development tools
STANDARD_TOOLS = ["ripgrep", "git", "pytest", "ruff", "gh"]
