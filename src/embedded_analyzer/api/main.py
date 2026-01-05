"""
FastAPI 主应用入口
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import logging

# 导入路由
from .routers import config, analysis

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="嵌入式资源分析工具",
    description="用于统计嵌入式模块资源占用的分析工具",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含路由 - 统一使用 /api 前缀
app.include_router(config.router, prefix="/api")
app.include_router(analysis.router, prefix="/api")

# 获取前端静态文件路径
BASE_DIR = Path(__file__).parent.parent.parent.parent
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
    try:
        from ..config.manager import ConfigManager
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        return JSONResponse({
            "status": "healthy",
            "service": "embedded-resource-analyzer",
            "version": "1.0.0",
            "config_loaded": True,
            "config_dir": str(config_manager.config_dir)
        })
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return JSONResponse({
            "status": "degraded",
            "error": str(e)
        }, status_code=500)

@app.get("/api")
async def api_info():
    """API信息"""
    return {
        "name": "嵌入式资源分析工具 API",
        "version": "1.0.0",
        "endpoints": [
            {"path": "/api/health", "method": "GET", "description": "健康检查"},
            {"path": "/api/config", "method": "GET", "description": "获取配置"},
            {"path": "/api/config", "method": "PUT", "description": "更新配置"},
            {"path": "/api/config/toolchain", "method": "PUT", "description": "更新工具链"},
            {"path": "/api/config/toolchain/test", "method": "POST", "description": "测试工具链"},
            {"path": "/api/config/toolchain/autodetect", "method": "GET", "description": "自动检测工具链"},
            {"path": "/api/analysis/file", "method": "POST", "description": "分析文件"},
            {"path": "/api/analysis/directory", "method": "POST", "description": "分析目录"},
            {"path": "/api/analysis/status", "method": "GET", "description": "获取分析状态"},
        ],
        "documentation": {
            "swagger": "/api/docs",
            "redoc": "/api/redoc"
        }
    }

# 挂载静态文件
if (FRONTEND_DIR / "static").exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR / "static"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "embedded_analyzer.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )