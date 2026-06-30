"""Environment abstraction — simulate different development environments."""

import abc
import subprocess
import tempfile
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EnvironmentSpec:
    """Specification for an environment."""
    env_id: str              # "terminal", "vscode", "github", "docker", etc.
    name: str
    description: str
    provides: list[str]      # capabilities: ["shell", "filesystem", "git", "lsp", "browser"]
    constraints: dict = field(default_factory=dict)  # memory limit, disk limit, etc.


@dataclass
class EnvironmentState:
    """Snapshot of environment state for observability."""
    cwd: str = "/workspace"
    files: dict[str, str] = field(default_factory=dict)  # path → content
    env_vars: dict[str, str] = field(default_factory=dict)
    running_processes: list[str] = field(default_factory=list)


class BaseEnvironment(abc.ABC):
    """Abstract base for all environments."""

    spec: EnvironmentSpec

    def __init__(self):
        self.state = EnvironmentState()

    def setup(self, workspace: Optional[Path] = None) -> None:
        """Prepare the environment."""
        if workspace:
            workspace.mkdir(parents=True, exist_ok=True)
            self.state.cwd = str(workspace)

    def teardown(self) -> None:
        """Clean up the environment."""
        pass

    def write_file(self, path: str, content: str) -> None:
        """Write a file into the environment."""
        full_path = Path(self.state.cwd) / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
        self.state.files[path] = content

    def read_file(self, path: str) -> Optional[str]:
        """Read a file from the environment."""
        full_path = Path(self.state.cwd) / path
        if full_path.exists():
            return full_path.read_text()
        return None

    def run_command(self, command: str, timeout: int = 30) -> tuple[int, str, str]:
        """Run a shell command. Returns (exit_code, stdout, stderr)."""
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True,
                timeout=timeout, cwd=self.state.cwd,
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", f"Command timed out after {timeout}s"

    @abc.abstractmethod
    def describe_for_model(self) -> str:
        """Return a description string for the model's system prompt."""
        ...


class TerminalEnvironment(BaseEnvironment):
    """Bare terminal with only shell and filesystem access."""

    spec = EnvironmentSpec(
        env_id="terminal",
        name="Terminal",
        description="Plain Linux terminal with bash, Python, and common CLI tools",
        provides=["shell", "filesystem"],
    )

    def describe_for_model(self) -> str:
        return (
            "You are working in a Linux terminal. You can run shell commands directly. "
            "Files are in the current working directory. "
            "Available: bash, python3, pip, git, curl, grep, find."
        )


class VSCodeEnvironment(BaseEnvironment):
    """Simulated VS Code environment with LSP and editor features."""

    spec = EnvironmentSpec(
        env_id="vscode",
        name="VS Code",
        description="VS Code IDE with Language Server Protocol, diagnostics, and file explorer",
        provides=["shell", "filesystem", "lsp", "editor"],
    )

    def describe_for_model(self) -> str:
        return (
            "You are working in VS Code. You have access to the file explorer, "
            "integrated terminal, language server diagnostics (errors/warnings inline), "
            "and the editor with syntax highlighting. You can run commands in the terminal "
            "and see lint errors in real-time."
        )


class GitHubEnvironment(BaseEnvironment):
    """GitHub repository environment with Issues, PRs, and Actions."""

    spec = EnvironmentSpec(
        env_id="github",
        name="GitHub Repository",
        description="GitHub repository with Issues, Pull Requests, Actions, and wiki",
        provides=["shell", "filesystem", "git", "issues", "prs", "actions"],
    )

    def describe_for_model(self) -> str:
        return (
            "You are working in a GitHub repository. You have access to: "
            "the file tree, Issues, Pull Requests, Actions (CI/CD), and wiki. "
            "You can read/write files, create commits, open PRs, and comment on issues. "
            "Follow standard GitHub Flow: branch → commit → PR → review → merge."
        )


class DockerEnvironment(BaseEnvironment):
    """Containerized environment with Docker isolation."""

    spec = EnvironmentSpec(
        env_id="docker",
        name="Docker Container",
        description="Isolated Docker container with defined resource limits",
        provides=["shell", "filesystem", "container"],
        constraints={"memory_mb": 512, "cpu_shares": 2},
    )

    def describe_for_model(self) -> str:
        return (
            "You are working inside a Docker container. You have shell access "
            "and a filesystem. The container has limited resources (512MB RAM). "
            "All changes are local to this container. You can install packages "
            "but they won't persist between sessions."
        )


class JupyterEnvironment(BaseEnvironment):
    """Jupyter notebook environment."""

    spec = EnvironmentSpec(
        env_id="jupyter",
        name="Jupyter Notebook",
        description="Interactive Jupyter notebook with cells and inline outputs",
        provides=["shell", "filesystem", "notebook", "inline_output"],
    )

    def describe_for_model(self) -> str:
        return (
            "You are working in a Jupyter notebook. You can execute cells "
            "and see inline output including charts, tables, and formatted text. "
            "Variables persist across cells. Use for data exploration, visualization, "
            "and iterative development."
        )


class BrowserEnvironment(BaseEnvironment):
    """Browser-based environment for web development."""

    spec = EnvironmentSpec(
        env_id="browser",
        name="Browser",
        description="Web browser environment with DOM, console, and devtools",
        provides=["shell", "filesystem", "browser", "dom", "devtools"],
    )

    def describe_for_model(self) -> str:
        return (
            "You are working in a web development environment with a live browser. "
            "You can edit HTML/CSS/JS files, start a dev server, and see changes "
            "reflected in the browser. You have access to the browser console, "
            "DOM inspector, and network tab for debugging."
        )


class RemoteServerEnvironment(BaseEnvironment):
    """SSH-accessible remote server environment."""

    spec = EnvironmentSpec(
        env_id="remote_server",
        name="Remote Server",
        description="SSH connection to a remote Linux server",
        provides=["shell", "filesystem", "ssh", "remote"],
    )

    def describe_for_model(self) -> str:
        return (
            "You are connected to a remote Linux server via SSH. You can run "
            "commands on the server, read/write files, and manage services. "
            "The server has systemd, nginx, and common server tools installed. "
            "Be mindful of latency and connection stability."
        )


# Registered environments
ENV_REGISTRY: dict[str, type] = {
    "terminal": TerminalEnvironment,
    "vscode": VSCodeEnvironment,
    "github": GitHubEnvironment,
    "docker": DockerEnvironment,
    "jupyter": JupyterEnvironment,
    "browser": BrowserEnvironment,
    "remote_server": RemoteServerEnvironment,
}


def create_environment(env_id: str) -> BaseEnvironment:
    """Create an environment instance by ID."""
    cls = ENV_REGISTRY.get(env_id)
    if cls is None:
        raise ValueError(f"Unknown environment: {env_id}. Available: {list(ENV_REGISTRY)}")
    return cls()
