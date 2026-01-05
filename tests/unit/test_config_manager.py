"""
测试配置管理器
"""
import pytest
import tempfile
import yaml
from pathlib import Path
from embedded_analyzer.config.manager import ConfigManager


class TestConfigManager:
    """测试配置管理器"""
    
    def test_default_config_dir(self):
        """测试默认配置目录"""
        manager = ConfigManager()
        config_dir = manager.config_dir
        
        # 检查目录名称包含embedded-analyzer
        assert "embedded-analyzer" in str(config_dir)
    
    def test_load_default_config(self):
        """测试加载默认配置"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "test-config"
            manager = ConfigManager(config_dir=config_dir)
            
            config = manager.load_config()
            
            assert config is not None
            assert config.version == "1.0.0"
            # 默认配置的size_path应该是空字符串
            assert config.toolchain.size_path == ""
    
    def test_save_and_load_config(self):
        """测试保存和加载配置"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "test-config"
            manager = ConfigManager(config_dir=config_dir)
            
            # 创建配置
            config = manager.get_default_config()
            # 使用系统真实存在的可执行文件
            import shutil
            true_path = shutil.which("true") or "/usr/bin/true"
            config.toolchain.size_path = true_path
            config.toolchain.arch = "test-arch"
            
            # 保存配置
            result = manager.save_config(config)
            assert result is True
            
            # 重新加载配置
            manager2 = ConfigManager(config_dir=config_dir)
            loaded_config = manager2.load_config()
            
            # 检查路径（可能会被解析为绝对路径）
            assert loaded_config.toolchain.size_path.endswith("true")
            assert loaded_config.toolchain.arch == "test-arch"