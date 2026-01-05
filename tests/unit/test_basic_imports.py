"""
测试基本导入功能
"""


def test_core_imports():
    """测试核心模块导入"""
    # 测试可以直接导入的模块
    from embedded_analyzer.core import models
    from embedded_analyzer.core import parsers
    from embedded_analyzer.core import utils
    from embedded_analyzer.core.exceptions import ToolchainError
    
    assert models is not None
    assert parsers is not None
    assert utils is not None
    assert issubclass(ToolchainError, Exception)


def test_config_import():
    """测试配置模块导入"""
    from embedded_analyzer.config.manager import ConfigManager
    
    # 创建临时配置管理器
    import tempfile
    from pathlib import Path
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_dir = Path(temp_dir) / "test-config"
        manager = ConfigManager(config_dir=config_dir)
        config = manager.load_config()
        
        assert config is not None
        assert config.version == "1.0.0"


def test_toolchain_manager_import():
    """测试工具链管理器导入"""
    from embedded_analyzer.core.toolchain_manager import ToolchainManager
    
    # 可以导入，但需要配置才能使用
    manager = ToolchainManager()
    assert manager is not None
