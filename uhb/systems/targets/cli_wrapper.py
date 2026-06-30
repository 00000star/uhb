import pexpect
import time
import os
import subprocess
from pathlib import Path
from typing import Optional, List

from uhb.systems.base import AICodingSystem, SystemOutput, SystemState

class CLICodingSystem(AICodingSystem):
    """An AI coding system wrapped around a CLI tool (e.g., Aider, Claude Code)."""

    def __init__(self, name: str, command: str, prompt_regex: str, version: str = "unknown"):
        super().__init__(name, version)
        self.command = command
        self.prompt_regex = prompt_regex
        self.process: Optional[pexpect.spawn] = None
        self.repo: Optional[Path] = None

    def setup(self, repo: Path) -> SystemState:
        self.repo = repo
        # Launch the CLI tool
        self.process = pexpect.spawn(self.command, cwd=str(repo), encoding='utf-8', timeout=60)
        self.process.expect(self.prompt_regex)
        
        return self.observe()

    def send_task(self, task: str) -> SystemOutput:
        if not self.process:
            raise RuntimeError("System not set up.")
        
        start = time.monotonic()
        self.process.sendline(task)
        
        # Wait for the prompt to reappear
        try:
            self.process.expect(self.prompt_regex, timeout=300)
            output_text = self.process.before or ""
            success = True
        except pexpect.TIMEOUT:
            output_text = self.process.before or ""
            success = False
        
        duration = time.monotonic() - start
        
        # Detect files changed by checking git status roughly
        files_changed = self._get_modified_files()
        
        return SystemOutput(
            stdout=output_text,
            stderr="",
            exit_code=0 if success else 1,
            files_changed=files_changed,
            duration_seconds=duration,
            tool_calls_made=output_text.count("Tool") + output_text.count("function call"), 
            human_interventions=0,
            success=success
        )

    def observe(self) -> SystemState:
        if not self.repo:
            return SystemState()
            
        modified = self._get_modified_files()
        
        # Check if test suite passing - generic heuristic (e.g., pytest)
        test_passing = True
        if (self.repo / "tests").exists() or (self.repo / "test").exists():
            try:
                res = subprocess.run(["pytest"], cwd=str(self.repo), capture_output=True, text=True)
                test_passing = (res.returncode == 0)
            except Exception:
                pass
                
        return SystemState(
            cwd=str(self.repo),
            files_modified=modified,
            test_suite_passing=test_passing,
            lint_errors=0
        )
        
    def _get_modified_files(self) -> List[str]:
        if not self.repo:
            return []
        try:
            res = subprocess.run(["git", "status", "--porcelain"], cwd=str(self.repo), capture_output=True, text=True)
            if res.returncode == 0:
                return [line[3:] for line in res.stdout.splitlines() if len(line) > 3]
        except Exception:
            pass
        return []

    def teardown(self) -> None:
        if self.process:
            self.process.terminate(force=True)
            self.process = None
