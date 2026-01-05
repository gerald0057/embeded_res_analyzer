"""
集成测试 - 完整工作流程
"""
import tempfile
from pathlib import Path


def test_full_workflow():
    """测试完整工作流程"""
    # 设置临时目录
    with tempfile.TemporaryDirectory() as temp_dir:
        # 1. 创建配置管理器
        from embedded_analyzer.config.manager import ConfigManager
        
        config_dir = Path(temp_dir) / "config"
        config_manager = ConfigManager(config_dir=config_dir)
        
        # 2. 配置工具链
        import shutil
        size_path = shutil.which("size")
        if not size_path:
            print("⚠️  size工具未找到，跳过集成测试")
            return
        
        config_manager.update_config(
            toolchain={
                "size_path": size_path,
                "readelf_path": None,
                "arch": "x86_64"
            }
        )
        
        # 3. 创建工具链管理器
        from embedded_analyzer.core.toolchain_manager import ToolchainManager
        toolchain_manager = ToolchainManager(config_manager)
        
        # 4. 初始化
        assert toolchain_manager.initialize() is True
        
        # 5. 测试工具链
        test_results = toolchain_manager.test_toolchain()
        assert test_results["overall"] in ["passed", "partial"]
        
        print(f"✅ 集成测试通过")
        print(f"   工具链状态: {test_results['overall']}")
        print(f"   size工具: {test_results['tools']['size']['available']}")


if __name__ == "__main__":
    test_full_workflow()
