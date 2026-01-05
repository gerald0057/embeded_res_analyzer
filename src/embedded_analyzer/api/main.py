"""
FastAPI 主应用入口
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path
import logging

# 导入配置管理 - 使用绝对导入
from embedded_analyzer.config.manager import ConfigManager

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
    version="0.2.0"
)

# 初始化配置管理器
config_manager = ConfigManager()

# 获取前端静态文件路径（现在静态文件在项目根目录的frontend目录）
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
        config = config_manager.load_config()
        return {
            "status": "healthy",
            "service": "embedded-resource-analyzer",
            "version": "0.2.0",
            "config_loaded": True,
            "config_dir": str(config_manager.config_dir)
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return {
            "status": "degraded",
            "error": str(e)
        }

@app.get("/api/config")
async def get_config():
    """获取当前配置"""
    try:
        config = config_manager.load_config()
        return config.dict()
    except Exception as e:
        logger.error(f"获取配置失败: {e}")
        return {"error": str(e)}

# 挂载静态文件
if (FRONTEND_DIR / "static").exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR / "static"), name="static")
