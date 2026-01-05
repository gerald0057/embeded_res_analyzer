"""
配置管理API路由
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from ...config.manager import ConfigManager
from ...core.models.config_models import AppConfig, ToolchainConfig
from ...core.toolchain_manager import ToolchainManager

router = APIRouter(prefix="/config", tags=["配置管理"])

# 初始化管理器
config_manager = ConfigManager()
toolchain_manager = ToolchainManager(config_manager)


# 请求/响应模型
class ToolchainUpdateRequest(BaseModel):
    """工具链更新请求"""
    size_path: str = Field(..., description="size工具路径")
    readelf_path: Optional[str] = Field(None, description="readelf工具路径")
    arch: Optional[str] = Field(None, description="目标架构")


class ConfigUpdateRequest(BaseModel):
    """配置更新请求"""
    toolchain: Optional[ToolchainUpdateRequest] = Field(None, description="工具链配置")
    ui: Optional[Dict[str, Any]] = Field(None, description="UI配置")
    analysis: Optional[Dict[str, Any]] = Field(None, description="分析配置")


class ToolchainTestResponse(BaseModel):
    """工具链测试响应"""
    initialized: bool
    tools: Dict[str, Any]
    overall: str
    error: Optional[str] = None


class AutoDetectResponse(BaseModel):
    """自动检测响应"""
    size: Dict[str, Any]
    readelf: Dict[str, Any]


@router.get("/", response_model=AppConfig)
async def get_configuration():
    """
    获取当前配置
    
    Returns:
        完整的应用配置
    """
    try:
        config = config_manager.load_config()
        return config
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取配置失败: {str(e)}"
        )


@router.put("/", response_model=AppConfig)
async def update_configuration(config_data: ConfigUpdateRequest):
    """
    更新配置
    
    Args:
        config_data: 配置数据
        
    Returns:
        更新后的配置
    """
    try:
        update_dict = {}
        
        if config_data.toolchain:
            update_dict["toolchain"] = config_data.toolchain.dict(exclude_unset=True)
        
        if config_data.ui:
            update_dict["ui"] = config_data.ui
        
        if config_data.analysis:
            update_dict["analysis"] = config_data.analysis
        
        if not update_dict:
            raise HTTPException(
                status_code=400,
                detail="没有提供有效的配置数据"
            )
        
        # 更新配置
        success = config_manager.update_config(**update_dict)
        if not success:
            raise HTTPException(
                status_code=500,
                detail="更新配置失败"
            )
        
        # 如果更新了工具链，重新初始化
        if config_data.toolchain:
            toolchain_manager.initialize(force=True)
        
        # 返回更新后的配置
        config = config_manager.load_config()
        return config
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"更新配置失败: {str(e)}"
        )


@router.put("/toolchain", response_model=AppConfig)
async def update_toolchain_config(toolchain_data: ToolchainUpdateRequest):
    """
    更新工具链配置
    
    Args:
        toolchain_data: 工具链配置数据
        
    Returns:
        更新后的配置
    """
    try:
        # 更新配置
        success = config_manager.update_config(
            toolchain=toolchain_data.dict(exclude_unset=True)
        )
        if not success:
            raise HTTPException(
                status_code=500,
                detail="更新工具链配置失败"
            )
        
        # 重新初始化工具链管理器
        toolchain_manager.initialize(force=True)
        
        # 返回更新后的配置
        config = config_manager.load_config()
        return config
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"更新工具链配置失败: {str(e)}"
        )


@router.post("/toolchain/test", response_model=ToolchainTestResponse)
async def test_toolchain_configuration():
    """
    测试工具链配置
    
    Returns:
        测试结果
    """
    try:
        # 确保工具链已初始化
        toolchain_manager.initialize(force=True)
        
        # 运行测试
        results = toolchain_manager.test_toolchain()
        return results
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"测试工具链失败: {str(e)}"
        )


@router.get("/toolchain/autodetect", response_model=AutoDetectResponse)
async def autodetect_toolchain():
    """
    自动检测系统中的工具链
    
    Returns:
        检测结果
    """
    try:
        from ...core.parsers.parser_factory import ParserFactory
        
        # 尝试查找size工具
        size_path = ParserFactory.find_tool_in_system("size")
        
        # 尝试查找readelf工具
        readelf_path = ParserFactory.find_tool_in_system("readelf")
        
        return {
            "size": {
                "found": size_path is not None,
                "path": size_path,
                "description": "用于分析目标文件大小的工具"
            },
            "readelf": {
                "found": readelf_path is not None,
                "path": readelf_path,
                "description": "用于分析ELF文件详细信息的工具"
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"自动检测失败: {str(e)}"
        )


@router.delete("/cache")
async def clear_config_cache():
    """
    清除配置缓存
    
    强制重新加载配置文件
    """
    try:
        # 清除配置缓存
        config_manager._config = None
        
        # 重新加载配置
        config = config_manager.load_config()
        
        # 重新初始化工具链
        toolchain_manager.initialize(force=True)
        
        return {
            "message": "配置缓存已清除",
            "reloaded": True
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"清除缓存失败: {str(e)}"
        )
