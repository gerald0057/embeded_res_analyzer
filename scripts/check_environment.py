#!/usr/bin/env python3
"""
检查开发环境
"""
import sys
import pkg_resources

def check_packages():
    """检查依赖包版本"""
    required = {
        "pydantic": "2.5.0",
        "fastapi": "0.104.0",
        "pytest": "7.4.0"
    }
    
    print("📦 检查依赖包版本...")
    for package, expected_version in required.items():
        try:
            version = pkg_resources.get_distribution(package).version
            status = "✅" if version == expected_version else "⚠️ "
            print(f"  {status} {package}: {version} (期望: {expected_version})")
        except pkg_resources.DistributionNotFound:
            print(f"  ❌ {package}: 未安装")

def check_imports():
    """检查导入"""
    print("\n🔍 检查模块导入...")
    
    modules = [
        "embedded_analyzer.core.models.config_models",
        "embedded_analyzer.config.manager",
        "embedded_analyzer.api.main"
    ]
    
    for module_name in modules:
        try:
            __import__(module_name)
            print(f"  ✅ {module_name}")
        except ImportError as e:
            print(f"  ❌ {module_name}: {e}")

def check_paths():
    """检查路径"""
    import os
    from pathlib import Path
    
    print("\n📁 检查项目路径...")
    project_root = Path(__file__).parent.parent
    print(f"  项目根目录: {project_root}")
    
    src_dir = project_root / "src"
    print(f"  src目录: {src_dir} {'✅ 存在' if src_dir.exists() else '❌ 不存在'}")
    
    # 检查Python路径
    print(f"  Python路径包含src: {str(src_dir) in sys.path}")

if __name__ == "__main__":
    print("🧪 开发环境检查\n")
    check_packages()
    check_imports()
    check_paths()
    
    print("\n" + "="*50)
    print("提示: 如果遇到导入问题，尝试运行: pip install -e .")
