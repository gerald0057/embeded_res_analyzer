"""
Pytest配置和共享fixture
"""
import sys
import os
from pathlib import Path

# 添加src目录到Python路径
project_root = Path(__file__).parent.parent
src_dir = project_root / "src"
sys.path.insert(0, str(src_dir))


# 创建测试用的配置管理器fixture
import pytest
import tempfile
from embedded_analyzer.config.manager import ConfigManager


@pytest.fixture
def temp_config_manager():
    """创建临时配置管理器"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_dir = Path(temp_dir) / "test-config"
        manager = ConfigManager(config_dir=config_dir)
        yield manager


@pytest.fixture
def configured_manager(temp_config_manager):
    """创建已配置的工具链管理器"""
    import shutil
    from embedded_analyzer.core.toolchain_manager import ToolchainManager
    
    size_path = shutil.which("size") or "/usr/bin/size"
    if not size_path:
        pytest.skip("size工具未找到")
    
    # 配置size路径
    temp_config_manager.update_config(
        toolchain={
            "size_path": size_path,
            "readelf_path": None,
            "arch": "test-arch"
        }
    )
    
    manager = ToolchainManager(temp_config_manager)
    manager.initialize()
    return manager
