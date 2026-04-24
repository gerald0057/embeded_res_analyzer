"""
Base parser for command-line tool invocations
"""
from __future__ import annotations

import os
import subprocess
import logging
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
from abc import ABC, abstractmethod

from ..exceptions import CommandExecutionError

logger = logging.getLogger(__name__)


class BaseParser(ABC):
    """Base parser that executes toolchain commands."""

    def __init__(self, tool_path: str, timeout: int = 30):
        self.tool_path = Path(tool_path).resolve()
        self.timeout = timeout
        self._validate_tool()

    def _validate_tool(self):
        if not self.tool_path.exists():
            raise FileNotFoundError(f"Tool not found: {self.tool_path}")
        if not self.tool_path.is_file():
            raise ValueError(f"Not an executable file: {self.tool_path}")

    def execute_command(self, args: List[str], cwd: Optional[Path] = None) -> Tuple[str, str]:
        cmd = [str(self.tool_path)] + args
        logger.debug(f"Executing: {' '.join(cmd)}")
        env = {**os.environ, "LANG": "C", "LC_ALL": "C"}
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                encoding="utf-8",
                errors="replace",
                env=env,
            )
            if result.returncode != 0:
                raise CommandExecutionError(
                    command=" ".join(cmd),
                    stderr=result.stderr,
                    returncode=result.returncode,
                )
            return result.stdout, result.stderr
        except subprocess.TimeoutExpired as e:
            raise CommandExecutionError(
                command=" ".join(cmd), stderr="Timeout", returncode=-1
            )
        except Exception as e:
            raise CommandExecutionError(
                command=" ".join(cmd), stderr=str(e), returncode=-1
            )

    @abstractmethod
    def parse(self, file_path: str, **kwargs) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_version(self) -> str:
        pass