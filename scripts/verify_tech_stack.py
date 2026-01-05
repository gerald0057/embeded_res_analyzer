#!/usr/bin/env python3
"""
验证技术栈决策
"""
import sys
import platform
from pathlib import Path

def verify_environment():
    """验证开发环境"""
    print("🔍 验证技术栈决策...")
    
    # Python版本
    py_version = sys.version_info
    print(f"✅ Python版本: {py_version.major}.{py_version.minor}.{py_version.micro}")
    
    # 平台信息
    print(f"✅ 操作系统: {platform.system()} {platform.release()}")
    
    # 项目结构
    required_dirs = [
        "backend/app",
        "frontend/static",
        "docs",
        ".vscode"
    ]
    
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"✅ 目录存在: {dir_path}")
        else:
            print(f"⚠️  目录缺失: {dir_path}")
    
    # 检查配置文件
    config_dir = Path.home() / ".config" / "embedded-analyzer"
    config_dir.mkdir(parents=True, exist_ok=True)
    print(f"✅ 配置目录: {config_dir}")
    
    return True

if __name__ == "__main__":
    verify_environment()
    print("\n🎯 技术栈验证完成！")
    print("下一步：开始阶段1 - 核心引擎开发")
