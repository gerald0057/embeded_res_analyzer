"""
工作区数据模型
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
from pathlib import Path


class PinnedModule(BaseModel):
    """置顶模块信息"""
    id: str = Field(..., description="唯一标识")
    path: str = Field(..., description="模块路径")
    display_name: Optional[str] = Field(None, description="显示名称")
    pinned_at: datetime = Field(default_factory=datetime.now, description="置顶时间")
    statistics: Optional[Dict] = Field(None, description="统计信息快照")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Workspace(BaseModel):
    """工作区配置"""
    name: str = Field("default", description="工作区名称")
    pinned_modules: List[PinnedModule] = Field(default_factory=list, description="置顶模块列表")
    recent_paths: List[str] = Field(default_factory=list, description="最近访问路径")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def add_pinned_module(self, path: str, display_name: Optional[str] = None) -> str:
        """添加置顶模块"""
        module_id = f"pinned_{len(self.pinned_modules)}_{Path(path).name}"
        pinned = PinnedModule(
            id=module_id,
            path=path,
            display_name=display_name or Path(path).name
        )
        self.pinned_modules.append(pinned)
        self.updated_at = datetime.now()
        return module_id
    
    def remove_pinned_module(self, module_id: str) -> bool:
        """移除置顶模块"""
        initial_count = len(self.pinned_modules)
        self.pinned_modules = [m for m in self.pinned_modules if m.id != module_id]
        self.updated_at = datetime.now()
        return len(self.pinned_modules) < initial_count
