"""
测试Pydantic V2兼容性
"""
import pytest
import json
from embedded_analyzer.core.models.config_models import ToolchainConfig
from embedded_analyzer.core.models.statistics_models import ModuleStatistics, SegmentInfo, SegmentType


def test_pydantic_v2_api():
    """测试Pydantic V2 API是否工作正常"""
    # 测试配置模型
    config = ToolchainConfig(
        size_path="",  # 空路径应该被允许
        arch="riscv64"
    )
    
    # 测试model_dump方法
    config_dict = config.model_dump()
    assert "size_path" in config_dict
    assert config_dict["arch"] == "riscv64"
    
    # 测试model_dump_json方法
    config_json = config.model_dump_json()
    parsed_config = json.loads(config_json)
    assert parsed_config["arch"] == "riscv64"
    
    # 测试统计模型
    stats = ModuleStatistics(
        file_path="/test.o",
        file_name="test.o",
        text_size=1024
    )
    
    stats_dict = stats.model_dump()
    assert "text_size" in stats_dict
    assert stats_dict["text_size"] == 1024
    
    # 测试JSON序列化
    stats_json = stats.model_dump_json()
    parsed_stats = json.loads(stats_json)
    assert parsed_stats["file_name"] == "test.o"


def test_field_validator():
    """测试字段验证器"""
    # 空路径应该被允许
    config1 = ToolchainConfig(size_path="")
    assert config1.size_path == ""
    
    # 无效路径应该抛出异常
    with pytest.raises(ValueError, match="size工具不存在"):
        ToolchainConfig(size_path="/nonexistent/path")
    
    # 有效路径应该被接受
    import shutil
    ls_path = shutil.which("ls") or "/bin/ls"
    config2 = ToolchainConfig(size_path=ls_path)
    assert "ls" in config2.size_path