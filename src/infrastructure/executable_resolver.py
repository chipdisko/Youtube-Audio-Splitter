"""Executable path resolver for bundled and development environments."""
import os
import sys
from pathlib import Path


class ExecutableResolver:
    """Resolves executable paths for bundled and development environments."""

    @staticmethod
    def get_executable_path(executable_name: str) -> str:
        """Get the path to an executable, handling both bundled and development environments."""
        if getattr(sys, 'frozen', False):
            # Application is bundled (py2app)
            app_dir = os.path.dirname(sys.executable)
            executable_path = os.path.join(app_dir, 'Resources', executable_name)
        else:
            # Development environment
            executable_path = executable_name
        return executable_path
