"""
统计分析数据模型 - 修复序列化递归错误
"""
from pydantic import BaseModel, Field, ConfigDict, field_serializer
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class SegmentType(str, Enum):
    """段类型枚举"""
    TEXT = "text"          # 代码段
    DATA = "data"          # 已初始化数据
    BSS = "bss"           # 未初始化数据
    RODATA = "rodata"     # 只读数据
    COMMENT = "comment"   # 注释
    VECTOR = "vectors"    # 中断向量表
    HEAP = "heap"         # 堆
    STACK = "stack"       # 栈
    OTHER = "other"       # 其他


class SegmentInfo(BaseModel):
    """段详细信息"""
    name: str = Field(..., description="段名称")
    type: SegmentType = Field(..., description="段类型")
    size: int = Field(..., description="段大小（字节）")
    virtual_address: Optional[int] = Field(None, description="虚拟地址")
    offset: Optional[int] = Field(None, description="文件偏移")
    flags: Optional[str] = Field(None, description="段标志（ALLOC, READONLY等）")
    
    @property
    def formatted_size(self) -> str:
        """格式化大小显示"""
        if self.size >= 1024 * 1024:
            return f"{self.size / (1024 * 1024):.2f} MB"
        elif self.size >= 1024:
            return f"{self.size / 1024:.2f} KB"
        else:
            return f"{self.size} B"


class ModuleStatistics(BaseModel):
    """模块统计信息"""
    file_path: str = Field(..., description="文件路径")
    file_name: str = Field(..., description="文件名")
    text_size: int = Field(0, description="代码段大小")
    data_size: int = Field(0, description="已初始化数据大小")
    bss_size: int = Field(0, description="未初始化数据大小")
    total_size: int = Field(0, description="总大小（dec）")
    
    # 详细段信息（可选）
    detailed_segments: List[SegmentInfo] = Field(default_factory=list, description="详细段信息")
    
    # 元数据
    analyzed_at: datetime = Field(default_factory=datetime.now, description="分析时间")
    is_valid: bool = Field(True, description="是否有效")
    error_message: Optional[str] = Field(None, description="错误信息")
    
    model_config = ConfigDict(
        # 移除json_encoders，使用field_serializer
    )
    
    @field_serializer('analyzed_at')
    def serialize_analyzed_at(self, analyzed_at: datetime, _info) -> str:
        """序列化analyzed_at字段为ISO格式字符串"""
        return analyzed_at.isoformat()
    
    @property
    def flash_usage(self) -> int:
        """Flash占用 = text + data"""
        return self.text_size + self.data_size
    
    @property
    def ram_usage(self) -> int:
        """RAM占用 = data + bss"""
        return self.data_size + self.bss_size
    
    def to_summary_dict(self) -> Dict:
        """转换为摘要字典"""
        return {
            "file_name": self.file_name,
            "text": self.text_size,
            "data": self.data_size,
            "bss": self.bss_size,
            "total": self.total_size,
            "flash": self.flash_usage,
            "ram": self.ram_usage
        }