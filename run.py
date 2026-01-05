#!/usr/bin/env python3
"""
开发环境启动脚本
"""
import sys
from pathlib import Path

# 添加src目录到Python路径
project_root = Path(__file__).parent
src_dir = project_root / "src"
sys.path.insert(0, str(src_dir))

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 启动嵌入式资源分析工具...")
    print(f"📁 项目根目录: {project_root}")
    print(f"📦 包目录: {src_dir}")
    print("🌐 服务将在 http://localhost:8000 启动")
    print("📝 API文档: http://localhost:8000/docs")
    print("🔴 按 Ctrl+C 停止服务\n")
    
    uvicorn.run(
        "embedded_analyzer.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[str(src_dir / "embedded_analyzer")],
        log_level="info"
    )
