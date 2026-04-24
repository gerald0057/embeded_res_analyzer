"""
Readelf parser - parses readelf -S output for detailed section info
"""
from __future__ import annotations

import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from .base_parser import BaseParser
from ..exceptions import ParserError
from ..models import SectionInfo

logger = logging.getLogger(__name__)


class ReadelfParser(BaseParser):
    """Parse readelf -S output."""

    def __init__(self, tool_path: str, timeout: int = 30):
        super().__init__(tool_path, timeout)

    def get_version(self) -> str:
        try:
            stdout, _ = self.execute_command(["--version"])
            match = re.search(r"(\d+\.\d+(\.\d+)?)", stdout)
            return match.group(1) if match else "unknown"
        except Exception:
            return "unknown"

    def get_sections(self, file_path: str) -> List[SectionInfo]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        stdout, _ = self.execute_command(["-S", str(path)])
        return self._parse_sections_output(stdout)

    def _parse_sections_output(self, output: str) -> List[SectionInfo]:
        lines = output.strip().split("\n")
        sections = []
        for line in lines:
            match = re.search(
                r"\[\s*(\d+)\]\s+(\S+)\s+\S+\s+([0-9a-fA-F]+)\s+\S+\s+([0-9a-fA-F]+)",
                line,
            )
            if match:
                try:
                    sections.append(
                        SectionInfo(
                            index=int(match.group(1)),
                            name=match.group(2),
                            size=int(match.group(4), 16),
                            vma=match.group(3),
                            lma="",
                            file_offset="",
                            align="",
                            flags_raw="",
                        )
                    )
                except (ValueError, IndexError):
                    continue
        return sections

    def parse(self, file_path: str, **kwargs) -> Dict[str, Any]:
        sections = self.get_sections(file_path)
        return {
            "sections": [{"name": s.name, "size": s.size} for s in sections],
            "section_count": len(sections),
        }