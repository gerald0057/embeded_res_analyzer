#!/usr/bin/env python3
"""
开发环境启动脚本
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 启动嵌入式资源分析工具...")
    print(f"📁 项目根目录: {project_root}")
    print("🌐 服务将在 http://localhost:8000 启动")
    print("📝 API文档: http://localhost:8000/docs")
    print("🔴 按 Ctrl+C 停止服务\n")
    
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[str(project_root / "backend"), str(project_root / "frontend")],
        log_level="info"
    )