"""
Size parser - parses size command output for text/data/bss breakdown
"""
from __future__ import annotations

import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from .base_parser import BaseParser
from ..exceptions import ParserError
from ..models import SizeResult

logger = logging.getLogger(__name__)


class SizeParser(BaseParser):
    """Parse size command output."""

    def __init__(self, tool_path: str, timeout: int = 30):
        super().__init__(tool_path, timeout)

    def get_version(self) -> str:
        try:
            stdout, _ = self.execute_command(["--version"])
            match = re.search(r"(\d+\.\d+(\.\d+)?)", stdout)
            return match.group(1) if match else "unknown"
        except Exception:
            return "unknown"

    def parse_single(self, file_path: str) -> SizeResult:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        stdout, _ = self.execute_command(["-t", str(path)])
        return self._parse_output(str(path), stdout)

    def _parse_output(self, file_path: str, output: str) -> SizeResult:
        lines = output.strip().split("\n")
        if len(lines) < 2:
            raise ParserError("SizeParser", "Invalid output format", output)

        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            name = Path(file_path).name
            if name in line or file_path in line:
                return self._parse_data_line(file_path, line)

        return self._parse_data_line(file_path, lines[-1].strip())

    def _parse_data_line(self, file_path: str, line: str) -> SizeResult:
        pattern = r"(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+([0-9a-fA-F]+)\s+(.+)"
        match = re.match(pattern, line.strip())
        if not match:
            parts = line.split()
            if len(parts) >= 6:
                try:
                    return SizeResult(
                        file_path=file_path,
                        text_size=int(parts[0]),
                        data_size=int(parts[1]),
                        bss_size=int(parts[2]),
                        total_size=int(parts[3]),
                    )
                except (ValueError, IndexError):
                    pass
            raise ParserError("SizeParser", f"Cannot parse line: {line}", line)

        return SizeResult(
            file_path=file_path,
            text_size=int(match.group(1)),
            data_size=int(match.group(2)),
            bss_size=int(match.group(3)),
            total_size=int(match.group(4)),
        )

    def parse(self, file_path: str, **kwargs) -> Dict[str, Any]:
        result = self.parse_single(file_path)
        return {
            "file_path": result.file_path,
            "text_size": result.text_size,
            "data_size": result.data_size,
            "bss_size": result.bss_size,
            "total_size": result.total_size,
        }