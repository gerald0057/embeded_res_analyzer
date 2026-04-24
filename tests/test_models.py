"""Tests for core models."""
from embedded_analyzer.core.models import (
    SectionInfo,
    FileSectionResult,
    SectionAnalysisResult,
    SizeResult,
    ToolchainConfig,
    AppConfig,
)


def test_section_info_size_hex():
    s = SectionInfo(index=0, name=".text", size=0x1e4, vma="0000", lma="0000",
                    file_offset="0034", align="2**2", flags_raw="")
    assert s.size == 0x1e4
    assert s.size_hex == "0x1e4"


def test_file_section_result():
    r = FileSectionResult(file_path="foo.o", section_name=".text", size=256, found=True)
    assert r.size_hex == "0x100"
    assert r.found is True


def test_section_analysis_result():
    files = [
        FileSectionResult(file_path="a.o", section_name=".text", size=100, found=True),
        FileSectionResult(file_path="b.o", section_name=".text", size=200, found=True),
        FileSectionResult(file_path="c.o", section_name=".text", size=0, found=False),
    ]
    result = SectionAnalysisResult(section_name=".text", files=files)
    assert result.total == 300
    assert result.total_hex == "0x12c"
    assert result.matched_count == 2


def test_size_result():
    r = SizeResult(file_path="test.o", text_size=100, data_size=50, bss_size=20, total_size=170)
    assert r.flash_usage == 150
    assert r.ram_usage == 70


def test_toolchain_config():
    tc = ToolchainConfig(name="riscv", objdump="/usr/bin/riscv64-unknown-elf-objdump")
    d = tc.to_dict()
    tc2 = ToolchainConfig.from_dict(d)
    assert tc2.name == "riscv"
    assert tc2.objdump == "/usr/bin/riscv64-unknown-elf-objdump"


def test_app_config():
    tc = ToolchainConfig(name="riscv", objdump="/usr/bin/objdump")
    cfg = AppConfig(current_toolchain="riscv", toolchains=[tc])
    d = cfg.to_dict()
    cfg2 = AppConfig.from_dict(d)
    assert cfg2.current_toolchain == "riscv"
    assert len(cfg2.toolchains) == 1

    current = cfg2.get_current()
    assert current is not None
    assert current.name == "riscv"


def test_app_config_default():
    cfg = AppConfig()
    assert cfg.current_toolchain is None
    assert cfg.toolchains == []
    assert cfg.get_current() is None