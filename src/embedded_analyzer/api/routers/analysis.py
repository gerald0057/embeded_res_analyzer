"""
分析功能API路由
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from pathlib import Path

from ...core.toolchain_manager import ToolchainManager
from ...config.manager import ConfigManager

router = APIRouter(prefix="/analysis", tags=["分析功能"])

# 初始化管理器
config_manager = ConfigManager()
toolchain_manager = ToolchainManager(config_manager)


# 请求/响应模型
class AnalyzeFileRequest(BaseModel):
    """分析文件请求"""
    file_path: str = Field(..., description="文件路径")
    detailed: bool = Field(False, description="是否获取详细信息")


class AnalyzeDirectoryRequest(BaseModel):
    """分析目录请求"""
    directory: str = Field(..., description="目录路径")
    pattern: str = Field("*.o", description="文件匹配模式")
    recursive: bool = Field(False, description="是否递归查找")
    detailed: bool = Field(False, description="是否获取详细信息")


@router.post("/file")
async def analyze_file(request: AnalyzeFileRequest):
    """
    分析单个文件
    
    Args:
        request: 分析请求
        
    Returns:
        分析结果
    """
    try:
        # 验证文件是否存在
        file_path = Path(request.file_path)
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"文件不存在: {request.file_path}"
            )
        
        # 确保工具链已初始化
        if not toolchain_manager.initialize():
            raise HTTPException(
                status_code=500,
                detail="工具链未配置或初始化失败"
            )
        
        # 分析文件
        result = toolchain_manager.analyze_file(
            file_path=str(file_path),
            detailed=request.detailed
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"分析文件失败: {str(e)}"
        )


@router.post("/directory")
async def analyze_directory(request: AnalyzeDirectoryRequest):
    """
    分析目录
    
    Args:
        request: 分析请求
        
    Returns:
        分析结果
    """
    try:
        # 验证目录是否存在
        directory = Path(request.directory)
        if not directory.exists():
            raise HTTPException(
                status_code=404,
                detail=f"目录不存在: {request.directory}"
            )
        if not directory.is_dir():
            raise HTTPException(
                status_code=400,
                detail=f"不是有效的目录: {request.directory}"
            )
        
        # 确保工具链已初始化
        if not toolchain_manager.initialize():
            raise HTTPException(
                status_code=500,
                detail="工具链未配置或初始化失败"
            )
        
        # 分析目录
        result = toolchain_manager.analyze_directory(
            directory=str(directory),
            pattern=request.pattern,
            recursive=request.recursive
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"分析目录失败: {str(e)}"
        )


@router.get("/status")
async def get_analysis_status():
    """
    获取分析状态
    
    Returns:
        工具链状态信息
    """
    try:
        initialized = toolchain_manager._initialized
        
        if initialized:
            size_parser = toolchain_manager.get_size_parser()
            readelf_parser = toolchain_manager.get_readelf_parser()
            
            return {
                "initialized": True,
                "size_available": True,
                "size_version": size_parser.get_version(),
                "readelf_available": readelf_parser is not None,
                "readelf_version": readelf_parser.get_version() if readelf_parser else None
            }
        else:
            return {
                "initialized": False,
                "size_available": False,
                "readelf_available": False,
                "message": "工具链未初始化，请先配置工具链路径"
            }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取状态失败: {str(e)}"
        )
