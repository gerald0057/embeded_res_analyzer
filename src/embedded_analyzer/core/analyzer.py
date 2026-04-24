"""
Core analyzer - orchestrates objdump/size/readelf for section-level analysis
"""
from __future__ import annotations

import glob
import logging
from pathlib import Path
from typing import Dict, List, Optional

from .models import (
    AppConfig,
    SectionAnalysisResult,
    FileSectionResult,
    SizeResult,
    ToolchainConfig,
)
from .objdump_parser import ObjdumpParser
from .parsers.size_parser import SizeParser
from .parsers.readelf_parser import ReadelfParser

logger = logging.getLogger(__name__)


class Analyzer:
    """Main analyzer that coordinates tool usage."""

    def __init__(self, toolchain: Optional[ToolchainConfig] = None, timeout: int = 30):
        self._toolchain = toolchain
        self._timeout = timeout
        self._objdump: Optional[ObjdumpParser] = None
        self._size: Optional[SizeParser] = None
        self._readelf: Optional[ReadelfParser] = None
        self._initialized = False

    def init_from_config(self, config: Optional[AppConfig] = None) -> "Analyzer":
        """Initialize analyzer from saved config."""
        if config is None:
            from ..config import load_config
            config = load_config()
        tc = config.get_current()
        if tc is None:
            raise ValueError(
                "No toolchain configured. Run 'esa config add' to add one."
            )
        self._toolchain = tc
        self._init_parsers()
        return self

    def init_from_toolchain(self, toolchain: ToolchainConfig) -> "Analyzer":
        """Initialize analyzer with a specific toolchain."""
        self._toolchain = toolchain
        self._init_parsers()
        return self

    def _init_parsers(self):
        if self._toolchain is None:
            raise ValueError("No toolchain set")
        self._objdump = ObjdumpParser(self._toolchain.objdump, self._timeout)
        if self._toolchain.size:
            try:
                self._size = SizeParser(self._toolchain.size, self._timeout)
            except Exception as e:
                logger.warning(f"Size parser init failed: {e}")
                self._size = None
        if self._toolchain.readelf:
            try:
                self._readelf = ReadelfParser(self._toolchain.readelf, self._timeout)
            except Exception as e:
                logger.warning(f"Readelf parser init failed: {e}")
                self._readelf = None
        self._initialized = True

    @property
    def objdump(self) -> ObjdumpParser:
        if not self._initialized:
            self.init_from_config()
        assert self._objdump is not None
        return self._objdump

    @property
    def size(self) -> Optional[SizeParser]:
        if not self._initialized:
            self.init_from_config()
        return self._size

    @property
    def readelf(self) -> Optional[ReadelfParser]:
        if not self._initialized:
            self.init_from_config()
        return self._readelf

    def analyze_section(
        self, files: List[str], section_name: str
    ) -> SectionAnalysisResult:
        """
        Analyze a set of files for a specific section size.
        Equivalent to the shell script's main use case.
        """
        return self.objdump.analyze_files_section(files, section_name)

    def analyze_section_glob(
        self, pattern: str, section_name: str
    ) -> SectionAnalysisResult:
        """Analyze files matching a glob pattern for a section."""
        files = sorted(glob.glob(pattern, recursive=True))
        if not files:
            logger.warning(f"No files matched pattern: {pattern}")
        return self.analyze_section(files, section_name)

    def list_sections(self, file_path: str):
        """List all sections in a file."""
        return self.objdump.get_sections(file_path)

    def analyze_size(self, file_path: str) -> SizeResult:
        """Get text/data/bss size breakdown for a file."""
        if self._size is None:
            raise ValueError("Size tool not configured for current toolchain")
        stats = self._size.parse_single(file_path)
        return SizeResult(
            file_path=file_path,
            text_size=stats.text_size,
            data_size=stats.data_size,
            bss_size=stats.bss_size,
            total_size=stats.total_size,
        )

    def expand_patterns(self, patterns: List[str]) -> List[str]:
        """Expand glob patterns into sorted unique file list."""
        seen = set()
        result = []
        for pattern in patterns:
            for f in sorted(glob.glob(pattern, recursive=True)):
                if f not in seen:
                    seen.add(f)
                    result.append(f)
        return result