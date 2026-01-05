#!/usr/bin/env python3
"""
简单测试脚本 - 验证核心模块
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_config_models():
    """测试配置模型"""
    print("🔍 测试配置模型...")
    
    try:
        from backend.core.models.config_models import ToolchainConfig, AppConfig
        
        # 创建一个简单的配置（使用/bin/ls作为测试，因为它肯定存在）
        toolchain = ToolchainConfig(
            size_path="/bin/ls",  # 使用系统存在的可执行文件
            readelf_path=None,
            arch="riscv64"
        )
        
        config = AppConfig(toolchain=toolchain)
        
        print(f"✅ 配置模型测试通过")
        print(f"   size_path: {config.toolchain.size_path}")
        print(f"   arch: {config.toolchain.arch}")
        return True
        
    except Exception as e:
        print(f"❌ 配置模型测试失败: {e}")
        return False

def test_statistics_models():
    """测试统计模型"""
    print("\n🔍 测试统计模型...")
    
    try:
        from backend.core.models.statistics_models import (
            ModuleStatistics, SegmentInfo, SegmentType
        )
        
        # 测试段信息
        segment = SegmentInfo(
            name=".text",
            type=SegmentType.TEXT,
            size=4096
        )
        
        # 测试模块统计
        stats = ModuleStatistics(
            file_path="/test/test.o",
            file_name="test.o",
            text_size=1024,
            data_size=256,
            bss_size=512,
            total_size=1792
        )
        
        print(f"✅ 统计模型测试通过")
        print(f"   段名称: {segment.name}, 大小: {segment.formatted_size}")
        print(f"   Flash占用: {stats.flash_usage} bytes")
        print(f"   RAM占用: {stats.ram_usage} bytes")
        return True
        
    except Exception as e:
        print(f"❌ 统计模型测试失败: {e}")
        return False

def test_config_manager():
    """测试配置管理器"""
    print("\n🔍 测试配置管理器...")
    
    try:
        from backend.config.manager import ConfigManager
        
        # 创建临时配置目录用于测试
        import tempfile
        temp_dir = Path(tempfile.mkdtemp())
        config_dir = temp_dir / "test-config"
        
        manager = ConfigManager(config_dir=config_dir)
        config = manager.load_config()
        
        print(f"✅ 配置管理器测试通过")
        print(f"   配置目录: {manager.config_dir}")
        print(f"   默认架构: {config.toolchain.arch}")
        
        # 清理临时目录
        import shutil
        shutil.rmtree(temp_dir)
        return True
        
    except Exception as e:
        print(f"❌ 配置管理器测试失败: {e}")
        return False

def test_file_utils():
    """测试文件工具"""
    print("\n🔍 测试文件工具...")
    
    try:
        from backend.core.utils.file_utils import split_path_components
        
        # 测试路径拆分
        path = "/home/user/projects/test/src"
        components = split_path_components(path)
        
        print(f"✅ 文件工具测试通过")
        print(f"   路径: {path}")
        print(f"   组件: {components}")
        return True
        
    except Exception as e:
        print(f"❌ 文件工具测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 开始核心模块测试\n")
    
    tests = [
        test_config_models,
        test_statistics_models,
        test_config_manager,
        test_file_utils
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append((test_func.__name__, result))
        except Exception as e:
            print(f"⚠️  测试异常: {test_func.__name__}: {e}")
            results.append((test_func.__name__, False))
    
    print("\n" + "="*50)
    print("📊 测试结果汇总:")
    
    passed = 0
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 通过率: {passed}/{len(results)} ({passed/len(results)*100:.0f}%)")
    
    if passed == len(results):
        print("\n✨ 所有测试通过！可以继续下一阶段。")
        return True
    else:
        print("\n⚠️  部分测试失败，请检查错误信息。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)