"""
目录统计模型
"""
from pydantic import BaseModel, Field, ConfigDict, field_serializer
from typing import List
from datetime import datetime
from .statistics_models import ModuleStatistics


class DirectoryStatistics(BaseModel):
    """目录统计信息"""
    path: str = Field(..., description="目录路径")
    modules: List[ModuleStatistics] = Field(default_factory=list, description="模块列表")
    
    # 汇总统计
    total_text: int = Field(0, description="总代码大小")
    total_data: int = Field(0, description="总数据大小")
    total_bss: int = Field(0, description="总bss大小")
    total_size: int = Field(0, description="总大小")
    
    # 元数据
    analyzed_at: datetime = Field(default_factory=datetime.now, description="分析时间")
    file_count: int = Field(0, description="文件数量")
    is_recursive: bool = Field(False, description="是否递归扫描")
    
    @field_serializer('analyzed_at')
    def serialize_analyzed_at(self, analyzed_at: datetime, _info) -> str:
        """序列化analyzed_at字段为ISO格式字符串"""
        return analyzed_at.isoformat()
    
    def update_totals(self):
        """更新汇总统计"""
        self.total_text = sum(m.text_size for m in self.modules)
        self.total_data = sum(m.data_size for m in self.modules)
        self.total_bss = sum(m.bss_size for m in self.modules)
        self.total_size = sum(m.total_size for m in self.modules)
        self.file_count = len(self.modules)
    
    @property
    def total_flash(self) -> int:
        """总Flash占用"""
        return self.total_text + self.total_data
    
    @property
    def total_ram(self) -> int:
        """总RAM占用"""
        return self.total_data + self.total_bss
