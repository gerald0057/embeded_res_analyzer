"""
配置相关数据模型 - 更新为Pydantic V2
"""
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any, ClassVar
from pathlib import Path
import os


class ToolchainConfig(BaseModel):
    """工具链配置"""
    size_path: str = Field("", description="size工具完整路径")
    readelf_path: Optional[str] = Field(None, description="readelf工具路径（可选）")
    arch: Optional[str] = Field(None, description="目标架构，如riscv64、arm-none-eabi等")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "size_path": "/opt/Xuantie-900-gcc-elf-newlib-x86_64-V2.10.2/bin/riscv64-unknown-elf-size",
                "readelf_path": "/opt/Xuantie-900-gcc-elf-newlib-x86_64-V2.10.2/bin/riscv64-unknown-elf-readelf",
                "arch": "riscv64"
            }
        }
    )
    
    @field_validator('size_path')
    @classmethod
    def validate_size_path(cls, v: str) -> str:
        """验证size工具路径"""
        if not v:  # 允许空路径（未配置）
            return v
            
        path = Path(v)
        if not path.exists():
            raise ValueError(f"size工具不存在: {v}")
        if not os.access(path, os.X_OK):
            raise ValueError(f"size工具不可执行: {v}")
        return str(path.resolve())
    
    @field_validator('readelf_path')
    @classmethod
    def validate_readelf_path(cls, v: Optional[str]) -> Optional[str]:
        """验证readelf工具路径"""
        if v is None or v == "":
            return None
            
        path = Path(v)
        if not path.exists():
            raise ValueError(f"readelf工具不存在: {v}")
        if not os.access(path, os.X_OK):
            raise ValueError(f"readelf工具不可执行: {v}")
        return str(path.resolve())


class UIConfig(BaseModel):
    """UI相关配置"""
    theme: str = Field("light", description="界面主题")
    recent_paths: List[str] = Field(default_factory=list, description="最近访问路径")
    default_pattern: str = Field("*.o", description="默认文件匹配模式")


class AnalysisConfig(BaseModel):
    """分析相关配置"""
    cache_enabled: bool = Field(True, description="启用缓存")
    cache_ttl: int = Field(3600, description="缓存生存时间（秒）")
    recursive_depth: int = Field(5, description="递归扫描深度")


class AppConfig(BaseModel):
    """应用完整配置"""
    toolchain: ToolchainConfig
    ui: UIConfig = Field(default_factory=UIConfig)
    analysis: AnalysisConfig = Field(default_factory=AnalysisConfig)
    version: str = Field("1.0.0", description="配置版本")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "toolchain": {
                    "size_path": "/opt/Xuantie-900-gcc-elf-newlib-x86_64-V2.10.2/bin/riscv64-unknown-elf-size",
                    "readelf_path": "/opt/Xuantie-900-gcc-elf-newlib-x86_64-V2.10.2/bin/riscv64-unknown-elf-readelf",
                    "arch": "riscv64"
                },
                "ui": {
                    "theme": "light",
                    "recent_paths": ["/path/to/project1", "/path/to/project2"],
                    "default_pattern": "*.o"
                },
                "analysis": {
                    "cache_enabled": True,
                    "cache_ttl": 3600,
                    "recursive_depth": 5
                },
                "version": "1.0.0"
            }
        }
    )