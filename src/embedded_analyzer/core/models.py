"""
Data models for embedded resource analyzer
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class SectionInfo:
    """Single section entry from objdump -h"""
    index: int
    name: str
    size: int
    vma: str
    lma: str
    file_offset: str
    align: str
    flags_raw: str

    @property
    def size_hex(self) -> str:
        return f"0x{self.size:x}"

    @property
    def size_formatted(self) -> str:
        s = self.size
        if s >= 1024 * 1024:
            return f"{s / (1024 * 1024):.2f} MB"
        elif s >= 1024:
            return f"{s / 1024:.2f} KB"
        return f"{s} B"


@dataclass
class FileSectionResult:
    """Result of analyzing one file for a specific section"""
    file_path: str
    section_name: str
    size: int
    found: bool

    @property
    def size_hex(self) -> str:
        return f"0x{self.size:x}"


@dataclass
class SectionAnalysisResult:
    """Aggregated result of section analysis across multiple files"""
    section_name: str
    files: List[FileSectionResult] = field(default_factory=list)

    @property
    def total(self) -> int:
        return sum(r.size for r in self.files if r.found)

    @property
    def total_hex(self) -> str:
        return f"0x{self.total:x}"

    @property
    def matched_count(self) -> int:
        return sum(1 for r in self.files if r.found)


@dataclass
class SizeResult:
    """Result from size command (text/data/bss breakdown)"""
    file_path: str
    text_size: int
    data_size: int
    bss_size: int
    total_size: int

    @property
    def flash_usage(self) -> int:
        return self.text_size + self.data_size

    @property
    def ram_usage(self) -> int:
        return self.data_size + self.bss_size


@dataclass
class ToolchainConfig:
    """Configuration for a single toolchain"""
    name: str
    objdump: str
    size: Optional[str] = None
    readelf: Optional[str] = None

    def to_dict(self) -> dict:
        d = {"name": self.name, "objdump": self.objdump}
        if self.size:
            d["size"] = self.size
        if self.readelf:
            d["readelf"] = self.readelf
        return d

    @staticmethod
    def from_dict(d: dict) -> "ToolchainConfig":
        return ToolchainConfig(
            name=d["name"],
            objdump=d["objdump"],
            size=d.get("size"),
            readelf=d.get("readelf"),
        )


DEFAULT_SECTIONS = [".text", ".data", ".bss", ".rodata", ".ram_text", ".ram_data", ".flash_text", ".flash_rodata"]


@dataclass
class AppConfig:
    """Application configuration with multiple toolchains"""
    current_toolchain: Optional[str] = None
    toolchains: List[ToolchainConfig] = field(default_factory=list)
    sections: List[str] = field(default_factory=lambda: list(DEFAULT_SECTIONS))

    def get_current(self) -> Optional[ToolchainConfig]:
        if not self.current_toolchain:
            return self.toolchains[0] if self.toolchains else None
        for tc in self.toolchains:
            if tc.name == self.current_toolchain:
                return tc
        return self.toolchains[0] if self.toolchains else None

    def to_dict(self) -> dict:
        return {
            "current_toolchain": self.current_toolchain,
            "toolchains": [tc.to_dict() for tc in self.toolchains],
            "sections": self.sections,
        }

    @staticmethod
    def from_dict(d: dict) -> "AppConfig":
        toolchains = [ToolchainConfig.from_dict(tc) for tc in d.get("toolchains", [])]
        sections = d.get("sections", list(DEFAULT_SECTIONS))
        return AppConfig(
            current_toolchain=d.get("current_toolchain"),
            toolchains=toolchains,
            sections=sections,
        )