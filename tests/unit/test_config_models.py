"""
测试配置模型
"""
import pytest
import tempfile
from pathlib import Path
from embedded_analyzer.core.models.config_models import ToolchainConfig, AppConfig
from embedded_analyzer.core.models.statistics_models import ModuleStatistics, SegmentInfo, SegmentType


class TestToolchainConfig:
    """测试工具链配置"""
    
    def test_valid_config(self):
        """测试有效配置"""
        # 使用/bin/true或/bin/false作为测试，它们在任何Unix系统都存在
        config = ToolchainConfig(
            size_path="/bin/true",
            readelf_path=None,
            arch="riscv64"
        )
        assert config.size_path is not None
        assert config.arch == "riscv64"
    
    def test_invalid_path(self):
        """测试无效路径"""
        with pytest.raises(ValueError, match="size工具不存在"):
            ToolchainConfig(size_path="/nonexistent/path/to/size")


class TestModuleStatistics:
    """测试模块统计"""
    
    def test_basic_statistics(self):
        """基础统计测试"""
        stats = ModuleStatistics(
            file_path="/test/test.o",
            file_name="test.o",
            text_size=1024,
            data_size=256,
            bss_size=512,
            total_size=1792
        )
        
        assert stats.flash_usage == 1280  # 1024 + 256
        assert stats.ram_usage == 768     # 256 + 512
        assert stats.file_name == "test.o"
    
    def test_summary_dict(self):
        """测试摘要字典转换"""
        stats = ModuleStatistics(
            file_path="/test/test.o",
            file_name="test.o",
            text_size=1024,
            data_size=256,
            bss_size=512
        )
        
        summary = stats.to_summary_dict()
        assert summary["file_name"] == "test.o"
        assert summary["text"] == 1024
        assert summary["flash"] == stats.flash_usage
        assert summary["ram"] == stats.ram_usage


class TestSegmentInfo:
    """测试段信息"""
    
    def test_segment_creation(self):
        """测试段创建"""
        segment = SegmentInfo(
            name=".text",
            type=SegmentType.TEXT,
            size=4096
        )
        
        assert segment.name == ".text"
        assert segment.type == SegmentType.TEXT
        assert segment.size == 4096
    
    def test_formatted_size(self):
        """测试格式化大小"""
        segment = SegmentInfo(
            name=".text",
            type=SegmentType.TEXT,
            size=4096  # 4KB
        )
        
        formatted = segment.formatted_size
        assert "KB" in formatted or "4.00" in formatted
