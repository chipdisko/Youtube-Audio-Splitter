"""DRY: Centralized subprocess execution."""
import subprocess
from pathlib import Path
from typing import List, Optional


class SubprocessRunner:
    """Handles subprocess execution with consistent error handling."""

    @staticmethod
    def run(command: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run a command and return the result."""
        return subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=check
        )

    @staticmethod
    def run_streaming(command: List[str]) -> subprocess.Popen:
        """Run a command with streaming output."""
        return subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

    @staticmethod
    def get_output(command: List[str]) -> str:
        """Run a command and return stdout."""
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return result.stdout.strip()
