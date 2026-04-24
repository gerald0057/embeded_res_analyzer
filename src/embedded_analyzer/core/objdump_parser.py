"""
Objdump parser - core analyzer for section-level size queries
"""
from __future__ import annotations

import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .parsers.base_parser import BaseParser
from .models import SectionInfo, FileSectionResult, SectionAnalysisResult
from .exceptions import ParserError

logger = logging.getLogger(__name__)


class ObjdumpParser(BaseParser):
    """
    Parse objdump -h output to get section headers with sizes.
    This is the primary parser matching the shell script's logic.
    """

    def __init__(self, tool_path: str, timeout: int = 30):
        super().__init__(tool_path, timeout)

    def get_version(self) -> str:
        try:
            stdout, _ = self.execute_command(["--version"])
            for line in stdout.strip().split("\n"):
                match = re.search(r"(\d+\.\d+(\.\d+)?)", line)
                if match:
                    return match.group(1)
            return "unknown"
        except Exception:
            return "unknown"

    def get_sections(self, file_path: str) -> List[SectionInfo]:
        """
        Get all sections from a single .o file using objdump -h.

        Returns a list of SectionInfo objects.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        stdout, _ = self.execute_command(["-h", str(path)])
        return self._parse_sections_output(stdout)

    def get_section_size(self, file_path: str, section_name: str) -> Optional[int]:
        """
        Get the size of a specific section in a file.
        Exact match on section name (same logic as the shell script).
        """
        sections = self.get_sections(file_path)
        for sec in sections:
            if sec.name == section_name:
                return sec.size
        return None

    def analyze_files_section(
        self, files: List[str], section_name: str
    ) -> SectionAnalysisResult:
        """
        Analyze multiple files for a specific section size.
        This is the equivalent of the shell script's main loop.
        """
        result = SectionAnalysisResult(section_name=section_name)

        for f in files:
            try:
                size = self.get_section_size(f, section_name)
                if size is not None:
                    result.files.append(
                        FileSectionResult(
                            file_path=f,
                            section_name=section_name,
                            size=size,
                            found=True,
                        )
                    )
                else:
                    result.files.append(
                        FileSectionResult(
                            file_path=f,
                            section_name=section_name,
                            size=0,
                            found=False,
                        )
                    )
            except Exception as e:
                logger.warning(f"Failed to analyze {f}: {e}")
                result.files.append(
                    FileSectionResult(
                        file_path=f,
                        section_name=section_name,
                        size=0,
                        found=False,
                    )
                )

        return result

    def _parse_sections_output(self, output: str) -> List[SectionInfo]:
        """
        Parse objdump -h output.

        Example output:
            file format elf64-littleriscv

            Sections:
            Idx Name          Size      VMA               LMA               File off  Algn
              0 .text         000001e4  0000000000000000  0000000000000000  00000034  2**2
                              CONTENTS, ALLOC, LOAD, READONLY, CODE
              1 .data         00000000  0000000000000000  0000000000000000  00000218  2**0
                              CONTENTS, ALLOC, LOAD, DATA
        """
        lines = output.strip().split("\n")
        sections = []

        in_sections = False
        i = 0
        while i < len(lines):
            line = lines[i].strip()

            if "Idx Name" in line or re.search(r"^\s*\d+\s+\S", line):
                in_sections = True

            if in_sections:
                section = self._try_parse_section_line(line)
                if section:
                    sections.append(section)

            i += 1

        return sections

    def _try_parse_section_line(self, line: str) -> Optional[SectionInfo]:
        """
        Try to parse a section line from objdump -h output.
        Format:  Idx Name          Size      VMA               LMA               File off  Algn
                 0 .text         000001e4  0000000000000000  0000000000000000  00000034  2**2
        """
        pattern = r"^\s*(\d+)\s+(\S+)\s+([0-9a-fA-F]+)\s+([0-9a-fA-F]+)\s+([0-9a-fA-F]+)\s+([0-9a-fA-F]+)\s+(\S+)"
        match = re.match(pattern, line)
        if not match:
            return None

        try:
            idx = int(match.group(1))
            name = match.group(2)
            size = int(match.group(3), 16)
            vma = match.group(4)
            lma = match.group(5)
            file_off = match.group(6)
            align = match.group(7)

            return SectionInfo(
                index=idx,
                name=name,
                size=size,
                vma=vma,
                lma=lma,
                file_offset=file_off,
                align=align,
                flags_raw="",
            )
        except (ValueError, IndexError) as e:
            logger.warning(f"Failed to parse section line: {line}, error: {e}")
            return None

    def parse(self, file_path: str, **kwargs) -> Dict:
        sections = self.get_sections(file_path)
        return {
            "sections": [
                {
                    "name": s.name,
                    "size": s.size,
                    "size_hex": s.size_hex if hasattr(s, "size_hex") else f"0x{s.size:x}",
                    "vma": s.vma,
                    "lma": s.lma,
                }
                for s in sections
            ],
            "section_count": len(sections),
        }