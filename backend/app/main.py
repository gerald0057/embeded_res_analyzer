"""
FastAPI 主应用入口
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import os
from pathlib import Path

# 创建FastAPI应用
app = FastAPI(
    title="嵌入式资源分析工具",
    description="用于统计嵌入式模块资源占用的分析工具",
    version="0.1.0"
)

# 获取前端静态文件路径
BASE_DIR = Path(__file__).parent.parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

@app.get("/")
async def root():
    """根路径，返回前端页面"""
    index_path = FRONTEND_DIR / "static" / "index.html"
    if index_path.exists():
        with open(index_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    return {"message": "前端页面未找到，请确保 frontend/static/index.html 存在"}

@app.get("/api/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": "embedded-resource-analyzer",
        "version": "0.1.0"
    }

@app.get("/api/test")
async def test_endpoint():
    """测试API端点"""
    return {
        "message": "后端API工作正常",
        "data": {"text": 1024, "data": 256, "bss": 512}
    }

# 挂载静态文件
if (FRONTEND_DIR / "static").exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR / "static"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
