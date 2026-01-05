"""
测试工具链管理器
"""
import pytest
import tempfile
from pathlib import Path

# 直接导入，不通过core.__init__
from embedded_analyzer.core.toolchain_manager import ToolchainManager


class TestToolchainManager:
    """测试工具链管理器"""
    
    def test_initialization_without_config(self):
        """测试无配置初始化"""
        # 导入ConfigManager
        from embedded_analyzer.config.manager import ConfigManager
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "test-config"
            config_manager = ConfigManager(config_dir=config_dir)
            
            manager = ToolchainManager(config_manager)
            # 初始化应该失败，因为没有配置size路径
            assert manager.initialize() is False
    
    def test_initialization_with_config(self):
        """测试带配置初始化"""
        from embedded_analyzer.config.manager import ConfigManager
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "test-config"
            config_manager = ConfigManager(config_dir=config_dir)
            
            # 创建有效配置
            import shutil
            size_path = shutil.which("size") or "/usr/bin/size"
            
            if not size_path or not Path(size_path).exists():
                pytest.skip("size工具未找到")
            
            config_manager.update_config(
                toolchain={
                    "size_path": size_path,
                    "readelf_path": None,
                    "arch": "test-arch"
                }
            )
            
            manager = ToolchainManager(config_manager)
            # 现在应该能初始化成功
            assert manager.initialize() is True