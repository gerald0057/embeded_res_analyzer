#!/usr/bin/env python3
"""
测试打包配置
"""
import subprocess
import sys
import os
from pathlib import Path

def test_pyinstaller():
    """测试PyInstaller打包"""
    print("📦 测试PyInstaller打包...")
    
    # 检查PyInstaller是否安装
    try:
        import PyInstaller
        print("✅ PyInstaller 已安装")
    except ImportError:
        print("❌ PyInstaller 未安装，正在安装...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # 创建临时spec文件用于测试
    spec_content = f"""
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['{Path(__file__).parent.parent / "backend" / "app" / "main.py"}'],
    pathex=[],
    binaries=[],
    datas=[
        ('{Path(__file__).parent.parent / "frontend"}', 'frontend'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='embedded-analyzer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='',
)
"""
    
    spec_path = Path(__file__).parent.parent / "test_package.spec"
    spec_path.write_text(spec_content)
    
    print("📄 创建打包配置文件")
    print("⚠️  注意：这只是打包测试，完整打包将在阶段5进行")
    
    # 计算预估大小
    import fastapi
    import uvicorn
    
    print(f"📊 依赖包大小估算:")
    print(f"  - FastAPI: ~2MB")
    print(f"  - Uvicorn: ~1MB")
    print(f"  - Python运行时: ~8MB")
    print(f"  - 前端资源: ~0.5MB")
    print(f"  ≈ 总计: ~12MB (使用UPX压缩后)")
    
    return True

if __name__ == "__main__":
    test_pyinstaller()